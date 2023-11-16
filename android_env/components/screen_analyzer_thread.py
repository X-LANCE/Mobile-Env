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

from android_env.components import thread_function
import enum

#from android_env.proto import emulator_controller_pb2
#from android_env.proto import emulator_controller_pb2_grpc
import numpy as np
import torch
#import torchvision.ops as tvops
import torchvision.io as tvio

from absl import logging
import traceback

from typing import Callable
from typing import List, Tuple
from android_env.components import event_listeners
import threading

# mainly taken from `DumpsysThread`
class ScreenAnalyzerThread(thread_function.ThreadFunction):
    #  class `ScreenAnalyzerThread` {{{ # 
    class Signal(enum.IntEnum):
        #  enum `Signal` {{{ # 
        CHECK_SCREEN = 0
        DID_NOT_CHECK = 1
        CHECK_ERROR = 2
        OK = 4
        #  }}} enum `Signal` # 

    def __init__(self,
            text_detector: Callable[[torch.Tensor, List[torch.Tensor]],
                List[List[str]]],
            text_recognizer: Callable[[torch.Tensor, List[torch.Tensor]],
                List[str]],
            icon_detector: Callable[[torch.Tensor, List[torch.Tensor]],
                Tuple[torch.Tensor, List[List[str]]]],
            icon_recognizer: Callable[[torch.Tensor, List[torch.Tensor]],
                List[str]],
            icon_matcher: Callable[[torch.Tensor, List[torch.Tensor], torch.Tensor],
                List[List[bool]]],
            #emulator_stub, image_format,
            #check_frequency,
            #max_failed_current_activity,
            lock: threading.Lock,
            block_input: bool, block_output: bool, name: str = "screen_analyzer"):
        #  method `__init__` {{{ # 
        """
        text_detector - callable accepting
          + tensor of float32 with shape (3, height, width) as screenshot
          + list of tensor of float32 with shape (1, 4) with length nb_bboxes
          and returning list of [[list of str]] with length nb_bboxes as
          detected texts
        text_recognizer - callable accepting
          + tensor of float32 with shape (3, height, width)
          + list of tensor of float32 with shape (1, 4) with length nb_bboxes
          and returning list of str with length nb_bboxes

        icon_detector - callable accepting
          + tensor of float32 with shape (3, height, width)
          + list of tensor of float32 with shape (1, 4) with length nb_bboxes
          and returning
          + tensor of float32 with shape (nb_bboxes, nb_candidates, 4)
          + list of [[list of str with length nb_candidates]] with length
            nb_bboxes as recognized icon classes
        icon_recognizer - callable accepting
          + tensor of float32 with shape (3, height, width)
          + list of tensor of float32 with shape (1, 4) with length nb_bboxes
          and returning list of str with length nb_bboxes as recognized icon
          class
        icon_matcher - callable accepting
          + tensor of float32 with shape (3, height, width) as the screenshot
          + list of tensor of float32 with shape (3, height', width') with length
            nb_bboxes as the targets
          + tensor of float32 with shape (nb_bboxes, nb_candidates, 4)
          and returning list of [[list of bool with length nb_candidates]] with
          length nb_bboxes

        #emulator_stub - emulator_controller_pb2_grpc.EmulatorControllerStub
        #image_format - emulator_controller_pb2.ImageFormat

        #check_frequency - int
        #max_failed_current_activity - int

        lock - threading.Lock

        block_input - bool
        block_output - bool
        name - str
        """

        self._text_detector: Callable[[torch.Tensor, List[torch.Tensor]],
                List[List[str]]] = text_detector
        self._text_recognizer: Callable[[torch.Tensor, List[torch.Tensor]],
                List[str]] = text_recognizer
        self._icon_detector: Callable[[torch.Tensor, List[torch.Tensor]],
                Tuple[torch.Tensor, List[List[str]]]] = icon_detector
        self._icon_recognizer: Callable[[torch.Tensor, List[torch.Tensor]],
                List[str]] = icon_recognizer
        self._icon_matcher: Callable[[torch.Tensor, List[torch.Tensor], torch.Tensor],
                List[List[bool]]] = icon_matcher

        #self._emulator_stub = emulator_stub
        #self._image_format = image_format

        self._text_recog_event_listeners: List[event_listeners.Event] = []
        self._text_detect_event_listeners: List[event_listeners.Event] = []
        self._icon_recog_event_listeners: List[event_listeners.Event] = []
        self._icon_detect_event_listeners: List[event_listeners.Event] = []
        self._icon_match_event_listeners: List[event_listeners.Event] = []
        self._icon_detect_match_event_listeners: List[event_listeners.Event] = []

        self._lock: threading.Lock = lock

        #self._main_loop_counter = 0
        #self._check_frequency = check_frequency
        #self._max_failed_activity_extraction = max_failed_current_activity
        #self._num_failed_activity_extraction = 0

        super(ScreenAnalyzerThread, self).__init__(block_input, block_output, name)
        #  }}} method `__init__` # 

    #  Methods to Add Event Listeners {{{ # 
    def add_text_event_listeners(self, *event_listeners):
        """
        event_listeners - list of event_listeners.TextEvent
        """

        for lstn in event_listeners:
            if lstn.needs_detection:
                self._text_detect_event_listeners.append(lstn)
            else:
                self._text_recog_event_listeners.append(lstn)

    def add_icon_event_listeners(self, *event_listeners):
        """
        event_listeners - list of event_listeners.IconRecogEvent
        """

        for lstn in event_listeners:
            if lstn.needs_detection:
                self._icon_detect_event_listeners.append(lstn)
            else:
                self._icon_recog_event_listeners.append(lstn)

    def add_icon_match_event_listeners(self, *event_listeners):
        """
        event_listeners - list of event_listeners.IconMatchEvent
        """

        for lstn in event_listeners:
            if lstn.needs_detection:
                self._icon_detect_match_event_listeners.append(lstn)
            else:
                self._icon_match_event_listeners.append(lstn)
    #  }}} Methods to Add Event Listeners # 

    #def get_screenshot(self):
        ##  method `get_screenshot` {{{ # 
        #"""
        #return tensor of float32 with shape (3, height, width)
        #"""
