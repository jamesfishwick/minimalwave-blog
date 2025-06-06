# Backup Strategy

## Database Backups

### Automatic Backups
- Configured automatic backups for PostgreSQL Flexible Server
- Retention period: 30 days
- Earliest restore point: Rolling backup allowing point-in-time recovery
- Location: East US (primary region)

### Manual Backup Procedures
1. Taking a manual backup:
   ```bash
   az postgres flexible-server backup create \
     --resource-group minimalwave-blog-rg \
     --server-name minimalwave-blog-db-2025
   ```

2. Listing available backups:
   ```bash
   az postgres flexible-server backup list \
     --resource-group minimalwave-blog-rg \
     --server-name minimalwave-blog-db-2025
   ```

### Recovery Procedures
1. Point-in-time restore:
   ```bash
   az postgres flexible-server restore \
     --resource-group minimalwave-blog-rg \
     --name minimalwave-blog-db-restore \
     --source-server minimalwave-blog-db-2025 \
     --restore-time "2025-06-05 20:30:00"
   ```

2. Specific backup restore:
   ```bash
   az postgres flexible-server restore \
     --resource-group minimalwave-blog-rg \
     --name minimalwave-blog-db-restore \
     --source-server minimalwave-blog-db-2025 \
     --backup-id <backup-id>
   ```

## Application Data Backups

### Static Files
1. Media files and uploaded content are stored in Azure Storage
2. Azure Storage automatically maintains redundant copies
3. Geo-redundant storage (GRS) provides cross-region protection

### Export Procedures
Regular exports of critical data:
```bash
# Export database
pg_dump -h minimalwave-blog-db-2025.postgres.database.azure.com -U minimalwave -d minimalwave > backup.sql

# Export media files
az storage blob download-batch \
  --source media \
  --destination ./backup/media \
  --account-name <storage-account>
```

## Monitoring and Verification

### Backup Monitoring
1. Azure Monitor alerts configured for:
   - Failed backup attempts
   - Storage capacity warnings
   - Backup completion status

### Regular Testing
1. Monthly test restore to verify backup integrity
2. Quarterly disaster recovery drill
3. Documentation of restore procedures and verification checklist

## Emergency Contacts

1. Primary Database Administrator:
   - Name: [To be filled]
   - Contact: [To be filled]

2. Backup Administrator:
   - Name: [To be filled]
   - Contact: [To be filled]

## Recovery Time Objective (RTO)
- Database: 1 hour
- Application: 2 hours
- Complete system: 4 hours

## Recovery Point Objective (RPO)
- Maximum data loss: 5 minutes (based on continuous backup)
