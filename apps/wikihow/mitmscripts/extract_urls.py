#!/usr/bin/python3

from mitmproxy import http
from mitmproxy import addonmanager
from mitmproxy import io

import re
import classify_url
import os.path
import load_response

import sys

#  Main Structure {{{ # 
with open(sys.argv[1], "rb") as fl_f:
        #open(os.path.basename(sys.argv[1]), "w") as l_f:
    flow_reader = io.FlowReader(fl_f)
    counter = 0
    for f in flow_reader.stream():
        if isinstance(f, http.HTTPFlow) and f.request.pretty_host=="www.wikihow.com":

            url = f.request.path
            #l_f.write(url + "\n")
            if url=="/Special:SortQuestions?wh_an=1&amp=1":
                with open("SQ.html.gz", "wb") as cpr_f:
                    cpr_f.write(f.response.raw_content)
#  }}} Main Structure # 
