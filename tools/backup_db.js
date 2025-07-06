import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// __dirname 相当の再現（ESMでは直接使えない）
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// パス定義
const dbPath = path.resolve(__dirname, '../database/db.sqlite3');
const backupDir = path.resolve(__dirname, '../backup');

// タイムスタンプ
function getTimestamp() {
    const now = new Date();
    const pad = (n) => String(n).padStart(2, '0');
    const yyyy = now.getFullYear();
    const mm = pad(now.getMonth() + 1);
    const dd = pad(now.getDate());
    const hh = pad(now.getHours());
    const mi = pad(now.getMinutes());
    const ss = pad(now.getSeconds());
    return `${yyyy}${mm}${dd}_${hh}${mi}${ss}`;
}

// 実行本体
function backup() {
    if (!fs.existsSync(dbPath)) {
        console.error('❌ データベースが存在しません:', dbPath);
        process.exit(1);
    }

    if (!fs.existsSync(backupDir)) {
        fs.mkdirSync(backupDir, { recursive: true });
    }

    const dest = path.join(backupDir, `db_${getTimestamp()}.sqlite3`);
    fs.copyFileSync(dbPath, dest);
    console.log('✅ バックアップ完了:', dest);
}

backup();
