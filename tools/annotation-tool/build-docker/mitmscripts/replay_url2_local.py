from mitmproxy import http
from mitmproxy import ctx
from mitmproxy.addonmanager import Loader
#import datetime
#import locale
import os
from typing import Sequence

class Replayer:
    #  class `Replayer` {{{ # 
    def __init__(self, data_server: str,
            data_port: int = 8080):
        self.data_server: str = data_server
        self.data_port: int = data_port

        #locale.setlocale(locale.LC_TIME, "en_US.utf8")
        #self.dateformat: str = "%a, %d %b %Y %H:%M:%S GMT"

    def load(self, loader: Loader):
        loader.add_option( name="replay_host"
                         , typespec=Sequence[str]
                         , default=["www.wikihow.com"]
                         , help="The domain name to be replayed"
                         )

    def request(self, flow: http.HTTPFlow):
        if flow.request.pretty_host in ctx.options.replay_host:
            flow.request.host = self.data_server
            flow.request.port = self.data_port
    #  }}} class `Replayer` # 

addons = [
        Replayer(os.environ["WIKIHOW_SERVER"],
            data_port=int(os.environ["WIKIHOW_PORT"]))
    ]
