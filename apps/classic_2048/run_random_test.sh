#!/bin/bash

python ../../examples/run_random_agent.py \
    --avd_name='Pixel_2_API_30_x64' \
    --android_avd_home=/home/david/.android/avd \
    --android_sdk_root=/home/david/Library/Android/sdk \
    --emulator_path=/home/david/Android/Sdk/emulator/emulator \
    --adb_path=/home/david/Android/Sdk/platform-tools/adb \
    --num_steps=500 \
    --task_path=classic_2048.textproto\
    --norun_headless\
