from mitmproxy import http
from mitmproxy import addonmanager

import io

class URLDumper:
    def load(self, loader: addonmanager.Loader):
        #  method `load` {{{ # 
        self.filename: str = "wikihow-urls.list"
        self.file: io.TextIOWrapper = open(self.filename)
        #  }}} method `load` # 

    def response(self, flow: http.HTTPFlow):
        if flow.host=="www.wikihow.com":
            self.file.write(flow.url)

    def done(self):
        self.file.flush()
        self.file.close()

addons = [
        URLDumper()
    ]
