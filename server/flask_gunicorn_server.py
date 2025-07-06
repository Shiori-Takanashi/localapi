from flask import Flask, Response
import sqlite3, json, time, random
from flask_cors import CORS
from pathlib import Path

# ────────────────
# パス設定
# ────────────────
BASE_DIR  = Path(__file__).resolve().parent.parent
DB_PATH   = BASE_DIR / "database" / "db.sqlite3"
JSON_DIR  = BASE_DIR / "json"

# ────────────────
# Flask 初期化
# ────────────────
app = Flask(__name__, static_folder=None)
CORS(app)

# ────────────────
# DB接続ユーティリティ
# ────────────────
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.text_factory = lambda b: b.decode("utf-8", errors="replace")
    return conn

# ────────────────
# APIエンドポイント定義
# ────────────────
@app.route('/db/<int:idx>', methods=['GET'])
def get_species_by_id(idx):
    idx_str = str(idx).zfill(5)
    conn = get_db_connection()
    cur = conn.execute("SELECT * FROM pokedex_pokemon WHERE national_dex = ?", (idx_str,))
    row = cur.fetchone()
    conn.close()

    if row:
        return Response(
            json.dumps(dict(row), ensure_ascii=False),
            content_type="application/json; charset=utf-8")
    return Response(
        json.dumps({'error': '指定されたIDのデータが見つかりません'}, ensure_ascii=False),
        content_type="application/json; charset=utf-8",
        status=404)

@app.route('/db/delay/<int:idx>', methods=['GET'])
def get_species_by_id_with_delay(idx):
    time.sleep(random.randint(3, 6))
    return get_species_by_id(idx)

@app.route('/json/<int:idx>', methods=['GET'])
def get_static_json(idx):
    target_file = JSON_DIR / f"{idx}.json"
    if target_file.exists():
        with open(target_file, encoding="utf-8") as f:
            data = json.load(f)
        return Response(
            json.dumps(data, ensure_ascii=False),
            content_type="application/json; charset=utf-8")
    return Response(
        json.dumps({'error': f'{idx}.json が見つかりません'}, ensure_ascii=False),
        content_type="application/json; charset=utf-8",
        status=404)

@app.route('/json/delay/<int:idx>', methods=['GET'])
def get_static_json_with_delay(idx):
    time.sleep(random.randint(3, 6))
    return get_static_json(idx)

# ────────────────
# ローカル実行用
# ────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6666, debug=True)
