from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import sqlite3, json, time, random
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "db.sqlite3"
JSON_DIR = BASE_DIR / "json"

app = FastAPI()

# CORS 許可
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 必要に応じて制限可
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.text_factory = lambda b: b.decode("utf-8", errors="replace")
    return conn

@app.get("/db/{idx}")
def get_species_by_id(idx: int):
    idx_str = str(idx).zfill(5)
    conn = get_db_connection()
    cur = conn.execute("SELECT * FROM pokedex_pokemon WHERE national_dex = ?", (idx_str,))
    row = cur.fetchone()
    conn.close()

    if row:
        return JSONResponse(content=dict(row), media_type="application/json")
    raise HTTPException(status_code=404, detail="指定されたIDのデータが見つかりません")

@app.get("/db/delay/{idx}")
def get_species_by_id_with_delay(idx: int):
    time.sleep(random.randint(3, 6))
    return get_species_by_id(idx)

@app.get("/json/{idx}")
def get_static_json(idx: int):
    target_file = JSON_DIR / f"{idx}.json"
    if target_file.exists():
        with open(target_file, encoding="utf-8") as f:
            data = json.load(f)
        return JSONResponse(content=data, media_type="application/json")
    raise HTTPException(status_code=404, detail=f"{idx}.json が見つかりません")

@app.get("/json/delay/{idx}")
def get_static_json_with_delay(idx: int):
    time.sleep(random.randint(3, 6))
    return get_static_json(idx)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,                 # ← 文字列ではなく実体を渡す
        host="0.0.0.0",
        port=7777,
        reload=False
    )
