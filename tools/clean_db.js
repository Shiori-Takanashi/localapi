import Database from 'better-sqlite3';
import path from 'path';
import { fileURLToPath } from 'url';

// __dirname 再現
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// DBパス
const dbPath = path.resolve(__dirname, '../database/db.sqlite3');
const db = new Database(dbPath);

// 削除クエリ
const stmt = db.prepare(`
  DELETE FROM pokedex_pokemon
  WHERE
    species_id NOT BETWEEN '00001' AND '01025'
    OR pokemon_id NOT BETWEEN '00001' AND '01025'
    OR form_id NOT BETWEEN '00001' AND '01025'
`);
const info = stmt.run();
console.log(`✅ 削除完了: ${info.changes} 件のレコードを削除しました`);

// VACUUM
db.exec('VACUUM');
console.log('✅ VACUUM完了: 空き領域を解放しました');

db.close();
