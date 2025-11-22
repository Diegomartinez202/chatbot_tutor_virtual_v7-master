#!/bin/bash
FECHA=$(date +%Y%m%d_%H%M%S)
mkdir -p backups
echo "🗃️ Realizando backup de MongoDB..."
mongodump --out=backups/backup_$FECHA
echo "✅ Backup guardado en backups/backup_$FECHA"