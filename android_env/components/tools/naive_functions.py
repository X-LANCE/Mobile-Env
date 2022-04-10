import random
import torch

from absl import logging

def naive_text_detector(screen, bboxes):
    #  function `naive_text_detector` {{{ # 
    """
    screen - tensor of float32 with shape (3, height, width)
    bboxes - list of tensor of float32 with shape (1, 4)

    return list of list of str
    """

    decides = random.random()
    event_index = random.randrange(len(bboxes)) if decides<=0.1 else None
    return [["Event String"] if i==event_index else ["Test String"] for i, _ in enumerate(bboxes)]
    #  }}} function `naive_text_detector` # 

def naive_text_recognizer(screen, bboxes):
    #  function `naive_text_recognizer` {{{ # 
    """
    screen - tensor of float32 with shape (3, height, width)
    bboxes - list of tensor of float32 with shape (1, 4)

    return list of str
    """

    decides = random.random()
    event_index = random.randrange(len(bboxes)) if decides<=0.2 else None
    if decides<=0.2:
        logging.info("Text Reward!")
    return ["Event String" if i==event_index else "Test String" for i, _ in enumerate(bboxes)]
    #  }}} function `naive_text_recognizer` # 

def naive_icon_detector(screen, bboxes):
    #  function `naive_icon_detector` {{{ # 
    """
    screen - tensor of float32 with shape (3, height, width)
    bboxes - list of tensor of float32 with shape (1, 4) with length nb_bboxes

    return
    - tensor of float32 with shape (nb_bboxes, nb_candidates, 4)
    - list of [[list of str with length nb_candidates]] with length nb_bboxes
    """

    decides = random.random()
    event_index = random.randrange(len(bboxes)) if decides<=0.5 else None
    if decides<=0.5:
        logging.info("Icon Reward!")
    return torch.stack(bboxes),\
            [["Event String"] if i==event_index else ["Test String"] for i, _ in enumerate(bboxes)]
    #  }}} function `naive_icon_detector` # 

def naive_icon_recognizer(screen, bboxes):
    #  function `naive_icon_recognizer` {{{ # 
    """
    screen - tensor of float32 with shape (3, height, width)
    bboxes - list of tensor of float32 with shape (1, 4)

    return list of str
    """

    decides = random.random()
    event_index = random.randrange(len(bboxes)) if decides<=0.1 else None
    return ["Event String" if i==event_index else "Test String" for i, _ in enumerate(bboxes)]
    #  }}} function `naive_icon_recognizer` # 

def naive_icon_matcher(screen, targets, bboxes):
    #  function `naive_icon_matcher` {{{ # 
    """
    screen - tensor of float32 with shape (3, height, width)
    targets - list of tensor of float32 with shape (3, height', width') with
      length nb_bboxes
    bboxes - tensor of float32 with shape(nb_bboxes, nb_candidates, 4)

    return list of [[list of bool with length nb_candidates]] with length
      nb_bboxes
    """

    decides = random.random()
    event_index = random.randrange(len(bboxes)) if decides<=0.1 else None
    return [i==event_index for i, _ in enumerate(bboxes)]
    #  }}} function `naive_icon_matcher` # 
