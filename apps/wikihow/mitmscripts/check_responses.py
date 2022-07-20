#!/usr/bin/python3

import os
import os.path

import re
import functools
import datetime

flows = os.listdir("pages/test-mitmproxy")
canonical_response = None
canonical_robots_tag = None
timer_pattern = re.compile(rb"S(\d+\.\d+),VS0,VE[01]")
c_pattern = re.compile(rb"cache-([a-z]+)[-a-z0-9]+-(?i:\1),M")
x_c_set = set()
for fl in flows:
    if fl.startswith("%2fx%2f") or fl.startswith("%2fev%2f"):
        with open(os.path.join("pages/test-mitmproxy/", fl), "rb") as f:
            response = f.read()
        header_bytes, _, content = response.partition(b"\r\n\r\n")
        header_items = header_bytes.split(b"\r\n")
        status_code = int(header_items[0].split()[1].strip())
        header = {k.decode(): val for k, val in
                map(functools.partial(bytes.split, sep=b": ", maxsplit=1),
                    header_items[1:])}

        if status_code!=204:
            print("\x1b[31m{:}\x1b[0m".format(fl))
            print("status code={:}".format(status_code))

        if "x-robots-tag" in header:
            x_robots_tag = header.pop("x-robots-tag")
            if not (fl.startswith("%2fx%2fcollect?t=first&") or\
                    fl.startswith("%2fx%2fcollect?t=later&") or\
                    fl.startswith("%2fev%2f")):
                print(fl)
            if canonical_robots_tag is None:
                canonical_robots_tag = x_robots_tag
                print("canonical-robots-tag={:}".format(canonical_robots_tag))
            else:
                if x_robots_tag!=canonical_robots_tag:
                    print("\x1b[31m{:}\x1b[0m".format(fl))
                    print("x-robots-tag={:}".format(x_robots_tag))

        if "x-timer" not in header:
            print("\x1b[31m{:}\x1b[0m".format(fl))
            print("No x-timer")
        else:
            x_timer = header.pop("x-timer")
            match_ = timer_pattern.fullmatch(x_timer)
            if match_ is None:
                print("\x1b[31m{:}\x1b[0m".format(fl))
                print("x-timer={:}".format(x_timer))
            else:
                date = datetime.datetime.strptime(header.pop("date").decode(), "%a, %d %b %Y %X GMT")
                date_ = datetime.datetime.utcfromtimestamp(float(match_.group(1)))

        if "x-c" not in header:
            print("\x1b[31m{:}\x1b[0m".format(fl))
            print("No x-c")
        else:
            x_c = header.pop("x-c")
            if c_pattern.fullmatch(x_c) is None:
                print("\x1b[31m{:}\x1b[0m".format(fl))
                print("x-c={:}".format(x_c))
            x_c_set.add(x_c)

        content_type = header.pop("content-type")
        #if fl.startswith("%2fx%2famp-view?"):
            #if content_type!="text/html; charset=UTF-8":
                #print("\x1b[31m{:}\x1b[0m".format(fl))
                #print("content-type={:}".format(content_type))
        #else:
            #if content_type!="text/plain; charset=UTF-8":
                #print("\x1b[31m{:}\x1b[0m".format(fl))
                #print("content-type={:}".format(content_type))

        if canonical_response is None:
            canonical_response = header
            print("canonical-header={:}".format(canonical_response))
        else:
            if header!=canonical_response:
                print("\x1b[31m{:}\x1b[0m".format(fl))
                print("header={:}".format(header))

        if len(content)>0:
            print("\x1b[31m{:}\x1b[0m".format(fl))
            print("content={:}".format(content))

#print("\x1b[33mX-C\x1b[0m")
#for x_c in sorted(x_c_set):
    #print(x_c)
