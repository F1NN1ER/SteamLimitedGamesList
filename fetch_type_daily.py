from concurrent.futures import ThreadPoolExecutor

from fetch_all_type import (
    MAX_WORKERS,
    BATCH_SIZE,
    MAX_ITEMS,
    init_db,
    get_app_limited_status,
    update_status_batch,
)


# 受限情况为空 / Learning / Error 的数据
def get_todo(connection):
    cur = connection.cursor()
    cur.execute(
        "SELECT appid FROM Info "
        "WHERE limited_status IS NULL "
        "OR limited_status IN ('Learning', 'Error')"
    )
    return [row[0] for row in cur.fetchall()]


if __name__ == '__main__':
    print("开始增量获取产品受限情况")
    conn = init_db()
    todo_all = get_todo(conn)
    todo = todo_all[:MAX_ITEMS]
    total = len(todo)
    print(f"待处理: {total}/{len(todo_all)}")

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
