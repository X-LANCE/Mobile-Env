from mitmproxy import http
import os.path
import functools
import classify_url
import datetime

class Replayer:
    #  class `Replayer` {{{ # 
    def __init__(self, replay_path: str):
        #self.replay_path = "mitmscripts/pages/test-mitmproxy/"
        #self.replay_path = "../../../small-web-crawler/dumps"
        self.replay_path = replay_path
        self.cache_index = 15090

    def request(self, flow: http.HTTPFlow):
        if flow.request.pretty_host=="www.wikihow.com":
            url_key = classify_url.classify(flow.request.path)
            if url_key in [ r"/x/collect\?t={first,later}&*"
                          , r"/x/collect\?t={exit,amp}&*"
                          , r"/x/amp-view\?*"
                          , r"/ev/*"
                          ]:

                headers = {}

                response_time = datetime.utcnow()
                headers["retry-after"] = "0"
                headers["accept-ranges"] = "bytes"
                headers["date"] = response_time.strftime("%a, %d %b %Y %X GMT")
                headers["x-timer"] = "S{:.6f},VS0,VE0".format(response.timestamp())
                headers["x-c"] = "cache-tyo{:d}-TYO,M".format(self.cache_index)
                headers["x-content-type-options"] = "nosniff"
                headers["x-xss-protection"] = "1; mode=block"
                headers["strict-transport-security"] = "max-age=31536000; includeSubDomains; preload"
                headers["content-type"] = "text/plain; charset=UTF-8"
                headers["x-robots-tag"] = "noindex, nofollow"

                flow.response = http.Response.make(204,
                        headers=headers).refresh()

                self.cache_index += 1
            else:
                filename = flow.request.path.replace("/", "%2f")
                if len(filename)>100:
                    filename = filename[:100]
                filename = os.path.join(self.replay_path, filename)
                if not os.path.exists(filename):
                    flow.response = http.Response.make(404)
                else:
                    with open(filename, "rb") as f:
                        response = f.read()
                    header_bytes, _, content = response.partition(b"\r\n\r\n")
                    header_items = header_bytes.split(b"\r\n")
                    status_code = int(header_items[0].split()[1].strip())
                    header = {k.decode(): val for k, val in
                            map(functools.partial(bytes.split, sep=b": ", maxsplit=1),
                                header_items[1:])}

                    flow.response = http.Response.make(status_code,
                            content=content,
                            headers=header).refresh()
    #  }}} class `Replayer` # 

addons = [
        Replayer("../../../small-web-crawler/dumps")
    ]
