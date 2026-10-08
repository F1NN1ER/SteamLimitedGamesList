import os
import sys

from fetch_all_type import init_db


def merge_new_data(base_path):
    if not os.path.exists(base_path):
        print(f"基础数据库不存在，跳过合并: {base_path}")
        return 0
    conn = init_db()
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


if __name__ == "__main__":
    base_path = sys.argv[1] if len(sys.argv) > 1 else "Data/base.db"
    merge_new_data(base_path)
