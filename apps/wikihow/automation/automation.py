#!/usr/bin/python3

import uiautomator2

PACKAGE_NAME = "com.wikihow.wikihowapp"

device = uiautomator2.connect()
device.app_wait(PACKAGE_NAME)
print(device.app_current())
