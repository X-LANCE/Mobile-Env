# Copyright 2025 SJTU X-Lance Lab
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
# Created by Danyang Zhang @X-Lance

from typing import Union, Callable, Literal, Any
from typing import Dict, List, Tuple
import numpy as np
from lxml.etree import _Element
from lxml.html import HtmlElement
import lxml.html
import lxml.etree
from android_env.wrappers.vh_io_wrapper import filter_elements
from android_env.wrappers import VhIoWrapper, TapActionWrapper
from enum import IntEnum
import ast

import logging

logger = logging.getLogger("mobile_env.agents.utils")

_vh_env_action_mapping = { "INPUT": (VhIoWrapper.ActionType.INPUT, "element_id", "text")
                         , "CLICK": (VhIoWrapper.ActionType.CLICK, "element_id")
                         , "LONGCLICK": (VhIoWrapper.ActionType.LONGCLICK, "element_id")
                         , "LONG_CLICK": (VhIoWrapper.ActionType.LONGCLICK, "element_id")
                         , "SCROLL": (VhIoWrapper.ActionType.SCROLL, ("direction", VhIoWrapper.ScrollDirection.__getitem__))
                         , "ANSWER": (VhIoWrapper.ActionType.NOTHING, "response")
                         , "GOBACK": (VhIoWrapper.ActionType.GOBACK,)
                         , "DO_NOTHING": (VhIoWrapper.ActionType.NOTHING,)
                         , "NOTHING": (VhIoWrapper.ActionType.NOTHING,)
                         }
_tap_env_action_mapping = { "TYPE": (TapActionWrapper.ActionType.TYPE, "text")
                          , "CLICK": (TapActionWrapper.ActionType.TAP, "touch_position") # touch_position is a tuple of two floats in [0, 1]
                          , "LONGCLICK": (TapActionWrapper.ActionType.LONGTAP, "touch_position")
                          , "LONG_CLICK": (TapActionWrapper.ActionType.LONGTAP, "touch_position")
                          , "TAP": (TapActionWrapper.ActionType.TAP, "touch_position")
                          , "LONGTAP": (TapActionWrapper.ActionType.LONGTAP, "touch_position")
                          , "LONG_TAP": (TapActionWrapper.ActionType.LONGTAP, "touch_position")
                          , "SLIDE": (TapActionWrapper.ActionType.SCROLL, "start_position", "end_position")
                          , "ANSWER": (TapActionWrapper.ActionType.NOTHING, "response")
                          , "GOBACK": (TapActionWrapper.ActionType.GOBACK,)
                          , "DO_NOTHING": (TapActionWrapper.ActionType.NOTHING,)
                          , "NOTHING": (TapActionWrapper.ActionType.NOTHING,)
                          }
