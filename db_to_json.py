import json
import os

from fetch_all_type import DB_DIR, init_db


def export():
    conn = init_db()
    cur = conn.cursor()

    # All.json
    rows = cur.execute(
        "SELECT appid, limited_status FROM Info "
        "WHERE limited_status IS NOT NULL ORDER BY appid"
    ).fetchall()
    all_data = [{"appid": appid, "limited_status": status} for appid, status in rows]
    with open(os.path.join(DB_DIR, "All.json"), "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, separators=(",", ":"))

    # type.json
    types = cur.execute(
        "SELECT DISTINCT limited_status FROM Info "
        "WHERE limited_status IS NOT NULL ORDER BY limited_status"
    ).fetchall()
    for (status,) in types:
        appids = [
            r[0] for r in cur.execute(
                "SELECT appid FROM Info WHERE limited_status = ? ORDER BY appid",
                (status,),
            ).fetchall()
        ]
        with open(os.path.join(DB_DIR, f"{status}.json"), "w", encoding="utf-8") as f:
            json.dump(appids, f, separators=(",", ":"))
        print(f"{status}.json: {len(appids)}")

    conn.close()
    print(f"All.json: {len(all_data)}")
    return len(all_data)


if __name__ == "__main__":
    print("开始导出数据库为 JSON")
    export()
    print("完成")
