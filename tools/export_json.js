import Database from 'better-sqlite3';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// __dirname 互換
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// パス定義
const dbPath = path.resolve(__dirname, '../database/db.sqlite3');
const outputDir = path.resolve(__dirname, '../json');

const db = new Database(dbPath);

// ディレクトリ作成
if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir);
}

// national_dex（連番）で1〜1025のデータを取得
const stmt = db.prepare(`
  SELECT * FROM pokedex_pokemon
  WHERE national_dex BETWEEN 1 AND 1025
`);

const rows = stmt.all();
console.log(`🔍 データ件数: ${rows.length}`);

// JSONファイルとして出力
for (const row of rows) {
    const id = row.national_dex;
    const jsonPath = path.join(outputDir, `${id}.json`);
    fs.writeFileSync(jsonPath, JSON.stringify(row, null, 2), 'utf-8');
}

console.log('✅ JSON出力完了');
db.close();
