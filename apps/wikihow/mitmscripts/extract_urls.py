#!/usr/bin/python3

from mitmproxy import http
from mitmproxy import addonmanager
from mitmproxy import io

import re
import classify_url
import os.path
import load_response

#  Main Structure {{{ # 
with open("../flows/wikihow-20220511-f.flow", "rb") as fl_f:
    flow_reader = io.FlowReader(fl_f)
    counter = 0
    for f in flow_reader.stream():
        if isinstance(f, http.HTTPFlow) and f.request.pretty_host=="www.wikihow.com":

            url = f.request.path
            if url.startswith("/wikiHowTo?search="):
                dump_name = url.replace("/", "%2f")
                #if len(dump_name)>100:
                    #dump_name = dump_name[:100]

                with open(os.path.join("pages/search-pages/header", dump_name + ".txt"), "w") as opt_f:
                    for k, v in f.response.headers.items():
                        opt_f.write("{:}: {:}\n".format(k, v))
                with open(os.path.join("pages/search-pages/html", dump_name + ".html.gz"), "wb") as opt_f:
                    opt_f.write(f.response.raw_content)
#  }}} Main Structure # 

#_, _, content = load_response.load_response("../../../../small-web-crawler/dumps/%2f?wh_an=1&amp=1")
#
#with open("pages/index3.html.gz", "wb") as f:
    #f.write(content)
