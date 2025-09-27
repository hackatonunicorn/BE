#!/bin/bash

# Startup VC Database Backup Script
# This script creates automated backups of the PostgreSQL database

set -e

# Configuration
BACKUP_DIR="/backups"
DB_HOST="${POSTGRES_HOST:-postgres}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-startup_vc}"
DB_USER="${POSTGRES_USER:-postgres}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/backup_${DB_NAME}_${TIMESTAMP}.sql"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

# S3 Configuration (optional)
S3_BUCKET="${BACKUP_S3_BUCKET:-}"
AWS_REGION="${AWS_REGION:-us-east-1}"

# Logging
LOG_FILE="/backups/backup.log"
exec > >(tee -a "$LOG_FILE")
exec 2>&1

echo "Starting backup process at $(date)"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Function to send notification
send_notification() {
    local status=$1
    local message=$2
    
    if [ "$status" = "success" ]; then
        echo "✅ Backup completed successfully: $message"
    else
        echo "❌ Backup failed: $message"
    fi
    
    # Send to notification service if available
    if [ -n "$NOTIFICATION_WEBHOOK" ]; then
        curl -X POST "$NOTIFICATION_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"status\": \"$status\", \"message\": \"$message\", \"timestamp\": \"$(date -Iseconds)\"}"
    fi
}

# Function to upload to S3
upload_to_s3() {
    local file_path=$1
    
    if [ -n "$S3_BUCKET" ] && [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
        echo "Uploading backup to S3..."
        
        aws s3 cp "$file_path" "s3://$S3_BUCKET/database-backups/" \
            --region "$AWS_REGION" \
            --storage-class STANDARD_IA
        
        if [ $? -eq 0 ]; then
            echo "✅ Backup uploaded to S3 successfully"
            return 0
        else
            echo "❌ Failed to upload backup to S3"
            return 1
        fi
    else
        echo "⚠️ S3 configuration not provided, skipping S3 upload"
        return 0
    fi
}

# Function to cleanup old backups
cleanup_old_backups() {
    echo "Cleaning up backups older than $RETENTION_DAYS days..."
    
    # Local cleanup
    find "$BACKUP_DIR" -name "backup_*.sql" -type f -mtime +$RETENTION_DAYS -delete
    
    # S3 cleanup
    if [ -n "$S3_BUCKET" ] && [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
        aws s3 ls "s3://$S3_BUCKET/database-backups/" \
            --region "$AWS_REGION" \
            --recursive | \
        while read -r line; do
            create_date=$(echo "$line" | awk '{print $1" "$2}')
            create_date_epoch=$(date -d "$create_date" +%s)
            older_than_epoch=$(date -d "$RETENTION_DAYS days ago" +%s)
            
            if [ "$create_date_epoch" -lt "$older_than_epoch" ]; then
                file_name=$(echo "$line" | awk '{print $4}')
                aws s3 rm "s3://$S3_BUCKET/$file_name" --region "$AWS_REGION"
                echo "Deleted old S3 backup: $file_name"
            fi
        done
    fi
    
    echo "✅ Cleanup completed"
}

# Function to verify backup integrity
verify_backup() {
    local backup_file=$1
    
    echo "Verifying backup integrity..."
    
    # Check if backup file exists and is not empty
    if [ ! -f "$backup_file" ] || [ ! -s "$backup_file" ]; then
        echo "❌ Backup file is missing or empty"
        return 1
    fi
    
    # Check if backup contains expected data
    if ! grep -q "PostgreSQL database dump" "$backup_file"; then
        echo "❌ Backup file does not contain PostgreSQL dump header"
        return 1
    fi
    
    # Check backup file size (should be > 1KB)
    backup_size=$(stat -f%z "$backup_file" 2>/dev/null || stat -c%s "$backup_file" 2>/dev/null)
    if [ "$backup_size" -lt 1024 ]; then
        echo "❌ Backup file is too small ($backup_size bytes)"
        return 1
    fi
    
    echo "✅ Backup verification passed (size: $backup_size bytes)"
    return 0
}

# Main backup process
main() {
    echo "Creating database backup..."
    echo "Database: $DB_NAME"
    echo "Host: $DB_HOST:$DB_PORT"
    echo "Backup file: $BACKUP_FILE"
    
    # Create database backup
    if pg_dump \
        --host="$DB_HOST" \
        --port="$DB_PORT" \
        --username="$DB_USER" \
        --dbname="$DB_NAME" \
        --verbose \
        --clean \
        --if-exists \
        --create \
        --format=plain \
        --file="$BACKUP_FILE"; then
        
        echo "✅ Database backup created successfully"
        
        # Verify backup
        if verify_backup "$BACKUP_FILE"; then
            
            # Compress backup
            echo "Compressing backup..."
            gzip "$BACKUP_FILE"
            BACKUP_FILE="${BACKUP_FILE}.gz"
            
            # Upload to S3
            upload_to_s3 "$BACKUP_FILE"
            
            # Cleanup old backups
            cleanup_old_backups
            
            # Create backup metadata
            cat > "${BACKUP_FILE}.meta" << EOF
{
    "backup_file": "$(basename "$BACKUP_FILE")",
    "database": "$DB_NAME",
    "host": "$DB_HOST",
    "port": "$DB_PORT",
    "timestamp": "$(date -Iseconds)",
    "size_bytes": $(stat -f%z "$BACKUP_FILE" 2>/dev/null || stat -c%s "$BACKUP_FILE" 2>/dev/null),
    "compressed": true,
    "retention_days": $RETENTION_DAYS
}
EOF
            
            send_notification "success" "Backup created: $(basename "$BACKUP_FILE")"
            echo "Backup process completed successfully at $(date)"
            
        else
            send_notification "error" "Backup verification failed"
            exit 1
        fi
        
    else
        send_notification "error" "Database backup failed"
        exit 1
    fi
}

# Handle script arguments
case "${1:-backup}" in
    "backup")
        main
        ;;
    "cleanup")
        cleanup_old_backups
        ;;
    "verify")
        if [ -z "$2" ]; then
            echo "Usage: $0 verify <backup_file>"
            exit 1
        fi
        verify_backup "$2"
        ;;
    "restore")
        if [ -z "$2" ]; then
            echo "Usage: $0 restore <backup_file>"
            exit 1
        fi
        echo "Restore functionality not implemented yet"
        exit 1
        ;;
    *)
        echo "Usage: $0 {backup|cleanup|verify|restore}"
        exit 1
        ;;
esac
