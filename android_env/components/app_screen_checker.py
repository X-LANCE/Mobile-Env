# coding=utf-8
# vim: set tabstop=2 shiftwidth=2:
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
# 
# Revised by Danyang Zhang @X-Lance based on
# 
# Copyright 2021 DeepMind Technologies Limited.
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

"""Determines if the current app screen matches an expected app screen."""

import enum
import re
from typing import Callable, Optional, Sequence
from typing import List, Pattern, Tuple

from absl import logging

from android_env.components import adb_controller as adb_control
from android_env.proto import task_pb2

import lxml.etree

class DumpsysNode():
  """A node in a dumpsys tree."""

  def __init__(self, data: Optional[str] = None):
    self._children = []
    self._data = data

  @property
  def data(self) -> str:
    return self._data

  @property
  def children(self) -> List['DumpsysNode']:
    return self._children

  def find_child(self,
                 predicate: Callable[['DumpsysNode'], bool],
                 max_levels: int = 0) -> Optional['DumpsysNode']:
    """Returns the first direct child that matches `predicate`, None otherwise.

    Args:
      predicate: Function-like that accepts a DumpsysNode and returns boolean.
      max_levels: Maximum number of levels down the tree to search for a child.
        If non-positive, only direct children will be searched for.

    Returns:
      A DumpsysNode or None.
    """
    if not self.children:
      return None

    try:
      return next(x for x in self.children if predicate(x))
    except StopIteration:
      logging.info('Failed to find child. max_levels: %i.', max_levels)
      # Search children.
      if max_levels:
        for child in self.children:
          child_result = child.find_child(predicate, max_levels - 1)
          if child_result is not None:
            return child_result

      return None

  def __repr__(self):
    return self._data

  def print_tree(self, indent: int = 2):
    """Prints this tree in logging.info()."""
    logging.info(' ' * indent + self.data)
    for c in self.children:
      c.print_tree(indent + 2)


