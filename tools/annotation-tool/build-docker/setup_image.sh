#!/bin/bash

ANDROID_HOME="/root/Android/Sdk"
AVD_NAME="Pixel_2_API_30_ga_x64"

avdmanager create avd -n $AVD_NAME -c 8G -k "system-images;android-30;google_apis;x86_64" -d pixel_2
cd ~/.android/avd/$AVD_NAME.avd/
sed -i.bak -e 's#^\(image\.sysdir\.1[[:space:]]*=[[:space:]]*\)Sdk/#\1#g' config.ini
cd ~/
./syscert_setup.exp $ANDROID_HOME/emulator $AVD_NAME
