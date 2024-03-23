#!/usr/bin/python3
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
from google.protobuf import text_format
import os.path
import re
import modifiers
from typing import Match, Dict, List, Set
from typing import Callable, TypeVar
import functools

import argparse
import sys

template_item_pattern = re.compile(r"<(?:(?P<modifiers>\w+'?(?:,\w+'?)*):)?(?P<identifier>\w+)>")

def replace_item(conf_dict: Dict[str, str], match_: Match[str]) -> str:
    identifier = match_.group("identifier")
    keyword = conf_dict.get(identifier, "")

    if match_.group("modifiers") is not None:
        modifiers_ = match_.group("modifiers").split(",")
        for mdf in modifiers_[-1::-1]:
            if mdf=="no_quote":
                return keyword
            elif mdf[-1]=="'":
                keyword = ",".join(map(getattr(modifiers, mdf[:-1]), keyword.split(",")))
            else:
                keyword = getattr(modifiers, mdf)(keyword)

    keyword = keyword.replace("\"", "\\\"").replace("'", "\\'")
    return keyword

def max_id(event_slot: task_pb2.EventSlot) -> int:
    #  function `max_id` {{{ # 
    if not event_slot.IsInitialized():
        return 0
    max_id_ = event_slot.id
    for evt in event_slot.events:
        if evt.HasField("event"):
            max_id_ = max(max_id_, max_id(evt.event))
    return max_id_
    #  }}} function `max_id` # 
def update_id(event_slot: task_pb2.EventSlot, bias: int):
    #  function `update_id` {{{ # 
    if not event_slot.IsInitialized():
        return
    if event_slot.id>0:
        event_slot.id = event_slot.id + bias
    for evt in event_slot.events:
        if evt.HasField("id"):
            evt.id = evt.id + bias
        else:
            update_id(evt.event, bias)
    for i in range(len(event_slot.prerequisite)):
        event_slot.prerequisite[i] = event_slot.prerequisite[i] + bias
    #  }}} function `update_id` # 

