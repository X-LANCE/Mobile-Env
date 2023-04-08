#!/usr/bin/python3

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
