import argparse
import subprocess
import sys
import threading
import queue
import requests
import time
from pathlib import Path

# ──────────────── 基本設定 ────────────────
NUM_WORKERS       = 6
task_queue        = queue.Queue()
result_queue      = queue.Queue()
start_time        = time.perf_counter()
sequence_counter  = 0
log_lock          = threading.Lock()

# ──────────────── ログユーティリティ ────────────────
def write_log(category: str, message: str, task_id: int | None,
              log_file: Path, html_file: Path) -> None:
    global sequence_counter
    with log_lock:
        sequence_counter += 1
        elapsed = time.perf_counter() - start_time
        tid     = f"{task_id:>2}" if task_id is not None else "--"
        line    = f"{sequence_counter:04d}|{elapsed:7.3f}s|{tid}|{message}"

        # テキストログを append モードで書き込む
        with log_file.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

        # HTMLログを append モードで書き込む
        css = (
            "thread-error" if category.startswith("one-error")
            else f"thread-{task_id}" if task_id is not None
            else "thread-none"
        )
        html_line = f'<span class="{css}">{line}</span>\n'
        with html_file.open("a", encoding="utf-8") as f:
            f.write(html_line)


def init_logs(log_file: Path, html_file: Path) -> None:
    """ログファイルと HTML ファイルを初期化する。"""
    # ディレクトリ作成
    log_file.parent.mkdir(parents=True, exist_ok=True)
    html_file.parent.mkdir(parents=True, exist_ok=True)
    # テキストログ初期化
    log_file.write_text("", encoding="utf-8")
    # HTMLログ初期化
    html_file.write_text(
        """<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8">
<style>
 body{background:#dbdbdb;font-family:monospace;font-size:16px}
 pre{white-space:pre-wrap}
 .thread-1{color:#e74c3c}.thread-2{color:#27ae60}.thread-3{color:#e69138}
 .thread-4{color:#3498db}.thread-5{color:#9b59b6}.thread-6{color:#1abc9c}
 .thread-error{color:#7f8c8d}.thread-none{color:#000}
</style></head><body><pre>
""",
        encoding="utf-8"
    )

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "server",
        choices=["all", "flask", "flask_gunicorn", "fastapi"],
        help="使用サーバ: all / flask / flask_gunicorn / fastapi"
    )
    parser.add_argument(
        "path",
        choices=["all", "db", "json"],
        help="アクセスパス: all / db / json"
    )
    parser.add_argument(
        "--delay",
        action="store_true",
        help="/delay/<id> エンドポイントを呼ぶ"
    )
    return parser.parse_args()