def parse_vh_vlm_action_from_action_markup( response: str
                                          , parse_for: Literal["text", "vh_env", "tap_env"] = "text"
                                          ) -> Union[str, Dict[str, np.ndarray]]:
    #  function parse_vh_vlm_action_from_action_markup {{{ # 
    """
    This function extracts action representation from "<action>...</action>"
    structure. If `parse_for` is "vh_env" or "tap_env", this function will
    further parse the extracted action str into the dict format used for
    `VhIoWrapper` and `TapActionWrapper`. The action to parse is expected to
    have the format of Python function call. Supported function names and
    parameters are configured through `_vh_env_action_mapping` and
    `_tap_env_action_mapping`.

    Args:
        response (str): raw response str
        parse_for (str): "text" | "vh_env" | "tap_env". "text" will return the
          raw extracted action str. "vh_env" will further parse the action str
          into the dict format for VhIoWrapper. "tap_env" will parse the action
          str into the dict format of TapActionWrapper.

    Returns:
        Union[str, Dict[str, np.ndarray]]: the extracted or parsed action
    """

    try:
        action_beginning: int = response.index("<action>")+8
        action_end: int = response.find("</action>", action_beginning)
        if action_end==-1:
            action_end = None
        action_str: str = response[action_beginning:action_end].strip()
    except ValueError:
        logger.exception("Cannot find action markups in the given response: %s", response)
        action_str = "DO_NOTHING()"

    if parse_for=="text":
        return action_str

    mapping_dict: Dict[str, Tuple[IntEnum, Union[str, Tuple[str, Callable[[Any], Any]]], ...]]
    if parse_for=="vh_env":
        mapping_dict = _vh_env_action_mapping
    elif parse_for=="tap_env":
        mapping_dict =_tap_env_action_mapping
    else:
        raise NotImplementedError("Not Implemented Action Parsing Mode: {:}".format(parse_for))

    try:
        action_call: ast.Call = ast.parse(action_str, mode="eval").body
        function_name: str = action_call.func.id
    except (SyntaxError, AttributeError):
        logger.exception("Action parsing error `%s`", action_str)
        return {"action_type": np.array(mapping_dict["NOTHING"][0])}
    if function_name not in mapping_dict:
        logger.error("Unknown action str: %s", action_str)
        return {"action_type": np.array(mapping_dict["NOTHING"][0])}
    mapping_tuple: Tuple[IntEnum, Union[str, Tuple[str, Callable[[Any], Any]]], ...]\
            = mapping_dict[function_name]
    action_object: Dict[str, np.ndarray] = {"action_type": np.array(mapping_tuple[0])}
    try:
        for i in range(1, len(mapping_tuple)):
            if isinstance(mapping_tuple[i], str):
                item_name: str = mapping_tuple[i]
                item_cast: Callable[[Any], Any] = lambda x: x
            else:
                item_name: str = mapping_tuple[i][0]
                item_cast: Callable[[Any], Any] = mapping_tuple[i][1]
            action_object[item_name] = np.array(item_cast(action_call.args[i].value))
    except IndexError:
        logger.exception("Action arguments parsing error: %s", action_str)
        return {"action_type": np.array(mapping_dict["NOTHING"][0])}
    return action_object
    #  }}} function parse_vh_vlm_action_from_action_markup # 

_vh_action_serialization_mapping =\
        { VhIoWrapper.ActionType.INPUT: ("INPUT", "element_id", "text")
        , VhIoWrapper.ActionType.CLICK: ("CLICK", "element_id")
        , VhIoWrapper.ActionType.LONGCLICK: ("LONG_CLICK", "element_id")
        , VhIoWrapper.ActionType.SCROLL: ("SCROLL", ("direction", lambda drct: repr(VhIoWrapper.ScrollDirection(drct).name)))
        , VhIoWrapper.ActionType.NOTHING: ("ANSWER", "response")
        , VhIoWrapper.ActionType.GOBACK: ("GOBACK",)
        , VhIoWrapper.ActionType.NOTHING: ("DO_NOTHING",)
        }
_tap_action_serilization_mapping = \
        { TapActionWrapper.ActionType.TYPE: ("TYPE", "text")
        , TapActionWrapper.ActionType.TAP: ("TAP", "touch_position")
        , TapActionWrapper.ActionType.LONGTAP: ("LONG_TAP", "touch_position")
        , TapActionWrapper.ActionType.SCROLL: ("SLIDE", "start_position", "end_position")
        , TapActionWrapper.ActionType.NOTHING: ("ANSWER", "response")
        , TapActionWrapper.ActionType.GOBACK: ("GOBACK",)
        , TapActionWrapper.ActionType.NOTHING: ("DO_NOTHING",)
        }
def convert_action_object_to_history(action_object: Dict[str, np.ndarray], action_for: Literal["vh_env", "tap_env"]) -> str:
    #  function convert_action_object_to_history {{{ # 
    mapping_dict: Dict[int, Tuple[str, Union[str, Tuple[str, Dict[[Any], str]]], ...]]
    if action_for=="vh_env":
        mapping_dict = _vh_action_serialization_mapping
    elif action_for=="tap_env":
        mapping_dict = _tap_action_serilization_mapping
    else:
        raise NotImplementedError("Not Implemented Action Type: {:}".format(action_for))

    action_type: int = action_object["action_type"].item()
    if action_type not in mapping_dict:
        logger.error("Unknown action type: %d for %s", action_type, action_for)
        return "DO_NOTHING()"
    mapping_tuple: Tuple[str, Union[str, Tuple[str, Dict[[Any], str]]], ...] = mapping_dict[action_type]
    function_name: str = mapping_tuple[0]
    arguments: List[str] = []
    try:
        for i in range(1, len(mapping_tuple)):
            if isinstance(mapping_tuple[i], str):
                item_name: str = mapping_tuple[i]
                item_cast: Callable[[Any], str] = repr
            else:
                item_name: str = mapping_tuple[i][0]
                item_cast: Callable[[Any], str] = mapping_tuple[i][1]
            arguments.append(item_cast(action_object[item_name].item()))
    except KeyError:
        logger.exception("Action arguments parsing error: %s for %s", item_name, str(action_for))
        return "DO_NOTHING()"
    return "{:}({:})".format(function_name, ", ".join(arguments))
    #  }}} function convert_action_object_to_history # 