#
        #image_proto = self._emulator_stub.getScreenshot(self._image_format)
        #height = image_proto.format.height
        #width = image_proto.format.width
        #image = np.frombuffer(image_proto.image, dtype=np.uint8, count=height*width*3)
        #image.shape = (height, width, 3)
        #image = np.transpose(image, axes=(2, 0, 1))
        #return torch.tensor(image, dtype=torch.float32)
        ##  }}} method `get_screenshot` # 

    #  Methods to Match Registered Events {{{ # 
    @torch.no_grad()
    def match_text_events(self, screen):
        #  method `match_text_events` {{{ # 
        """
        screen - tensor of float32 with shape (3, height, width)
        """

        _, height, width = screen.shape

        # first, for detection
        bboxes = []
        for lstn in self._text_detect_event_listeners:
            x0, y0, x1, y1 = lstn.region
            bboxes.append(torch.tensor(
                [
                    x0*width,
                    y0*height,
                    x1*width,
                    y1*height
                ])[None, :])
        if len(bboxes)>0:
            #logging.debug("Invoking Detector")
            results = self._text_detector(screen, bboxes)
            #logging.debug("Invoked Detector")
            with self._lock:
                for lstn, rslts in zip(self._text_detect_event_listeners, results):
                    for cddt in rslts:
                        lstn.set(cddt)
                        if lstn.is_set():
                            break

        # then, for pure recognize
        try:
            bboxes = []
            for lstn in self._text_recog_event_listeners:
                x0, y0, x1, y1 = lstn.region
                bboxes.append(torch.tensor(
                    [
                        x0*width,
                        y0*height,
                        x1*width,
                        y1*height
                    ])[None, :])
            if len(bboxes)>0:
                results = self._text_recognizer(screen, bboxes)
                with self._lock:
                    for lstn, rslt in zip(self._text_recog_event_listeners, results):
                        #logging.info("ZDY_DEBUG: {:}".format(type(rslt)))
                        lstn.set(rslt)
        except Exception as e:
            logging.error("Error occurred during text recognition!")
            logging.error(str(e))
            traceback.print_exc()
        #  }}} method `match_text_events` # 

    @torch.no_grad()
    def match_icon_events(self, screen):
        #  method `match_icon_events` {{{ # 
        """
        screen - tensor of float32 with shape (3, height, width)
        """

        _, height, width = screen.shape

        # first, for detection
        try:
            bboxes = []
            for lstn in self._icon_detect_event_listeners:
                x0, y0, x1, y1 = lstn.region
                bboxes.append(torch.tensor(
                    [
                        x0*width,
                        y0*height,
                        x1*width,
                        y1*height
                    ])[None, :])
            if len(bboxes)>0:
                _, results = self._icon_detector(screen, bboxes)
                with self._lock:
                    for lstn, rslts in zip(self._icon_detect_event_listeners, results):
                        for cddt in rslts:
                            lstn.set(cddt)
                            if lstn.is_set():
                                #logging.info("Icon Event Set!")
                                break
        except Exception as e:
            logging.error("Error occurred during icon detection!")
            logging.error(str(e))

        # then, for pure recognize
        try:
            bboxes = []
            for lstn in self._icon_recog_event_listeners:
                x0, y0, x1, y1 = lstn.region
                bboxes.append(torch.tensor(
                    [
                        x0*width,
                        y0*height,
                        x1*width,
                        y1*height
                    ])[None, :])
            if len(bboxes)>0:
                results = self._icon_recognizer(screen, bboxes)
                with self._lock:
                    for lstn, rslt in zip(self._icon_recog_event_listeners, results):
                        lstn.set(rslt)
        except Exception as e:
            logging.error("Error occurred during icon recognition!")
            logging.error(str(e))
        #  }}} method `match_icon_events` # 

    @torch.no_grad()
    def match_icon_match_events(self, screen):
        #  method `match_icon_match_events` {{{ # 
        """
        screen - tensor of float32 with shape (3, height, width)
        """

        _, height, width = screen.shape

        # first, for detection
        bboxes = []
        target_images = []
        for lstn in self._icon_detect_match_event_listeners:
            x0, y0, x1, y1 = lstn.region
            bboxes.append(torch.tensor(
                [
                    x0*width,
                    y0*height,
                    x1*width,
                    y1*height
                ])[None, :])

            image_tensor = tvio.read_image(lstn.path, tvio.ImageReadMode.RGB)
            image_tensor = image_tensor.to(dtype=torch.float32)/255.
            target_images.append(image_tensor)
        if len(bboxes)>0:
            candidate_bboxes, _ = self._icon_detector(screen, bboxes)
            base_bboxes = torch.cat(bboxes)[:, None, :]
            candidate_bboxes[:, :, 0] += base_bboxes[:, :, 0]
            candidate_bboxes[:, :, 2] += base_bboxes[:, :, 0]
            candidate_bboxes[:, :, 1] += base_bboxes[:, :, 1]
            candidate_bboxes[:, :, 3] += base_bboxes[:, :, 1]
            results = self._icon_matcher(screen, target_images, candidate_bboxes)

            with self._lock:
                for lstn, rslts in zip(self._icon_detect_match_event_listeners, results):
                    if any(rslts):
                        lstn.set(True)

        # then, for pure recognize
        bboxes = []
        target_images = []
        for lstn in self._icon_match_event_listeners:
            x0, y0, x1, y1 = lstn.region
            bboxes.append(torch.tensor(
                [
                    x0*width,
                    y0*height,
                    x1*width,
                    y1*height
                ])[None, :])

            image_tensor = tvio.read_image(lstn.path, tvio.ImageReadMode.RGB)
            image_tensor = image_tensor.to(dtype=torch.float32)/255.
            target_images.append(image_tensor)
        if len(bboxes)>0:
            bboxes = torch.cat(bboxes)[:, None, :]
            results = self._icon_matcher(screen, target_images, bboxes)
            with self._lock:
                for lstn, rslt in zip(self._icon_recog_event_listeners, results):
                    lstn.set(rslt[0])
        #  }}} method `match_icon_match_events` # 
    #  }}} Methods to Match Registered Events # 

    def main(self):
        #  method `main` {{{ # 
        command = self._read_value()
        if command!=ScreenAnalyzerThread.Signal.CHECK_SCREEN:
            self._write_value(ScreenAnalyzerThread.Signal.DID_NOT_CHECK)
            return

        screen = self._read_value()
        if not isinstance(screen, np.ndarray):
            self._write_value(ScreenAnalyzerThread.Signal.DID_NOT_CHECK)
            return
        screen = np.clip(screen, 0, 255).astype(np.float32)/255.
        screen = torch.from_numpy(screen)

        #self._main_loop_counter += 1
        #if self._check_frequency<=0 or\
                #self._main_loop_counter < self._check_frequency:
            #self._write_value(ScreenAnalyzerThread.Signal.DID_NOT_CHECK)
            #return
        #self._main_loop_counter = 0


        try:
            #logging.info("Screen Analyzer Tries to Catch Screenshot...")
            #screen = self.get_screenshot()
            #logging.info("Screen Analyzer Caught Screenshot!")

            self.match_text_events(screen)
            self.match_icon_events(screen)
            self.match_icon_match_events(screen)

            self._write_value(ScreenAnalyzerThread.Signal.OK)
        except:
            self._write_value(ScreenAnalyzerThread.Signal.CHECK_ERROR)
        #  }}} method `main` # 
    #  }}} class `ScreenAnalyzerThread` # 
