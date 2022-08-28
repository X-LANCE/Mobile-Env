#!/usr/bin/python3

import re
import sys
import os.path

input_file = sys.argv[1]
stepname = sys.argv[2]
if len(sys.argv)>3:
    dump_path = sys.argv[3]

template_item_pattern = re.compile(r"<(?:(?P<modifiers>\w+(?:,\w+)*):)?(?P<identifier>\w+)>")

item_set = set()
with open(input_file) as f:
    for l in f:
        items = template_item_pattern.findall(l)
        for _, id_ in items:
            item_set.add(id_)

classname = os.path.basename(input_file).split(".")[0]
with open(os.path.join(dump_path, "{:}-{:}.conf".format(classname, stepname)), "w") as f:
    for itm in item_set:
        f.write("{:}: <VALUE>\n".format(itm))