def convert_vh_node_to_html(node: _Element) -> HtmlElement:
    #  function convert_vh_node_to_html {{{ # 
    """
    Converts one leaf node in android view hierarchy to html element. Will
    convert the class, text, resource-id, and content-desc properties.

    Args:
        node (lxml.etree.Element): leaf node from an android view hierarchy

    Returns:
        lxml.html.Element: the converted html element. usually is p, button,
          img, input, or div.
    """

    attribute_dict: Dict[str, str] = {}

    # convert resource-id
    resource_id: str = node.get("resource-id")
    if len(resource_id)>0:
        resource_identifyers = resource_id.rsplit("/", maxsplit=1)
        #assert len(resource_identifyers)==2
        attribute_dict["class"] = " ".join(resource_identifyers[-1].split("_"))

    # convert content-desc
    content_desc: str = node.get("content-desc")
    if len(content_desc)>0:
        attribute_dict["alt"] = content_desc

    # convert text
    text: str = node.get("text")

    # convert class
    vh_class_name: str = node.get("class")
    if vh_class_name.endswith("TextView"):
        html_element = lxml.html.Element( "p"
                                        , attribute_dict
                                        )
        if len(text)>0:
            html_element.text = text
    elif vh_class_name.endswith("Button")\
            or vh_class_name.endswith("MenuItemView"):
        html_element = lxml.html.Element( "button"
                                        , attribute_dict
                                        )
        if len(text)>0:
            html_element.text = text
    elif vh_class_name.endswith("ImageView")\
            or vh_class_name.endswith("IconView")\
            or vh_class_name.endswith("Image"):
        if len(text)>0:
            if "alt" in attribute_dict:
                attribute_dict["alt"] += ": " + text
            else:
                attribute_dict["alt"] = text
        html_element = lxml.html.Element( "img"
                                        , attribute_dict
                                        )
    elif vh_class_name.endswith("EditText"):
        if len(text)>0:
            attribute_dict["value"] = text
        attribute_dict["type"] = "text"
        html_element = lxml.html.Element( "input"
                                        , attribute_dict
                                        )
    else:
        html_element = lxml.html.Element( "div"
                                        , attribute_dict
                                        )
        if len(text)>0:
            html_element.text = text

    return html_element
    #  }}} function convert_vh_node_to_html # 

def escape_newlines_to_html(html: str) -> str:
    return html.strip().replace("\n", "&#10;").replace("\r", "&#13;")

def convert_vh_to_html_list(node: _Element) -> str:
    #  function convert_vh_to_html_list {{{ # 
    """
    Args:
        node (_Element): the VH tree to convert

    Returns:
        str: converted HTML list, one element on one line
    """

    node_list: List[_Element] = filter_elements(node)[0]
    result_list: List[str] = []

    annotate_id: Callable[[HtmlElement, int], None] = lambda elm, i: elm.set("id", str(i))
    def annotate_clickable(elm: HtmlElement, n: _Element):
        elm.set("clickable", n.get("clickable"))
        elm.set("long-clickable", n.get("long-clickable"))

    for i, n in enumerate(node_list):
        html_element: lxml.html.Element = convert_vh_node_to_html(n)
        annotate_id(html_element, i)
        annotate_clickable(html_element, n)
        result_list.append(escape_newlines_to_html(lxml.html.tostring(html_element, pretty_print=True, encoding="unicode")))

    return "\n".join(result_list)
    #  }}} function convert_vh_to_html_list # 
