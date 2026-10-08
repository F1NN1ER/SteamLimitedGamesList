import os

import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "Data")
DB_PATH = os.path.join(DB_DIR, "data.db")

URL = "https://github.com/F1NN1ER/SteamAppListWithType/releases/download/db/data.db"

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0",
})


def fetch_database() -> bool:
    os.makedirs(DB_DIR, exist_ok=True)
    try:
        with SESSION.get(URL, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(DB_PATH, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return True
    except requests.RequestException as e:
        print(f"下载失败: {e}")
        return False


if __name__ == "__main__":
    success = fetch_database()
    print(f"{'成功' if success else '失败'}: {DB_PATH}")
