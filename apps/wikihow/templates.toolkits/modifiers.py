import urllib.parse
from typing import Callable

def regex_list(x: str) -> str:
    return "(" + "|".join(x.split(",")) + ")"

def regex_esc(x: str) -> str:
    return x.replace("+", r"\\+")

url_space: Callable[[str], str] = urllib.parse.quote_plus
url_space: Callable[[str], str] = urllib.parse.quote

def url_title(x: str) -> str:
    return urllib.parse.quote(x.replace(" ", "-"))

def to_list(x: str) -> str:
    return "["\
            + ",".join(
                map(lambda s: "\"{:}\"".format(s),
                    x.split(",")))\
            + "]"

lower: Callable[[str], str] = str.lower
upper: Callable[[str], str] = str.upper
title: Callable[[str], str] = str.title

def filter_comma(x: str) -> str:
    return x.replace(",", "")
