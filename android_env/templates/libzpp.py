#!/usr/bin/python3

"""
Composed by Danyang Zhang
Last Revision: Dec 2024
"""

# Test:
# ./zpp -m C test.txt.orig -o output.txt
# ./zpp -m C --def ABC test.txt.orig -o output.txt
# ./zpp -m C --def got=获得 test.txt.orig -o output.txt
# ./zpp -m C --def ABC=321 test.txt.orig -o output.txt
# ./zpp -m C --def 'ABC=/(?<!^)ABC/321/' test.txt.orig -o output.txt
# ./zpp -m C --def 'ABC=/(?<!^)ABC/321/' --def NUM=2 test.txt.orig -o output.txt
# ./zpp -m C --def 'ABC=/(?<!^)ABC/321/' --def NUM=3 test.txt.orig -o output.txt

import argparse
import re
import os.path
import collections

from typing import Iterable, TextIO, Optional, Union
from typing import Dict, Deque, Tuple, Pattern, List
from numbers import Number
import operator

import logging

logger = logging.Logger("zpp")

line_prefix_mark_pattern: Pattern[str] = re.compile(r"(?<!\\)<")
line_suffix_mark_pattern: Pattern[str] = re.compile(r"(?<!\\)>")
line_subs_mark_pattern: Pattern[str] = re.compile(r"(?<!\\)/")
def parse_include_arguments(command_line: str) ->\
        Tuple[ Optional[str], Optional[str]
             , Optional[str], Optional[str]
             , Optional[Tuple[str, str]], str
             ]:
    """
    Args:
        command_line (str): the remaining arguments to parse

    Returns:
        Optional[str]: prefix definition
        Optional[str]: suffix definition
        Optional[str]: line prefix to prepend
        Optional[str]: line suffix to append
        Optional[Tuple[str, str]]: line substitution rule
        str: remaining command line
    """

    if command_line.startswith("-"):
        items = command_line.split(maxsplit=1)
        return items[0][1:], None, None, None, None, items[1]
    if command_line.startswith("+"):
        items = command_line.split(maxsplit=1)
        return None, items[0][1:], None, None, None, items[1]
    if command_line.startswith("<"):
        endposition: int = line_prefix_mark_pattern.search(command_line, 1).end()
        return None, None\
             , command_line[1:endposition-1].replace(r'\<', '<'), None\
             , None, command_line[endposition:].strip()
    if command_line.startswith(">"):
        endposition: int = line_suffix_mark_pattern.search(command_line, 1).end()
        return None, None\
             , None, command_line[1:endposition-1].replace(r'\>', '>')\
             , None, command_line[endposition:].strip()
    if command_line.startswith("/"):
        endposition1: int = line_subs_mark_pattern.search(command_line, 1).end()
        endposition2: int = line_subs_mark_pattern.search(command_line, endposition1).end()
        return None, None, None, None\
             , (command_line[1:endposition1-1].replace(r'\/', '/'), command_line[endposition1:endposition2-1].replace(r'\/', '/'))\
             , command_line[endposition2:].strip()
    return None, None, None, None, None, command_line

def parse_number(number_str: str) -> Union[None, int, float]:
    try:
        number: int = int(number_str)
        return number
    except ValueError:
        pass
    try:
        number: float = float(number_str)
        return number
    except ValueError:
        pass
    logger.warning("%s is neither interger nor float.", number_str)
    return None

def _print_plainline( line: str, macros: Dict[str, Union[str, Tuple[str, str, str]]], line_subs: List[Tuple[str, str]]
                    , line_prefix: str, line_suffix: str
                    ) -> str:
    #  function _print_plainline {{{ # 
    for mcr, mcr_val in macros.items():
        if isinstance(mcr_val, str):
            line = re.sub(r"\b" + mcr + r"\b", mcr_val, line, flags=re.ASCII)
        else:
            # mcr_val[0]: regex
            # mcr_val[1]: substitution
            # mcr_val[2]: regex flags, one letter per flag
            line = re.sub(mcr_val[0], mcr_val[1], line, flags=all(getattr(re, fl) for fl in mcr_val[2]))
    for ptn, sstt in line_subs:
        line = re.sub(ptn, sstt, line)
    return line_prefix + line + line_suffix + "\n"
    #  }}} function _print_plainline # 

