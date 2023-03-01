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

import random
import torch

#from absl import logging

def text_detector(screen, bboxes):
    #  function `text_detector` {{{ # 
    """
    screen - tensor of float32 with shape (3, height, width)
    bboxes - list of tensor of float32 with shape (1, 4)

    return list of list of str
    """

    decides = random.random()
    event_index = random.randrange(len(bboxes)) if decides<=0.2 else None
    #if decides<=0.2:
        #logging.info("\x1b[32;1;43mText Detected!\x1b[0m")
    return [["Event String"] if i==event_index else ["Test String"] for i, _ in enumerate(bboxes)]
    #  }}} function `text_detector` # 

def text_recognizer(screen, bboxes):
    #  function `text_recognizer` {{{ # 
    """
    screen - tensor of float32 with shape (3, height, width)
    bboxes - list of tensor of float32 with shape (1, 4)

    return list of str
    """

    decides = random.random()
    event_index = random.randrange(len(bboxes)) if decides<=0.2 else None
    #if decides<=0.2:
        #logging.info("Text Reward!")
    return ["Event String" if i==event_index else "Test String" for i, _ in enumerate(bboxes)]
    #  }}} function `text_recognizer` # 

def icon_detector(screen, bboxes):
    #  function `icon_detector` {{{ # 
    """
    screen - tensor of float32 with shape (3, height, width)
    bboxes - list of tensor of float32 with shape (1, 4) with length nb_bboxes

    return
    - tensor of float32 with shape (nb_bboxes, nb_candidates, 4)
    - list of [[list of str with length nb_candidates]] with length nb_bboxes
    """

    decides = random.random()
    event_index = random.randrange(len(bboxes)) if decides<=0.5 else None
    #if decides<=0.5:
        #logging.info("Icon Reward!")
    return torch.stack(bboxes),\
            [["Event String"] if i==event_index else ["Test String"] for i, _ in enumerate(bboxes)]
    #  }}} function `icon_detector` # 

def icon_recognizer(screen, bboxes):
    #  function `icon_recognizer` {{{ # 
    """
    screen - tensor of float32 with shape (3, height, width)
    bboxes - list of tensor of float32 with shape (1, 4)

    return list of str
    """

    decides = random.random()
    event_index = random.randrange(len(bboxes)) if decides<=0.1 else None
    return ["Event String" if i==event_index else "Test String" for i, _ in enumerate(bboxes)]
    #  }}} function `icon_recognizer` # 

def icon_matcher(screen, targets, bboxes):
    #  function `icon_matcher` {{{ # 
    """
    screen - tensor of float32 with shape (3, height, width)
    targets - list of tensor of float32 with shape (3, height', width') with
      length nb_bboxes
    bboxes - tensor of float32 with shape (nb_bboxes, nb_candidates, 4)

    return list of [[list of bool with length nb_candidates]] with length
      nb_bboxes
    """

    decides = random.random()
    event_index = random.randrange(len(bboxes)) if decides<=0.1 else None
    return [[i==event_index] + [False for _ in bb] for i, bb in enumerate(bboxes)]
    #  }}} function `icon_matcher` # 
