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

import visualization
import random

import pickle as pkl
import sys
import os.path
import os

pkl_path = sys.argv[1]
video_path = sys.argv[2]

with open(pkl_path, "rb") as f:
    record = pkl.load(f)

task_definition_id = record["meta"]["task_definition_id"]
trajectories = record["trajectories"]

#if len(trajectories)==1:
    #index = 0
#else:
    #if len(trajectories)==2:
        #index = 1
    #elif len(trajectories)==3 or len(trajectories)==4:
        #index = random.randrange(2)+1
    #elif len(trajectories)>4:
        #index = 2
#print(pkl_n, len(trajectories), index)

for i, trjtr in enumerate(trajectories):
    dirname = "{:}:{:}%{:}#{:}"\
                .format( task_definition_id
                       , i
                       , len(trajectories)
                       , len(trjtr)
                       )
    os.makedirs( os.path.join( video_path
                             , dirname
                             )
               )
    print(os.path.join(video_path, dirname))

    for j, rcd in enumerate(trjtr[1:]):
        screen = visualization.visualize(rcd, task_definition_id)
        screen.save( os.path.join( video_path
                                 , dirname
                                 , "{:}.jpg".format(j+1)
                                 )
                   )
