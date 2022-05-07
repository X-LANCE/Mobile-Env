#!/usr/bin/python3

import uiautomator2

device = uiautomator2.connect()
xml = device.dump_hierarchy()
with open("../window_dump.xml", "w") as f:
    f.write(xml + "\n")
