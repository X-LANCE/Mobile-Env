#!/usr/bin/python3

import re
import os
import os.path
import yaml

template_path = "../templates"
template_item_pattern = re.compile(r"<(?:(?P<modifiers>\w+(?:,\w+)*):)?(?P<identifier>\w+)>")

identifiers_dict = {}

for tpl in os.listdir(template_path):
    if not tpl.endswith(".textproto.template")\
            or tpl=="basic.textproto.template":
        continue

    with open(os.path.join(template_path, tpl)) as f:
        class_name = tpl.split(".", maxsplit=1)[0]
        identifiers_dict[class_name] = []

        item_set = set()
        for l in f:
            items = template_item_pattern.findall(l)
            for _, id_ in items:
                item_set.add(id_)
        identifiers_dict[class_name] += item_set

with open("identifiers.yaml", "w") as f:
    yaml.dump(identifiers_dict, f, yaml.Dumper, encoding="utf-8")
