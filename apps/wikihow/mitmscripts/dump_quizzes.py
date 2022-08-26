#!/usr/bin/python3

from mitmproxy import http
from mitmproxy import io

import os.path
import classify_url

dump_path = "../../../../small-web-crawler/dumps"

counter = {}

with open("../flows/wikihow-quiz-20220826.flow", "rb") as fl_f:
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

            if url_path=="/Special:QuizYourself":
                #print(fl.request.urlencoded_form)
                if fl.request.urlencoded_form["action"]=="get_quiz":
                    categ = fl.request.urlencoded_form["category"]
                    if categ not in counter:
                        counter[categ] = 0
                    dump_name = dump_name + "-{:}-{:}".format(categ, counter[categ])
                    counter[categ] += 1
                else:
                    dump_name = dump_name + "-CATEG"

            if url_path=="/Special:QuizYourself?wh_an=1&amp=1":
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
