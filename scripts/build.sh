#!/bin/bash

set -euo pipefail

# --------------------------------------------------
# Load Environment
# --------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/android-env.sh"

# --------------------------------------------------
# Configuration
# --------------------------------------------------

BUILD_TASK="${1:-assembleDebug}"

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_FILE="$LOG_HOME/builds/build-$TIMESTAMP.log"

# --------------------------------------------------
# Locate Project
# --------------------------------------------------

CURRENT_DIR="$PWD"

while [ "$CURRENT_DIR" != "/" ]; do
    if [ -f "$CURRENT_DIR/settings.gradle.kts" ] || [ -f "$CURRENT_DIR/settings.gradle" ]; then
        PROJECT_DIR="$CURRENT_DIR"
        break
    fi
    CURRENT_DIR=$(dirname "$CURRENT_DIR")
done

if [ -z "$PROJECT_DIR" ]; then
    echo "❌ Not inside an Android Gradle project."
    exit 1
fi

# --------------------------------------------------
# Verify Gradle Wrapper
# --------------------------------------------------

if [ ! -f "$PROJECT_DIR/gradlew" ]; then
    echo "❌ gradlew not found."
    exit 1
fi

chmod +x "$PROJECT_DIR/gradlew"

# --------------------------------------------------
# Build Information
# --------------------------------------------------

echo
echo "==========================================="
echo " Android Build"
echo "==========================================="
echo
echo "Project : $(basename "$PROJECT_DIR")"
echo "Task    : $BUILD_TASK"
echo "Log     : $LOG_FILE"
echo

START=$(date +%s)

# --------------------------------------------------
# Build
# --------------------------------------------------

cd "$PROJECT_DIR"

if ./gradlew "$BUILD_TASK" 2>&1 | tee "$LOG_FILE"; then

    END=$(date +%s)
    DURATION=$((END - START))

    echo
    echo "✅ Build Successful"
    echo "Time : ${DURATION}s"
    echo "Log  : $LOG_FILE"
    exit 0

else

    END=$(date +%s)
    DURATION=$((END - START))

    echo
    echo "❌ Build Failed"
    echo "Time : ${DURATION}s"
    echo "Log  : $LOG_FILE"
    exit 1

fi
