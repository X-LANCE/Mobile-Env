from mitmproxy import http
from mitmproxy import ctx
import os.path
import functools
import classify_url
import load_response
import datetime
import locale
import gzip
import lxml.html
import lxml.cssselect
from pyserini.search.lucene import LuceneSearcher
import csv
import urllib.parse
from typing import List
from typing import Mapping
from mitmproxy.coretypes.multidict import MultiDict
import random
import os

class Replayer:
    #  class `Replayer` {{{ # 
    def __init__(self, start_cache_index: int):
        self.cache_index: int = start_cache_index

        self.data_server: str = data_server

        locale.setlocale(locale.LC_TIME, "en_US.utf8")
        #self.dateformat: str = "%a, %d %b %Y %H:%M:%S GMT"

    def request(self, flow: http.HTTPFlow):
        if flow.request.pretty_host=="www.wikihow.com":
            flow.request.host = self.data_server
    #  }}} class `Replayer` # 

addons = [
        Replayer(os.environ["WIKIHOW_SERVER"])
    ]
