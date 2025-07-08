#!/bin/bash
# This script is intended to be called via sudo by the web application
# to perform a Git update.

APP_DIR="/opt/whisper-appliance"
LOG_FILE="$APP_DIR/logs/git-update.log" # Optional: for logging

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

echo "===== Starting Git update: $(date) =====" >> "$LOG_FILE"

if [ ! -d "$APP_DIR" ]; then
    echo "Error: Application directory $APP_DIR not found." | tee -a "$LOG_FILE"
    exit 1
fi

cd "$APP_DIR" || exit 1

if [ ! -d ".git" ]; then
    echo "Error: Not a git repository at $APP_DIR." | tee -a "$LOG_FILE"
    exit 1
fi

# Configure SSH if deploy key exists (copied from auto-update.sh)
if [ -f "./deploy_key_whisper_appliance" ]; then
    export GIT_SSH_COMMAND="ssh -i ./deploy_key_whisper_appliance -o IdentitiesOnly=yes"
    echo "Using deploy key for GitHub access." >> "$LOG_FILE"
fi

echo "Fetching updates from origin main..." >> "$LOG_FILE"
if git fetch origin main >> "$LOG_FILE" 2>&1; then
    echo "Fetch successful." >> "$LOG_FILE"
else
    echo "Error: git fetch failed." >> "$LOG_FILE"
    # Output last few lines of log for Flask to capture
    tail -n 5 "$LOG_FILE"
    exit 1
fi

LOCAL_COMMIT=$(git rev-parse HEAD)
REMOTE_COMMIT=$(git rev-parse origin/main)

if [ "$LOCAL_COMMIT" = "$REMOTE_COMMIT" ]; then
    echo "System is already up to date. Local: $LOCAL_COMMIT" | tee -a "$LOG_FILE"
    echo "===== Git update finished: $(date) =====" >> "$LOG_FILE"
    # Provide a clear message for the UI
    echo "Already up-to-date."
    exit 0
fi

echo "Local commit: $LOCAL_COMMIT" >> "$LOG_FILE"
echo "Remote commit: $REMOTE_COMMIT" >> "$LOG_FILE"
echo "Pulling updates..." >> "$LOG_FILE"

if git pull origin main >> "$LOG_FILE" 2>&1; then
    echo "Git pull successful." >> "$LOG_FILE"
    # Update file permissions for any new/changed shell scripts
    chmod +x $APP_DIR/*.sh 2>/dev/null || true
    chmod +x $APP_DIR/scripts/*.sh 2>/dev/null || true
    echo "Updated file permissions for shell scripts." >> "$LOG_FILE"
    echo "===== Git update finished: $(date) =====" >> "$LOG_FILE"
    # Provide a clear message for the UI
    echo "Update successful. New version: $(git describe --tags --always 2>/dev/null || git rev-parse --short HEAD)"
    exit 0
else
    echo "Error: git pull failed." >> "$LOG_FILE"
    # Output last few lines of log for Flask to capture
    tail -n 10 "$LOG_FILE"
    exit 1
fi
