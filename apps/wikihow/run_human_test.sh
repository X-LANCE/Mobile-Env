#!/bin/bash

python ../../examples/run_human_agent.py \
    --avd_name='Pixel_2_API_30_ga_x64_1' \
    --android_avd_home=/home/david/.android/avd \
    --android_sdk_root=/home/david/Library/Android/sdk \
    --emulator_path=/home/david/Android/Sdk/emulator/emulator \
    --adb_path=/home/david/Android/Sdk/platform-tools/adb \
    --task_path=wikihow_search.textproto\
    --norun_headless\
    --mitm syscert\
    --frida_script ../../tools/frida-script.js