def build_tree_from_dumpsys_output(dumpsys_output: str) -> DumpsysNode:
  """Constructs a tree from a dumpsys string output.

  Args:
    dumpsys_output: string Verbatim output from adb dumpsys. The expected format
      is a list where each line is a node and the indentation marks the
      relationship with its parent or sibling.

  Returns:
    DumpsysNode The root of the tree.
  """
  lines = dumpsys_output.split('\n')  # Split by lines.
  lines = [x.rstrip(' \r') for x in lines]
  lines = [x for x in lines if len(x)]  # Remove empty lines.

  root = DumpsysNode('___root___')  # The root of all nodes.
  parents_stack = [root]
  for line in lines:
    stripped_line = line.lstrip(' ')
    indent = len(line) - len(stripped_line)  # Number of indent spaces.
    new_node = DumpsysNode(stripped_line)  # Create a node without indentation.

    parent = parents_stack.pop()
    if parent.data == '___root___':  # The root is an exception for indentation.
      parent_indent = -2
    else:
      parent_indent = (len(parents_stack) - 1) * 2

    if indent == parent_indent:  # `new_node` is a sibiling.
      parent = parents_stack.pop()
    elif indent < parent_indent:  # Indentation reduced (i.e. a block finished)
      num_levels = (indent // 2) + 1
      parents_stack = parents_stack[:num_levels]
      parent = parents_stack.pop()
    elif indent > parent_indent:  # `new_node` is a child.
      pass  # No need to change the current parent.

    parent.children.append(new_node)
    parents_stack.append(parent)
    parents_stack.append(new_node)

  return root


def matches_path(dumpsys_activity_output: str,
                 expected_view_hierarchy_path: Sequence[Pattern[str]],
                 max_levels: int = 0) -> bool:
  """Returns True if the current dumpsys output matches the expected path.

  Args:
    dumpsys_activity_output: The output of running `dumpsys activity ...`.
    expected_view_hierarchy_path: [regex] A list of regular expressions to be
      tested at each level of the tree.
    max_levels: How many levels to search from root for View Hierarchy.

  Returns:
    True if the dumpsys tree contains one path that matches all regexes.
  """
  root = build_tree_from_dumpsys_output(dumpsys_activity_output)

  # Find the View Hierarchy.
  view_hierarchy = root.find_child(
      lambda x: x.data.startswith('View Hierarchy'), max_levels)
  if view_hierarchy is None:
    logging.error(
        'view_hierarchy is None. Dumpsys activity output: %s. tree: %r',
        str(dumpsys_activity_output), root.print_tree())
    logging.error('Tree root: %s', str(root))
    return None

  current_node = view_hierarchy
  for i, regex in enumerate(expected_view_hierarchy_path):

    def regex_predicate(node, expr=regex):
      matches = expr.match(node.data)
      return matches is not None

    child = current_node.find_child(regex_predicate)
    if child is None:
      logging.error('Mismatched regex (%i, %s). current_node: %s', i,
                    regex.pattern, current_node)
      logging.error('Dumpsys activity output: %s', str(dumpsys_activity_output))
      logging.error('Tree root: %s', str(root))
      return None
    else:
      current_node = child
  return True

def find_children(node: lxml.etree.Element,
    class_regex: str, id_regex: str) -> List[lxml.etree.Element]:
  #  function `find_children` {{{ # 
  """
  node - lxml.etree.Element
  class_regex - str
  id_regex - str

  return list of lxml.etree.Element
  """

  children = []
  for ch in node.iterdescendants():
    #if class_regex.match(ch.get("class")) is not None and\
        #id_regex.match(ch.get("resource-id")) is not None:
    if class_regex==ch.get("class") and\
        (id_regex=="" or id_regex==ch.get("resource-id")):
      children.append(ch)
  return children
  #  }}} function `find_children` # 

_separator_pattern = re.compile(r"(?<!\\)@")
_fake_separator_pattern = re.compile(r"\\@")
def match_path2(node: lxml.etree.Element, vh_path: List[str])\
    -> Tuple[bool, Optional[lxml.etree.Element]]:
  #  function `match_path2` {{{ # 
  """
  node - lxml.etree.Element
  vh_path - list of str
  
  return
  - bool
  - lxml.etree.Element or None
  """

  if len(vh_path)==0:
    return True, node

  head = vh_path[0]
  tail = vh_path[1:]

  patterns = _separator_pattern.split(head, maxsplit=1)
  class_pattern_str = _fake_separator_pattern.sub("@", patterns[0])
  #class_regex = re.compile(class_regex)
  class_regex = class_pattern_str
  id_pattern_str = _fake_separator_pattern.sub("@", patterns[1]) if len(patterns)>=2\
      else ""
      #else r".*"
  #id_regex = re.compile(id_pattern_str)
  id_regex = id_pattern_str

  matched_children = find_children(node, class_regex, id_regex)
  for ch in matched_children:
    matches, leaf = match_path2(ch, tail)
    if matches:
      return True, leaf
  return False, None
  #  }}} function `match_path2` # 

class AppScreenChecker():
  """Checks that the current app screen matches an expected screen."""

  bbox_regex = re.compile(r"\[(?P<left>\d+),(?P<top>\d+)\]\[(?P<right>\d+),(?P<bottom>\d+)\]")

  class Outcome(enum.IntEnum):
    """Possible return vales from checking the current app screen."""
    # The current app screen matches the expected app screen.
    SUCCESS = 0
    # There's no activity to check.
    EMPTY_EXPECTED_ACTIVITY = 1
    # We were unable to determine the current activity.
    FAILED_ACTIVITY_EXTRACTION = 2
    # The current activity does not match the expected activity.
    UNEXPECTED_ACTIVITY = 3
    # The current view hierarchy does not match the expected view hierarchy.
    UNEXPECTED_VIEW_HIERARCHY = 4

  def __init__(self,
               adb_controller: adb_control.AdbController,
               expected_app_screen: task_pb2.AppScreen):

    self._adb_controller = adb_controller
    self._expected_activity = expected_app_screen.activity
    self._expected_view_hierarchy_path = [
        re.compile(regex) for regex in expected_app_screen.view_hierarchy_path
    ]

    self._event_listeners = [] # zdy

  # Return type is AppScreenChecker.Outcome, but pytype doesn't understand that.
  def matches_current_app_screen(self) -> enum.IntEnum:
    """Determines whether the current app screen matches `expected_app_screen`."""
    if not self._expected_activity:
      return AppScreenChecker.Outcome.EMPTY_EXPECTED_ACTIVITY

    # Check if we are still on the expected Activity.
    current_activity = self._adb_controller.get_current_activity()
    if current_activity is None:
      return AppScreenChecker.Outcome.FAILED_ACTIVITY_EXTRACTION

    if current_activity != self._expected_activity:
      logging.error('current_activity: %s,  expected_activity: %s',
                    current_activity, self._expected_activity)
      return AppScreenChecker.Outcome.UNEXPECTED_ACTIVITY

    # Extract just the package name from the full activity name.
    package_name = self._expected_activity.split('/')[0]

    # Check if we are in the expected view hierarchy path.
    if self._expected_view_hierarchy_path:
      dumpsys_activity_output = self._adb_controller.get_activity_dumpsys(
          package_name)
      if dumpsys_activity_output:
        if not matches_path(
            dumpsys_activity_output,
            self._expected_view_hierarchy_path,
            max_levels=3):
          return AppScreenChecker.Outcome.UNEXPECTED_VIEW_HIERARCHY

    return AppScreenChecker.Outcome.SUCCESS

  #  For VH Events Listening {{{ # 
  def add_event_listeners(self, *event_listeners):
    #  method `add_event_listeners` {{{ # 
    """
    event_listeners - list of event_listeners.ViewHierarchyEvent
    """

    self._event_listeners += event_listeners
    #  }}} method `add_event_listeners` # 

  def match_events(self, lock):
    #  method `match_events` {{{ # 
    """
    lock - threading.Lock
    """

    view_hierarchy = self._adb_controller.get_view_hierarchy()
    if view_hierarchy is None:
      return

    for evnt in self._event_listeners:
      # 1. match the path
      #matches, leaf_node = match_path2(view_hierarchy, evnt.path)
      #if not matches:
        #continue
      leaf_nodes: List[lxml.etree.Element] = evnt.selector(view_hierarchy)
      if len(leaf_nodes)==0:
        continue

      # 2. match the property value
      for l in leaf_nodes:
        values = []
        for prpt in evnt.property_names:
          if prpt in ["left", "top", "right", "bottom"]:
            matches = AppScreenChecker.bbox_regex.fullmatch(l.get("bounds"))
            normalization = self._adb_controller.get_screen_dimensions()[1]\
                if prpt[0]=="l" or prpt[0]=="r"\
                else self._adb_controller.get_screen_dimensions()[0]
            values.append(float(matches[prpt])/normalization)
          else:
            values.append(l.get(prpt))
        with lock:
          evnt.set(values)
    #  }}} method `match_events` # 
  #  }}} For VH Events Listening # 
