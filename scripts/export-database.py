"""Export the demo DBs without PowerShell encoding changes or passwords in arguments."""
from pathlib import Path
import subprocess

root=Path(__file__).resolve().parents[1]
result=subprocess.run(['docker','compose','exec','-T','mysql-db','sh','-c',
    'exec mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" --databases product_db order_db --no-tablespaces --set-gtid-purged=OFF --single-transaction --default-character-set=utf8mb4'],cwd=root,capture_output=True)
if result.returncode: raise SystemExit(result.stderr.decode())
target=root/'database/backup.sql'
target.write_bytes(result.stdout)
print(f'Exported {target.name}: {target.stat().st_size} bytes')