_condition_pattern = re.compile(r"(?P<if>if|elif)(?P<not>n?)(?P<rel>def|eqn?|[lg][et])")
def include( input_file: Iterable[str]
           , output_file: TextIO
           , configs: Dict[str, str]
           , states: Dict[str, Dict[str, Union[str, Tuple[str, str, str]]]]
           , if_stack: Deque[Tuple[bool, bool]]
           , modifications: Dict[str, Union[str, List[Tuple[str, str]]]]
           ):
    #  function `include` {{{ # 
    """
    Args:
        input_file: iterable of str
        output_file: object supporting `write` accepting str
        configs: dict like
          {
            "prefix": str,
            "suffix": str,
            "path": str
          }
        states: dict like
          {
            "macros": dict like {str: str, str: (str, str, str)}
          }
        if_stack: collections.deque of (bool, bool)
          - the first item indicates whether the current if-block has been
            matched ever
          - the second item indicates whether the current if-block is matched
            right now
        modifications (Dict[str, Union[str, List[Tuple[str, str]]]]): dict like
          {
            "line_prefix": str
            "line_suffix": str
            "line_subs": list of tuple like (str, str)
          }
    """

    macros = states["macros"]

    prefix = configs["prefix"]
    suffix = configs["suffix"]
    path = configs["path"]

    line_prefix: str = modifications.get("line_prefix", "")
    line_suffix: str = modifications.get("line_suffix", "")
    line_subs: List[Tuple[str, str]] = modifications.get("line_subs", [])

    for l in input_file:
        unstripped_line = l[:-1]
        l = l.strip()
        if l.startswith(prefix) and l.endswith(suffix):
            candidate = l[len(prefix):-len(suffix)] if len(suffix)>0 else l[len(prefix):]
            candidate = candidate.strip()

            command = candidate.split(maxsplit=1)
            if len(command)<1:
                if if_stack[-1][1]:
                    output_file.write(_print_plainline(unstripped_line, macros, line_subs, line_prefix, line_suffix))
            elif command[0]=="define":
                if if_stack[-1][1]:
                    arguments = command[1].split(maxsplit=1)
                    macros[arguments[0]] = arguments[1] if len(arguments)>1 else ""
            elif command[0]=="defineR":
                if if_stack[-1][1]:
                    macro_name: str
                    remaining: str
                    macro_name, remaining = command[1].split(maxsplit=1)
                    endposition1: int = line_subs_mark_pattern.search(remaining, 1).end()
                    endposition2: int = re.search(r'\s', remaining, endposition1).start()
                    regex: str = remaining[1:endposition1-1].replace(r'\/', '/')
                    flags: str = remaining[endposition1:endposition2].strip()
                    replacement: str = remaining[endposition2:].strip()
                    macros[macro_name] = (regex, replacement, flags)
            elif command[0]=="undef":
                if if_stack[-1][1]:
                    if command[1] in macros:
                        del macros[command[1]]

            elif command[0]=="include":
                if if_stack[-1][1]:
                    in_prefix = prefix
                    in_suffix = suffix
                    in_line_prefix = ""
                    in_line_suffix = ""
                    in_line_subs: List[Tuple[str, str]] = []

                    prefix_, suffix_, line_prefix_, line_suffix_, new_line_sub, remaining = parse_include_arguments(command[1])
                    # parse the arguments iteratively
                    while True:
                        if prefix_ is not None:
                            in_prefix = prefix_
                        elif suffix_ is not None:
                            in_suffix = suffix_
                        elif line_prefix_ is not None:
                            in_line_prefix = line_prefix_
                        elif line_suffix_ is not None:
                            in_line_suffix = line_suffix_
                        elif new_line_sub is not None:
                            in_line_subs.append(new_line_sub)
                        else:
                            break

                        prefix_, suffix_, line_prefix_, line_suffix_, new_line_sub, remaining = parse_include_arguments(remaining)

                    if remaining.startswith("#"):
                        include_file: str = remaining.lstrip("#") # use "#" to distinguish an absolute path from the replacement rules
                    else:
                        include_file: str = os.path.join(path, remaining)
                    in_path = os.path.dirname(include_file)

                    with open(include_file) as incl_f:
                        include( incl_f, output_file
                               , configs={ "prefix": in_prefix
                                         , "suffix": in_suffix
                                         , "path": in_path
                                         }
                               , states={"macros": macros}
                               , if_stack=if_stack
                               , modifications={ "line_prefix": line_prefix + in_line_prefix
                                               , "line_suffix": line_suffix + in_line_suffix
                                               , "line_subs": line_subs + in_line_subs
                                               }
                               )

            elif command[0]=="else":
                if_stack[-1][1] = if_stack[-2][1] and not if_stack[-1][0]
                if_stack[-1][0] = if_stack[-2][1]
            elif command[0]=="endif":
                if_stack.pop()
            else:
                match_ = _condition_pattern.match(command[0])
                if match_ is not None:
                    if match_["if"]=="if":
                        if_stack.append([False, False])
                    if if_stack[-1][0]:
                        if_stack[-1][1] = False
                    else:
                        if not if_stack[-2][1]:
                            condition = False
                        else:
                            if match_["rel"]=="def":
                                condition = command[1] in macros
                                mask = True
                            else:
                                macro_name, macro_value = command[1].split(maxsplit=1)
                                mask = macro_name in macros
                                real_value: Union[str, Tuple[str, str, str]] = macros.get(macro_name, "")
                                if isinstance(real_value, tuple):
                                    real_value: str = real_value[1]

                                if match_["rel"]=="eq":
                                    condition = mask and real_value==macro_value
                                else:
                                    ref_number: Optional[Number] = parse_number(macro_value)
                                    real_number: Optional[Number] = parse_number(real_value)
                                    mask = mask and ref_number is not None\
                                                and real_number is not None
                                    if match_["rel"]=="eqn":
                                        condition = mask and real_number==ref_number
                                    else:
                                        condition = mask and getattr(operator, match_["rel"])(real_number, ref_number)

                            if match_["not"]=="n":
                                condition = mask and not condition
                        if_stack[-1] = [condition, condition]
                else:
                    if if_stack[-1][1]:
                        output_file.write(_print_plainline(unstripped_line, macros, line_subs, line_prefix, line_suffix))
        else:
            if if_stack[-1][1]:
                output_file.write(_print_plainline(unstripped_line, macros, line_subs, line_prefix, line_suffix))
    #  }}} function `include` # 

