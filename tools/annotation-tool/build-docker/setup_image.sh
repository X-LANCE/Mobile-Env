#!/bin/bash
# Copyright 2023 SJTU X-Lance Lab
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Created by Danyang Zhang @X-Lance.

ANDROID_HOME="/root/Android/Sdk"
AVD_NAME="Pixel_2_API_30_ga_x64"

avdmanager create avd -n $AVD_NAME -c 8G -k "system-images;android-30;google_apis;x86_64" -d pixel_2
cd ~/.android/avd/$AVD_NAME.avd/
sed -i.bak -e 's#^\(image\.sysdir\.1[[:space:]]*=[[:space:]]*\)Sdk/#\1#g' config.ini
cd ~/
./syscert_setup.exp $ANDROID_HOME/emulator $AVD_NAME
