@echo off
set FECHA=%date:~6,4%-%date:~3,2%-%date:~0,2%_%time:~0,2%%time:~3,2%
set FECHA=%FECHA: =0%
set OUTPUT=chatbot_tutor_virtual_backup_%FECHA%.zip

echo 🗃️ Comprimiendo proyecto a: %OUTPUT%

powershell Compress-Archive -Path * -DestinationPath %OUTPUT% -Force -CompressionLevel Optimal -Exclude `
.vs, `
*.log, `
*.zip, `
*.pyc, `
__pycache__, `
node_modules, `
*.db-shm, `
*.db-wal, `
*.db, `
*.sqlite

echo ✅ Proyecto comprimido correctamente.
pause