MODE_DICT = {
        "H": {
            "prefix": "<!--",
            "suffix": "-->",
        },
        "T": {
            "prefix": "%",
            "suffix": ""
        },
        "C": {
            "prefix": "#",
            "suffix": ""
        },
        "J": {
            "prefix": "//",
            "suffix": ""
        }
    }

def preprocess( input_file: Iterable[str], output_file: TextIO
              , configs: Dict[str, str]
              , states: Dict[str, Dict[str, Union[str, Tuple[str, str, str]]]]
              ):
    """
    Args:
        input_file (Iterable[str]): input file as line sequence
        output_file (TextIO): output file
        configs (Dict[str, str]): dict like
          {
            "prefix": str,
            "suffix": str,
            "path": str
          }
          configuring the prefix, suffix, and working path
        states (Dict[str, Dict[str, str]): dict like
          {
            "macros": dict like {str: str, str: (str, str, str)}
          }
          defining macros
    """

    if_stack = collections.deque([[True, True]])
    include(input_file, output_file, configs, states, if_stack, {})

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("--prefix", type=str, help="Prefix for preprocessing commands.")
    parser.add_argument("--suffix", type=str, help="Suffix for preprocessing commands.")
    parser.add_argument("--nosuffix", action="store_const", const="", dest="suffix",
        help="No suffices is in need.")
    parser.add_argument("--mode", "-m", default="H", type=str, choices=["H", "T", "C", "J"],
        help="""\
H: HTML Comment Mode, e.g., <!-- include a.js -->
T: TeX Comment Mode, e.g., %% define TeX \\LaTeX
C: C Preprocessing Instruction Mode, e.g., #define A_TOY_PREPROCESSOR
J: Java Comment Mode, e.g., // include class.java""")

    parser.add_argument("--def", action="append", type=str,
        help="Manually define a macro like \"ABC\" or \"ABC=LSP\" or \"ABC=/REGEX/SUB/\", \"=\" in macro name and definitions and \"/\" in definitions could be escaped by \"\\\"",
        dest="macro")

    parser.add_argument("file", type=str, help="Input file.")

    parser.add_argument("--output", "-o", default="/dev/stdout", type=str,
        help="Output file")

    args = parser.parse_args()

    mode_data = MODE_DICT[args.mode]
    prefix = mode_data["prefix"]
    suffix = mode_data["suffix"]

    if args.prefix is not None:
        prefix = args.prefix
    if args.suffix is not None:
        suffix = args.suffix

    definition_separator_pattern = re.compile(r"(?<!\\)=")
    real_equal_mark_pattern = re.compile(r"\\=")

    macros = {}
    if args.macro:
        for mcr in args.macro:
            items = definition_separator_pattern.split(mcr, maxsplit=1)
            macro_name = real_equal_mark_pattern.sub("=", items[0])
            macro_value = real_equal_mark_pattern.sub("=", items[1]) if len(items)>1 else ""

            if macro_value.startswith("/") and macro_value.endswith("/"):
                regex: str
                replacement: str
                regex, replacement = line_subs_mark_pattern.split(macro_value[1:-1], maxsplit=1)
                macro_value: Tuple[str, str, str] = ( regex.replace(r'\/', '/')
                                                    , replacement.replace(r'\/', '/')
                                                    , ""
                                                    )
            else:
                macro_value: str = macro_value.replace(r'\/', '/')
            macros[macro_name] = macro_value

    path = os.path.dirname(args.file)

    if_stack = collections.deque([[True, True]])

    with open(args.file) as in_f,\
            open(args.output, "w") as out_f:
        include( in_f, out_f
               , configs={ "prefix": prefix
                         , "suffix": suffix
                         , "path": path
                         }
               , states={"macros": macros}
               , if_stack=if_stack
               , modifications={}
               )

if __name__ == "__main__":
    main()
