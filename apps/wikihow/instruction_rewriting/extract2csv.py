#!/usr/bin/python3

from android_env.proto import task_pb2
from google.protobuf import text_format
import os
import csv

import os.path

task_path = "../templates.miniout"
tasks = list(
        sorted(
            filter(lambda f: f.endswith(".textproto"),
                os.listdir(task_path))))

with open("instruction.csv", "w") as out_f:
    writer = csv.DictWriter(out_f, [ "task"
                                   , "index"
                                   , "text"
                                   , "label"
                                   ])
    writer.writeheader()

    for t in tasks:
        with open(os.path.join(task_path, t)) as t_f:
            task = task_pb2.Task()
            text_format.Parse(t_f.read(), task)

        for i, cmd in enumerate(task.command):
            cmd = str(cmd)
            text = cmd[6].upper() + cmd[7:] if cmd.startswith("Then, ") else cmd
            if not text.startswith("Search"):
                continue
            writer.writerow({ "task": t
                            , "index": i
                            , "text": text
                            , "label": ""
                            })

