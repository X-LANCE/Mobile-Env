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
import threading
from typing import List, Pattern, Match, Tuple
from typing import ClassVar, cast, Optional
from android_env.components.event_listeners import ViewHierarchyEvent
from lxml.etree import Element, _Element
import re
from android_env.components.adb_controller import AdbController

class ViewHierarchyAnalyzerThread(thread_function.ThreadFunction):
    #  class ViewHierarchyAnalyzerThread {{{ # 
    bbox_regex: ClassVar[Pattern[str]] =\
            re.compile(r"\[(?P<left>\d+),(?P<top>\d+)\]\[(?P<right>\d+),(?P<bottom>\d+)\]")

    class Signal(enum.IntEnum):
        #  enum `Signal` {{{ # 
        CHECK_VH_EVENT = 0
        DID_NOT_CHECK = 1
        CHECK_ERROR = 2
        OK = 4
        #  }}} enum `Signal` # 

    def __init__( self
                , adb_controller: AdbController
                , lock: threading.Lock
                , block_input: bool
                , block_output: bool
                , name: str = "vh_analyzer"
                ):
        #  function __init__ {{{ # 
        """
        Args:
            adb_controller (AdbController): backup controller if no vh is
              provided from the main thread
            lock (threading.Lock): lock to prevent collision
            block_input (bool): controls if _read_value should block
            block_output (bool): controls if _write_value should block
            name (str): thread name
        """

        self._event_listeners: List[ViewHierarchyEvent] = []
        self._adb_controller: AdbController = adb_controller

        self._lock: threading.Lock = lock
        super(ViewHierarchyAnalyzerThread, self).__init__(block_input, block_output, name)
        #  }}} function __init__ # 

    def add_event_listeners(self, *event_listeners: List[ViewHierarchyEvent]):
        self._event_listeners += event_listeners

    def match_events(self, view_hierarchy: Element, screen_dimension: Tuple[int, int]):
        #  method match_events {{{ # 
        """
        Args:
            view_hierarchy (Element): view hierarchy to analyze
            screen_dimension (Tuple[int, int]): screen dimension as (height, width)
        """

        #view_hierarchy = self._adb_controller.get_view_hierarchy()
        #if view_hierarchy is None:
          #return

        for evnt in self._event_listeners:
            # 1. match the path
            #matches, leaf_node = match_path2(view_hierarchy, evnt.path)
            #if not matches:
              #continue
            leaf_nodes: List[Element] = evnt.selector(view_hierarchy)
            if len(leaf_nodes)==0:
                continue

            # 2. match the property value
            for l in leaf_nodes:
                values = []
                for prpt in evnt.property_names:
                    if prpt in ["left", "top", "right", "bottom"]:
                        matches: Match[str] = ViewHierarchyAnalyzerThread.bbox_regex.fullmatch(l.get("bounds"))
                        normalization = screen_dimension[1]\
                                if prpt[0]=="l" or prpt[0]=="r"\
                              else screen_dimension[0]
                        values.append(float(matches[prpt])/normalization)
                    else:
                        values.append(l.get(prpt))
                with self._lock:
                    evnt.set(values)
        #  }}} method match_events # 

    def main(self):
        #  method main {{{ # 
        command = self._read_value()
        if command!=ViewHierarchyAnalyzerThread.Signal.CHECK_VH_EVENT:
            self._write_value(ViewHierarchyAnalyzerThread.Signal.DID_NOT_CHECK)
            return

        view_hierarchy: Optional[Element] = self._read_value()
        if view_hierarchy is None:
            view_hierarchy = self._adb_controller.get_view_hierarchy()
        if not isinstance(view_hierarchy, _Element):
            self._write_value(ViewHierarchyAnalyzerThread.Signal.DID_NOT_CHECK)
            return
        view_hierarchy: Element = cast(Element, view_hierarchy)

        screen_dimension: Tuple[int, int] = self._read_value()
        if not isinstance(screen_dimension, tuple):
            self._write_value(ViewHierarchyAnalyzerThread.Signal.DID_NOT_CHECK)
            return

        try:
            self.match_events(view_hierarchy, screen_dimension)
            self._write_value(ViewHierarchyAnalyzerThread.Signal.OK)
        except:
            self._write_value(ViewHierarchyAnalyzerThread.Signal.CHECK_ERROR)
        #  }}} method main # 
    #  }}} class ViewHierarchyAnalyzerThread # 
