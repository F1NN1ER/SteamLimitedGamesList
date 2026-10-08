import os
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MAX_RETRY = 3
MAX_WORKERS = 24
BATCH_SIZE = 500
RESUME = True

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "Data")
DB_PATH = os.path.join(DB_DIR, "data.db")

BASE_URL = "https://store.steampowered.com/app/{}/"

_thread_local = threading.local()


def _get_session():
    if not hasattr(_thread_local, "session"):
        s = requests.Session()
        s.headers.update({
            "User-Agent": "Mozilla/5.0",
            "Cookie": "birthtime=283993201; mature_content=1; wants_mature_content=1",
            "Accept-Encoding": "gzip, deflate",
        })
        _thread_local.session = s
    return _thread_local.session


# 初始化数据库
def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    # 确保受限情况列存在（兼容基础数据库）
    cols = [r[1] for r in connection.execute("PRAGMA table_info(Info)")]
    if "limited_status" not in cols:
        connection.execute("ALTER TABLE Info ADD COLUMN limited_status text")
        connection.commit()
    return connection


# 获取待处理项
def get_todo(connection, resume=True):
    cur = connection.cursor()
    if resume:
        cur.execute("SELECT appid FROM Info WHERE limited_status IS NULL")
    else:
        cur.execute("SELECT appid FROM Info")
    return [row[0] for row in cur.fetchall()]


# 获取产品受限情况
def get_app_limited_status(appid: int):
    url = BASE_URL.format(appid)
    session = _get_session()

    for attempt in range(MAX_RETRY):
        try:
            r = session.get(
                url,
                timeout=(6, 15),
                allow_redirects=True,
                verify=False,
                stream=True,
            )
            # 加载错误
            if r.status_code != 200:
                r.close()
                raise requests.RequestException(f"status {r.status_code}")
            # 跳转至商店首页，标记为下架
            if urlparse(str(r.url)).path in ("/", ""):
                r.close()
                return "Banned"
            data = r.content
            r.close()
            # 了解中
            if b"ico_learning_about_game" in data:
                return "Learning"
            # 受限
            if b"learning_about" in data:
                return "Limited"
            # 正常
            return "Normal"

        except requests.RequestException:
            if attempt < MAX_RETRY - 1:
                time.sleep(min(2 ** attempt, 10))

    return "Error"


# 批量写入数据库
def update_status_batch(connection, items):
    connection.executemany(
        "UPDATE Info SET limited_status = ? WHERE appid = ?",
        [(status, appid) for appid, status in items],
    )
    connection.commit()


if __name__ == '__main__':
    print("开始全量获取产品受限情况")
    conn = init_db()
    todo = get_todo(conn, resume=RESUME)
    total = len(todo)
    print(f"待处理: {total}")

    if total == 0:
        print("无待处理项")
    else:
        done = 0
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            for start in range(0, total, BATCH_SIZE):
                chunk = todo[start:start + BATCH_SIZE]
                results = executor.map(get_app_limited_status, chunk)
                batch = [(appid, status) for appid, status in zip(chunk, results)]
                update_status_batch(conn, batch)
                done += len(batch)
                print(f"进度: {done}/{total}")

    conn.close()
    print("完成")
