#!/usr/bin/python3

import pickle as pkl
import sys
#import traceback

import os
import os.path

from android_env.proto import task_pb2
from google.protobuf import text_format

from typing import List, Dict
from typing import Any, Union

# pkl_name.%d.pkl:2:211
pkl_name_pattern: str
start_index: str
end_index: str
pkl_name_pattern, start_index, end_index = sys.argv[1].rsplit(":", maxsplit=2)
start_index = int(start_index)
end_index = int(end_index)

output_path: str = sys.argv[2] if len(sys.argv)>=3 else "pkl_resaved"
textproto_path: str = sys.argv[3] if len(sys.argv)>=4 else "textprotos"

task_definition_files: List[str] = list( map( lambda f: f[:-10]
                                            , filter( lambda f: f.endswith(".textproto")
                                                    , os.listdir(textproto_path)
                                                    )
                                            )
                                       )
task_definition_ids: Dict[str, str] = {}
for f_n in task_definition_files:
    with open(os.path.join(textproto_path, f_n + ".textproto")) as f:
        prototext: str = f.read()

    task_definition = task_pb2.Task()
    text_format.Parse(prototext, task_definition)

    task_definition_ids[str(getattr(task_definition, "id"))] = f_n

for idx in range(start_index, end_index+1):
    pkl_name: str = pkl_name_pattern % idx
    if idx%500==0:
        print("\x1b[37m{:d}\x1b[0m=>\x1b[32m{:d}\x1b[0m=>\x1b[37m{:d}\x1b[0m\t{:}"\
                .format( start_index
                       , idx
                       , end_index
                       , pkl_name
                       )
             )
    if not os.path.exists(pkl_name):
        continue
    with open(pkl_name, "rb") as in_f:
        while True:
            try:
                annotation_list: Dict[str, Any] = pkl.load(in_f)

                task_id: str = annotation_list[0]["task_id"]

                task_definition_id: str = task_definition_ids[task_id]

                ###***^^^∘∘∘^^^***###

                task_obj = task_pb2.Task()
                with open(os.path.join(textproto_path, "{:}.textproto".format(task_definition_id))) as prt_f:
                    text_format.Parse(prt_f.read(), task_obj)

                for d in annotation_list:
                    if "input_token" in d:
                        d["input_token"] = str(task_obj.vocabulary[d["input_token"]])

                ###∗∗∗㈠㈠㈠===㈠㈠㈠∗∗∗###

                output_file = os.path.join(output_path, "{:}.tmp.pkl".format(task_definition_id))
                is_first = not os.path.exists(output_file)
                with open(output_file, "ab") as out_f:
                    if is_first:
                        pkl.dump({ "otask_id": task_id
                                 , "otask_name": annotation_list[0]["task"]
                                 , "task_definition_id": task_definition_id
                                 }, out_f)
                    pkl.dump(annotation_list, out_f)
            except EOFError:
                break

resaved_pickles: List[str] = list( filter( lambda f: f.endswith(".tmp.pkl")
                                         , os.listdir(output_path)
                                         )
                                 )
for pkl_n in resaved_pickles:
    annotation_dict: Dict[ str
                         , Union[ Dict[str, str]
                                , List[Dict[str, Any]]
                                ]
                         ] = {}
    with open(os.path.join(output_path, pkl_n), "rb") as in_f\
            , open(os.path.join(output_path, pkl_n[:-8] + ".pkl"), "wb") as out_f:

        meta_dict: Dict[str, str] = pkl.load(in_f)
        annotation_dict["meta"] = meta_dict

        annotation_dict["trajectories"]: List[Dict[str, Any]] = []
        while True:
            try:
                annotation_list: Dict[str, Any] = pkl.load(in_f)
                annotation_dict["trajectories"].append(annotation_list)
            except EOFError:
                break

        pkl.dump(annotation_dict, out_f)
    os.remove(os.path.join(output_path, pkl_n))
