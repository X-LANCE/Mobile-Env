from mitmproxy import http
from mitmproxy import ctx
#import datetime
#import locale
import os

class Replayer:
    #  class `Replayer` {{{ # 
    def __init__(self, data_server: str,
            data_port: int = 8080):
        self.data_server: str = data_server
        self.data_port: int = data_port

        #locale.setlocale(locale.LC_TIME, "en_US.utf8")
        #self.dateformat: str = "%a, %d %b %Y %H:%M:%S GMT"

    def request(self, flow: http.HTTPFlow):
        if flow.request.pretty_host=="www.wikihow.com":
            flow.request.host = self.data_server
            flow.request.port = self.data_port
    #  }}} class `Replayer` # 

addons = [
        Replayer(os.environ["WIKIHOW_SERVER"],
            data_port=int(os.environ["WIKIHOW_PORT"]))
    ]
