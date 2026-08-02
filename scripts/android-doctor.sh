#!/bin/bash

source "$(dirname "$0")/android-env.sh"

echo "=============================="
echo " Android Build Environment"
echo "=============================="

echo
echo "Java:"
java --version

echo
echo "ANDROID_HOME:"
echo "$ANDROID_HOME"

echo
echo "SDK Manager:"
sdkmanager --version

echo
echo "ADB:"
adb version

echo
echo "Installed Platforms:"
sdkmanager --list_installed | grep "platforms;"

echo
echo "Installed Build Tools:"
sdkmanager --list_installed | grep "build-tools;"

echo
echo "Installed Platform Tools:"
sdkmanager --list_installed | grep "platform-tools"

echo
echo "Doctor Complete."
