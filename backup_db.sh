﻿#!/bin/bash

FECHA=$(date +%Y%m%d_%H%M%S)
mkdir -p backups

echo "ðŸ—ƒï¸ Realizando backup de MongoDB..."
mongodump --out=backups/backup_$FECHA
echo "âœ… Backup guardado en backups/backup_$FECHA"

