#!/usr/bin/python3

from mitmproxy import http
from mitmproxy import io

import os.path
import re
import classify_url

dump_path = "../../../../small-web-crawler/dumps"

special_strs = [
        "RCLit",
        "UsageLogs",
        "SpellChecker",
        "SortQuestions",
        "TechFeedback",
        "MobileSpellchecker",
        "MobileCategoryGuardian",
        "CategoryGuardian",
        "UnitGuardian",
        "QuizYourself"
    ]
special_pattern = re.compile(r"^/Special:(?:{:})".format("|".join(special_strs)))

counter = {}

with open("../flows/wikihow-20220826.flow", "rb") as fl_f:
    reader = io.FlowReader(fl_f)
    for fl in reader.stream():
        if isinstance(fl, http.HTTPFlow) and fl.request.pretty_host=="www.wikihow.com":
            url_path = fl.request.path
            url_key = classify_url.classify(url_path)
            if url_key in [ r"/x/collect\?t={first,later}&*"
                          , r"/x/collect\?t={exit,amp}&*"
                          , r"/x/amp-view\?*"
                          , r"/ev/*"
                          ]:
                continue

            dump_name = url_path.replace("/", "%2f")
            if len(dump_name)>100:
                dump_name = dump_name[:100]

            if url_path.startswith("/Special:"):
                match_ = special_pattern.match(url_path)
                if match_ is not None:
                    if url_path not in counter:
                        counter[url_path] = 0
                    dump_name = dump_name + "-{:}".format(counter[url_path])
                    counter[url_path] += 1

            if url_path.startswith("/Special:CommunityDashboard")\
                    or url_path.startswith("/Special:MobileCommunityDashboard"):
                print("Dumped {:}".format(dump_name))
                with open(os.path.join(dump_path, dump_name), "wb") as f:
                    f.write("HTTP/2 {:d}\r\n".format(fl.response.status_code).encode())
                    for k, v in fl.response.headers.items():
                        f.write("{:}: {:}\r\n".format(k, v).encode())
                    f.write(b"\r\n")
                    if fl.response.raw_content is not None:
                        f.write(fl.response.raw_content)
            elif os.path.exists(os.path.join(dump_path, dump_name)):
                print("Exists {:}".format(dump_name))
            else:
                print("Dumped {:}".format(dump_name))
                with open(os.path.join(dump_path, dump_name), "wb") as f:
                    f.write("HTTP/2 {:d}\r\n".format(fl.response.status_code).encode())
                    for k, v in fl.response.headers.items():
                        f.write("{:}: {:}\r\n".format(k, v).encode())
                    f.write(b"\r\n")
                    if fl.response.raw_content is not None:
                        f.write(fl.response.raw_content)
