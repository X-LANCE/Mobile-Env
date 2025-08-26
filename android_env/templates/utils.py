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

from typing import Union, Callable, Literal
from typing import Dict, List
import numpy as np
from lxml.etree import _Element
from lxml.html import HtmlElement
import lxml.html
import lxml.etree
from android_env.wrappers.vh_io_wrapper import filter_elements

def parse_vh_vlm_action_from_action_markup( response: str
                                          , parse_for: Literal["text", "vh_env", "tap_env"] = "text"
                                          ) -> Union[str, Dict[str, np.ndarray]]:
    #  function parse_vh_vlm_action_from_action_markup {{{ # 
    # NOTE: add a special field in actions with element ids for element
    # representations
    # TODO
    pass
    #  }}} function parse_vh_vlm_action_from_action_markup # 

def convert_action_object_to_history(action_object: Dict[str, np.ndarray]) -> str:
    #  function convert_action_object_to_history {{{ # 
    # TODO
    pass
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

def convert_raw_img_to_jpeg_base64(image: np.ndarray) -> str:
    #  function convert_raw_img_to_jpeg_base64 {{{ # 
    # TODO
    pass
    #  }}} function convert_raw_img_to_jpeg_base64 # 