# ──────────────── メイン ────────────────
def main() -> None:
    args = parse_args()

    # ---- all は未実装 ----
    if args.server == "all" or args.path == "all":
        print("Not error. Only not implemented.")
        sys.exit(1)

    # ---- サーバー起動設定 ----
    port_map      = {"flask":5555, "flask_gunicorn":6666, "fastapi":7777}
    port          = port_map[args.server]
    endpoint_base = f"http://127.0.0.1:{port}/{args.path}"
    if args.delay:
        endpoint_base += "/delay"

    # ---- ログファイル準備 ----
    log_dir    = Path(__file__).parent.parent / "log"
    delay_tag  = "delay" if args.delay else "not_delay"
    log_file   = log_dir / f"threads_{args.server}_{args.path}_{delay_tag}.log"
    html_file  = log_file.with_suffix(".html")
    init_logs(log_file, html_file)

    # ---- サーバー起動 ----
    server_script = Path(__file__).parent.parent / "server" / f"{args.server}_server.py"
    write_log("all-start", f"サーバー起動準備: {server_script}", None, log_file, html_file)
    server_proc = subprocess.Popen([sys.executable, str(server_script)])
    write_log("one-todo", "サーバー起動コマンド送信", None, log_file, html_file)
    time.sleep(1)
    write_log("one-done", f"サーバー起動完了: port={port}", None, log_file, html_file)

    # ---- ネスト関数：HTTP タスク（細粒度ログ） ----
    def fetch_species(task_id: int) -> None:
        url = f"{endpoint_base}/{task_id}"
        write_log("one-todo", f"準備: HTTP GET {url}", task_id, log_file, html_file)

        t0 = time.perf_counter()
        write_log("one-todo", "HTTP送信開始", task_id, log_file, html_file)
        try:
            resp = requests.get(url, timeout=20)
            t1 = time.perf_counter()
            write_log("one-todo",
                      f"受信完了: status={resp.status_code}, elapsed={(t1-t0):.3f}s",
                      task_id, log_file, html_file)

            write_log("one-todo", "ステータス検証開始", task_id, log_file, html_file)
            resp.raise_for_status()
            write_log("one-todo", "ステータスOK", task_id, log_file, html_file)

            write_log("one-todo", "JSON解析開始", task_id, log_file, html_file)
            data = resp.json()
            write_log("one-todo", f"JSON解析成功: keys={list(data.keys())}",
                      task_id, log_file, html_file)

            if "ja" in data:
                name = data["ja"]
                write_log("one-todo", f"ja取得: {name}", task_id, log_file, html_file)
            else:
                name = "(jaなし)"
                write_log("one-todo", "jaフィールドなし", task_id, log_file, html_file)

            write_log("one-todo", "結果キュー登録開始", task_id, log_file, html_file)
            result_queue.put((task_id, name))
            write_log("one-todo", "結果キュー登録完了", task_id, log_file, html_file)

            write_log("one-done", f"タスク完了: name={name}", task_id, log_file, html_file)
        except Exception as exc:
            write_log("one-error",
                      f"例外発生: {type(exc).__name__}: {exc}",
                      task_id, log_file, html_file)

    # ---- ネスト関数：ワーカー ----
    def worker() -> None:
        wid = int(threading.current_thread().name.split("-",1)[1])
        write_log("one-start", f"ワーカー起動: WID={wid}", wid, log_file, html_file)
        while True:
            write_log("one-todo", "タスク取得待機", wid, log_file, html_file)
            task_id = task_queue.get()
            write_log("one-todo", f"タスク取得: task_id={task_id}", wid, log_file, html_file)
            if task_id is None:
                write_log("one-finish", "シャットダウンシグナル受信", wid, log_file, html_file)
                task_queue.task_done()
                break

            write_log("one-todo", f"実行開始: task_id={task_id}", wid, log_file, html_file)
            fetch_species(task_id)
            write_log("one-finish", f"実行完了: task_id={task_id}", wid, log_file, html_file)
            task_queue.task_done()

        write_log("one-finish", "ワーカー終了", wid, log_file, html_file)

    # ---- ワーカー起動 ----
    write_log("all-start", f"ワーカー起動準備: NUM_WORKERS={NUM_WORKERS}", None, log_file, html_file)
    threads = [threading.Thread(target=worker, name=f"Worker-{i+1}") for i in range(NUM_WORKERS)]
    for th in threads:
        write_log("one-todo", f"スレッド開始: {th.name}", None, log_file, html_file)
        th.start()
        write_log("one-done", f"スレッド起動完了: {th.name}", None, log_file, html_file)
    write_log("all-done", "全ワーカー起動完了", None, log_file, html_file)

    # ---- タスク投入 ----
    write_log("all-start", f"タスク投入開始: 件数={NUM_WORKERS}", None, log_file, html_file)
    for tid in range(1, NUM_WORKERS+1):
        write_log("one-todo", f"タスク投入: task_id={tid}", None, log_file, html_file)
        task_queue.put(tid)
    write_log("all-done", "タスク投入完了", None, log_file, html_file)

    # ---- 完了待機 ----
    write_log("all-start", "全タスク完了待機開始", None, log_file, html_file)
    task_queue.join()
    write_log("all-done", "全タスク完了待機終了", None, log_file, html_file)

    # ---- ワーカー終了待機 ----
    write_log("all-start", "ワーカー終了シグナル送信", None, log_file, html_file)
    for _ in threads:
        task_queue.put(None)
    for th in threads:
        write_log("one-todo", f"スレッド結合待機: {th.name}", None, log_file, html_file)
        th.join()
        write_log("one-done", f"スレッド終了完了: {th.name}", None, log_file, html_file)
    write_log("all-done", "全ワーカー終了完了", None, log_file, html_file)

    # ---- 結果ログ ----
    write_log("all-start", "結果ログ出力開始", None, log_file, html_file)
    while not result_queue.empty():
        tid, name = result_queue.get()
        write_log("one-done", f"結果出力: {tid}→{name}", tid, log_file, html_file)
    write_log("all-done", "結果ログ出力完了", None, log_file, html_file)

    # ---- 全体完了／HTML閉じ ----
    write_log("all-finish", "処理全体完了", None, log_file, html_file)

    # ---- サーバープロセス終了 ----
    write_log("all-start", "サーバー停止処理開始", None, log_file, html_file)
    server_proc.terminate()
    write_log("one-todo", "サーバー terminate コマンド送信", None, log_file, html_file)
    server_proc.wait()
    write_log("one-done", "サーバー停止完了", None, log_file, html_file)

    # ---- HTML閉じ ----
    html_file.write_text(html_file.read_text() + "</pre></body></html>", encoding="utf-8")

if __name__ == "__main__":
    main()