C = TypeVar("C")
def apply_to_event_slots(function: Callable[[task_pb2.EventSlot], C],
        eventslots: task_pb2.TaskEventSlots) -> List[C]:
    #  function `apply_to_event_slots` {{{ # 
    score_result = function(eventslots.score_listener)
    reward_result = function(eventslots.reward_listener)
    episode_end_result = function(eventslots.episode_end_listener)
    extra_result = function(eventslots.extra_listener)
    json_extra_result = function(eventslots.json_extra_listener)
    instruction_result = function(eventslots.instruction_listener)

    return [ score_result
           , reward_result
           , episode_end_result
           , extra_result
           , json_extra_result
           , instruction_result
           ]
    #  }}} function `apply_to_event_slots` # 

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=str, required=True)
    parser.add_argument("--template-path", "-p", default="templates", type=str)
    parser.add_argument("--output", "-o", type=str)
    args = parser.parse_args()

    extra_setup_steps: Set[int] = set() # index-1
    extra_reset_steps: Set[int] = set() # index-1

    with open(args.task) as f:
        conf_list: List[str] = []
        for i, l in enumerate(f):
            items: List[str] = l.strip().split()
            conf_list.append(items[0])
            if i>0 and len(items)>=1:
                if "s" in items[1]:
                    extra_setup_steps.add(i-1)
                if "r" in items[1]:
                    extra_reset_steps.add(i-1)

    conf_path = os.path.dirname(args.task)

    task_list = []
    for c in conf_list:
        # read keywords
        with open(os.path.join(conf_path, c + ".conf")) as f:
            conf_dict = {}
            for l in f:
                key, value = l.strip().split(": ", maxsplit=1)
                conf_dict[key] = value

        template_name, _ = c.split("-", maxsplit=1)

        # replace keywords
        with open(os.path.join(args.template_path, template_name + ".textproto.template")) as f:
            textproto = []
            for l in f:
                l = template_item_pattern.sub(functools.partial(replace_item, conf_dict), l)
                textproto.append(l)
            textproto = "".join(textproto)

        # parse protobuf
        task = task_pb2.Task()
        text_format.Parse(textproto, task)
        task_list.append(task)

    # merge the fields
    target_task = task_pb2.Task()
    event_id_base = 0

    target_task.CopyFrom(task_list[0])
    #  rebase event slots {{{ # 
    score_slot = task_pb2.EventSlot()
    score_slot.type = task_pb2.EventSlot.Type.OR
    instance = score_slot.events.add()
    instance.event.CopyFrom(task_list[0].event_slots.score_listener)
    target_task.event_slots.score_listener.CopyFrom(score_slot)

    reward_slot = task_pb2.EventSlot()
    reward_slot.type = task_pb2.EventSlot.Type.OR
    instance = reward_slot.events.add()
    instance.event.CopyFrom(task_list[0].event_slots.reward_listener)
    target_task.event_slots.reward_listener.CopyFrom(reward_slot)

    #episode_end_slot = task_pb2.EventSlot()
    #episode_end_slot.type = task_pb2.EventSlot.Type.OR
    #instance = episode_end_slot.events.add()
    #instance.event.CopyFrom(task_list[0].event_slots.episode_end_listener)
    #target_task.event_slots.episode_end_listener.CopyFrom(episode_end_slot)

    extra_slot = task_pb2.EventSlot()
    extra_slot.type = task_pb2.EventSlot.Type.OR
    instance = extra_slot.events.add()
    instance.event.CopyFrom(task_list[0].event_slots.extra_listener)
    target_task.event_slots.extra_listener.CopyFrom(extra_slot)

    json_extra_slot = task_pb2.EventSlot()
    json_extra_slot.type = task_pb2.EventSlot.Type.OR
    instance = json_extra_slot.events.add()
    instance.event.CopyFrom(task_list[0].event_slots.json_extra_listener)
    target_task.event_slots.json_extra_listener.CopyFrom(json_extra_slot)

    instruction_slot = task_pb2.EventSlot()
    instruction_slot.type = task_pb2.EventSlot.Type.OR
    instance = instruction_slot.events.add()
    instance.event.CopyFrom(task_list[0].event_slots.instruction_listener)
    target_task.event_slots.instruction_listener.CopyFrom(instruction_slot)
    #  }}} rebase event slots # 

    event_id_base = max(
            max(map(lambda evt: evt.id, task_list[0].event_sources)),
            max(apply_to_event_slots(max_id, task_list[0].event_slots)))

    for i, t in enumerate(task_list[1:]):
        target_task.id = "{:}-{:}".format(target_task.id, t.id)
        target_task.name = "{:}, {:}".format(target_task.name,
            t.name.split(" - ", maxsplit=1)[-1])
        target_task.description = "{:}\n{:}".format(target_task.description,
            t.description)

        if i in extra_setup_steps:
            target_task.setup_steps.extend(t.setup_steps)
        if i in extra_reset_steps:
            target_task.reset_steps.extend(t.reset_steps)

        #  calculate new base {{{ # 
        for evt in t.event_sources:
            evt.id = evt.id + event_id_base
        apply_to_event_slots(functools.partial(update_id, bias=event_id_base),
            t.event_slots)

        event_id_base = max(
                max(map(lambda evt: evt.id, t.event_sources)),
                max(apply_to_event_slots(max_id, t.event_slots)))
        #  }}} calculate new base # 

        #  merge event sources slots {{{ # 
        target_task.event_sources.extend(t.event_sources)

        new_slot = target_task.event_slots.score_listener.events.add()
        new_slot.event.CopyFrom(t.event_slots.score_listener)

        new_slot = target_task.event_slots.reward_listener.events.add()
        new_slot.event.CopyFrom(t.event_slots.reward_listener)

        #new_slot = target_task.event_slots.episode_end_listener.events.add()
        #new_slot.event.CopyFrom(t.event_slots.episode_end_listener)

        new_slot = target_task.event_slots.extra_listener.events.add()
        new_slot.event.CopyFrom(t.event_slots.extra_listener)

        new_slot = target_task.event_slots.json_extra_listener.events.add()
        new_slot.event.CopyFrom(t.event_slots.json_extra_listener)

        new_slot = target_task.event_slots.instruction_listener.events.add()
        new_slot.event.CopyFrom(task_list[i].event_slots.episode_end_listener)
        del new_slot.event.transformation[:]
        new_slot.event.transformation.append("y = ["\
                                            + ", ".join(map(repr, t.command))\
                                            + "]")

        new_slot = target_task.event_slots.instruction_listener.events.add()
        new_slot.event.CopyFrom(t.event_slots.instruction_listener)
        #  }}} merge event slots # 

        target_task.extras_spec.extend(t.extras_spec)
        t.command[0] = "Then, "\
                     + t.command[0][0].lower()\
                     + t.command[0][1:]
        target_task.command.extend(t.command)
        target_task.vocabulary.extend(t.vocabulary)

    target_task.event_slots.episode_end_listener.CopyFrom(
        task_list[-1].event_slots.episode_end_listener)

    target_task.vocabulary[:] = list(set(target_task.vocabulary))

    if args.output is not None:
        with open(args.output, "w") as f:
            text_format.PrintMessage(target_task, f,
                as_utf8=True,
                use_short_repeated_primitives=True,
                force_colon=True)
    else:
        text_format.PrintMessage(target_task, sys.stdout,
            as_utf8=True,
            use_short_repeated_primitives=True,
            force_colon=True)

if __name__ == "__main__":
    main()
