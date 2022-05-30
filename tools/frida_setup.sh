#!/bin/bash
# vimc: call SyntaxRange#Include('expect <<"EOF"', 'EOF', 'expect', 'NonText'):

export EMULATOR_PATH=${1:-$HOME/Android/Sdk/emulator}
export AVD_NAME=${2:-Pixel_2_API_30_x64}
export FRIDA_SERVER=${3:-frida-server-14.2.2-android-x86_64.xz}

rm -f ${FRIDA_SERVER%.xz}

expect <<"EOF"
#puts $env(HOME)
set env(LD_LIBRARY_PATH) "$env(EMULATOR_PATH)/lib64:$env(EMULATOR_PATH)/lib64/qt/lib:$env(EMULATOR_PATH)/lib64/gles_swiftshader"
spawn $env(EMULATOR_PATH)/emulator -writable-system -no-snapshot -no-audio -verbose -avd $env(AVD_NAME) -ports 33375,5555
set emulator_process $spawn_id
set timeout 300

proc wait_for_adb {} {
    while {[catch {exec adb get-state} results]} {
        puts "\x1b\[5;31m$results\x1b\[0m"
        sleep 1
    }
    if {$results == "device"} {
        return true
    } else {
        return false
    }
}

proc wait_for_launch {emulator_process} {
    expect {
        timeout {
            puts "\x1b\[5;31mTIMEOUT!\x1b\[0m"
            exit
        }
        -i $emulator_process "boot completed" {
            puts "\x1b\[32mBOOTED!\x1b\[0m"
            sleep 1
        }
    }
    wait_for_adb
}

proc execute_step args {
    set results [eval exec $args]
    puts "\x1b\[32mSTEP: \x1b\[0m$results"
    sleep 1
}

execute_step xz -d -k $env(FRIDA_SERVER)

wait_for_launch $emulator_process
execute_step adb root
wait_for_adb
execute_step adb push [string range $env(FRIDA_SERVER) 0 [expr [string length $env(FRIDA_SERVER)] - 4]] /data/local/tmp/frida-server
execute_step adb shell chmod 755 /data/local/tmp/frida-server

puts "\x1b\[32mSysCert Configured Successfully!\x1b\[0m"
#interact
exit
EOF

pip install frida==14.2.2 frida-tools