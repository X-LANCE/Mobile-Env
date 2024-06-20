#!/usr/bin/python3

#import lxml.cssselect as lcss
import lxml.etree
from lxml.etree import Element, ElementTree

from typing import List, Pattern, Match, Dict

import re

_css_quick_pattern: Pattern[str] = re.compile(r'(?P<type>[#.$@])(?P<oprt>[$^*]?)(?P<val>"[^"]+"|\d+)')
_css_quick_type: Dict[str, str] = { "#": "resource-id"
                                  , ".": "class"
                                  , "$": "package"
                                  , "@": "index"
                                  }
def _css_quick_replace(me_selector: Match[str]) -> str:
    #  function _css_quick_replace {{{ # 
    value: str = me_selector.group("val")
    if value.isdigit():
        value = "\"" + value + "\""
    return '[{:}{:}={:}]'.format( _css_quick_type[me_selector.group("type")]
                                  , me_selector.group("oprt")
                                  , value
                                  )
    #  }}} function _css_quick_replace # 
def transform_selector(me_selector: str) -> str:
    #  function transform_selector {{{ # 
    """
    Transforms Mobile-Env-customized CSS selector into standard CSS selector.
    The syntax is defined as follows:

    * #"com.wikihow.wikihowapp:id/search_src_text" -> [resource-id="com.wikihow.wikihowapp:id/search_src_text"]
    * #$"search_src_text" -> [resource-id$=search_src_text]
    * ."android.widget.EditText" -> [class="android.widget.EditText"]
    * .$"EditText" -> [class$=EditText]
    * $"com.wikihow.wikihowapp" -> [package="com.wikihow.wikihowapp"]
    * @2 -> [index="2"], somewhat the same as :nth-child(3) (index attribute starts from 0)

    Args:
        me_selector (str): Mobile-Env-customized CSS selector

    Returns:
        str: transformed standard CSS selector
    """

    return _css_quick_pattern.sub(_css_quick_replace, me_selector)
    #  }}} function transform_selector # 

tree: ElementTree = lxml.etree.parse("../../llm-on-android/llmdemo-vh/do_ruby_rose_hair-0/step_13.view_hierarchy")
root: Element = tree.getroot()

#nodes: List[Element] = root.cssselect("[resource-id=\"com.wikihow.wikihowapp:id/search_src_text\"]")
pattern: str = transform_selector('#"com.wikihow.wikihowapp:id/search_src_text"')
print(pattern)
pattern: str = transform_selector('#$"search_src_text"[text~="rose"].$"EditText"')
print(pattern)
pattern: str = transform_selector('#$"search_src_text"$"com.wikihow.wikihowapp"')
print(pattern)
pattern: str = transform_selector('$"com.wikihow.wikihowapp"')
print(pattern)
pattern: str = transform_selector('#$"search_plate">.$"ImageView"@1')
print(pattern)
pattern: str = transform_selector('#$"search_plate">.$"ImageView":nth-child(2)')
print(pattern)
pattern: str = transform_selector('#$"search_src_text", #$"search_plate">.$"ImageView":last-child')
print(pattern)
nodes: List[Element] = root.cssselect(pattern)
for n in nodes:
    #n.set("text", "Do \"ruby\" rose 'hair'")
    print(lxml.etree.tostring(n, encoding="unicode", pretty_print=True))
