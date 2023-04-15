# Copyright 2023 SJTU X-Lance Lab
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Created by Danyang Zhang @X-Lance.
"""

from android_env.proto import task_pb2
import os.path
from typing import Optional

def fix_path(task: task_pb2.Task, task_directory: str) -> task_pb2.Task:
    """
    Fixes the path setting in `task` and return it back.

    Args:
        task (task_pb2.Task): task config object
        task_directory (str): the path which is expected to be the base path,
          usually is the directory of the task config file

    Return:
        task_pb2.Task: task config object with the fixed path
    """

    for st in task.setup_steps:
        _fix(st, task_directory)
    for st in task.reset_steps:
        _fix(st, task_directory)
    for evt_s in task.event_sources:
        if evt_s.HasField("icon_match"):
            attribute_name: Optional[str] = evt_s.WhichOneof("event")
            if attribute_name=="icon_match" or attribute_name=="icon_detect_match":
                path: str = getattr(evt_s, attribute_name).path
                if not os.path.isabs(path):
                    getattr(evt_s, attribute_name).path =\
                            os.path.normpath(os.path.join(task_directory, path))
    return task

def _fix(setup: task_pb2.SetupStep, task_directory: str):
    if setup.HasField("adb_call")\
            and setup.adb_call.HasField("install_apk"):
        apk_path = setup.adb_call.install_apk.filesystem.path
        if not os.path.isabs(apk_path):
            setup.adb_call.install_apk.filesystem.path =\
                    os.path.normpath(os.path.join(task_directory, apk_path))
