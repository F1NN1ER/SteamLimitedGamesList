import os

import requests

from fetch_all_type import DB_DIR, init_db

BASE_URL = "https://github.com/F1NN1ER/SteamAppListWithType/releases/download/db/data.db"


def _download_base_db(dest):
    r = requests.get(BASE_URL, stream=True, timeout=30)
    r.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in r.iter_content(8192):
            if chunk:
                f.write(chunk)


def merge_new_data():
    conn = init_db()
    base_path = os.path.join(DB_DIR, "base.db")
    try:
        _download_base_db(base_path)
    except requests.RequestException as e:
        print(f"下载基础数据库失败，跳过合并: {e}")
        conn.close()
        return 0

    try:
        conn.execute("ATTACH ? AS base", (base_path,))
        before = conn.execute("SELECT COUNT(*) FROM main.Info").fetchone()[0]
        conn.execute(
            "INSERT OR IGNORE INTO Info(appid, name, type, limited_status) "
            "SELECT appid, name, type, NULL FROM base.Info"
        )
        conn.commit()
        after = conn.execute("SELECT COUNT(*) FROM main.Info").fetchone()[0]
        conn.execute("DETACH base")
        added = after - before
        print(f"新增 {added} 条（{before} -> {after}）")
        return added
    finally:
        conn.close()
        if os.path.exists(base_path):
            os.remove(base_path)


if __name__ == "__main__":
    merge_new_data()
