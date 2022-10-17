#!/usr/bin/python3

import json
import os.path
import copy

file_list = [ "dlf.json"
            , "yfw51.json"
            , "zdy023.json"
            ]
annotations_list = []
for f in file_list:
    with open(os.path.join("doccano", f)) as f_obj:
        annotations = json.load(f_obj)
    annotations_list.append(annotations)

merged_annotations = []
for anntt_gr in zip(*annotations_list):
    standard_id = anntt_gr[0]["id"]
    assert all(map(lambda anntt: anntt["id"]==standard_id, anntt_gr))
    merged_annotation = copy.deepcopy(anntt_gr[0])
    for anntt in anntt_gr[1:]:
        merged_annotation["label"] += anntt["label"]
    merged_annotations.append(merged_annotation)

with open("merged_doccano.json", "w") as f:
    json.dump(merged_annotations, f, indent="\t", ensure_ascii=False)
