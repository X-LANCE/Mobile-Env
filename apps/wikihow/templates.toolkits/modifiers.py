def regex_list(x: str) -> str:
    return "(" + "|".join(x.split(",")) + ")"

def regex_esc(x: str) -> str:
    return x.replace("+", r"\\+")

def url_space(x: str) -> str:
    return x.replace(" ", "+")

def url_title(x: str) -> str:
    return x.replace(" ", "-")

def to_list(x: str) -> str:
    return "["\
            + ",".join(
                map(lambda s: "\"{:}\"".format(s),
                    x.split(",")))\
            + "]"

lower = str.lower
upper = str.upper
title = str.title

def filter_comma(x: str) -> str:
    return x.replace(",", "")
