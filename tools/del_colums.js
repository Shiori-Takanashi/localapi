import Database from 'better-sqlite3';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const dbPath = path.resolve(__dirname, '../database/db.sqlite3');
const db = new Database(dbPath);

// 残す列
const keepColumns = [
    'national_dex', 'ja', 'en', 'type_first', 'type_second', 'front_default_url',
    'base_h', 'base_a', 'base_b', 'base_c', 'base_d', 'base_s'
];

// テンポラリテーブルを作成
const createStmt = `
  CREATE TABLE pokedex_pokemon_new AS
  SELECT ${keepColumns.join(', ')}
  FROM pokedex_pokemon;
`;
db.exec(createStmt);
console.log('✅ 新テーブル作成完了');

// 元テーブル削除
db.exec(`DROP TABLE pokedex_pokemon;`);
console.log('✅ 旧テーブル削除完了');

// リネーム
db.exec(`ALTER TABLE pokedex_pokemon_new RENAME TO pokedex_pokemon;`);
console.log('✅ テーブルリネーム完了');

db.close();
