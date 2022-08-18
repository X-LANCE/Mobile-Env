from mitmproxy import http
from mitmproxy import ctx
import os.path
import functools
import classify_url
import datetime
import load_response
import locale
import gzip

class Replayer:
    #  class `Replayer` {{{ # 
    def __init__(self, replay_path: str):
        locale.setlocale(locale.LC_TIME, "en_US.utf8")

        self.replay_path = replay_path
        self.dateformat = "%a, %d %b %Y %H:%M:%S GMT"

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

                response_time = datetime.datetime.utcnow()
                headers["retry-after"] = "0"
                headers["accept-ranges"] = "bytes"
                headers["date"] = response_time.strftime(self.dateformat)
                headers["x-timer"] = "S{:.6f},VS0,VE0".format(response_time.timestamp())
                headers["x-c"] = "cache-tyo{:d}-TYO,M".format(self.cache_index)
                headers["x-content-type-options"] = "nosniff"
                headers["x-xss-protection"] = "1; mode=block"
                headers["strict-transport-security"] = "max-age=31536000; includeSubDomains; preload"
                headers["content-type"] = "text/plain; charset=UTF-8"
                headers["x-robots-tag"] = "noindex, nofollow"

                flow.response = http.Response.make(204,
                        headers=headers)

                self.cache_index += 1
            #elif url_key in [ r"/load.php\?*only=styles*"
                            #, r"R /load.php?.\+$\(only=styles\)\@!"
                            #]:
                #pass
            else:
                filename = flow.request.path.replace("/", "%2f")
                if len(filename)>100:
                    filename = filename[:100]
                filename = os.path.join(self.replay_path, filename)
                #ctx.log.info("Requesting {:}".format(filename))
                if not os.path.exists(filename):
                    ctx.log.info("404: {:}".format(filename))
                    flow.response = http.Response.make(404)
                else:
                    status_code, header, content = load_response.load_response(filename)

                    if "content-encoding" in header\
                            and header["content-encoding"]==b"gzip"\
                            and len(content)>0:
                        try:
                            content = gzip.decompress(content)
                        except Exception as e:
                            ctx.log(str(e))

                    response_time = datetime.datetime.utcnow()
                    #if "date" in header:
                        #header["date"] = response_time.strftime(self.dateformat)
                    #if "last-modified" in header:
                        #header["last-modified"] = (response_time - datetime.timedelta(days=1))\
                                #.strftime(self.dateformat)
                    #if "expires" in header:
                        #header["expires"] = (response_time + datetime.timedelta(days=3650))\
                                #.strftime(self.dateformat)
                    if "x-timer" in header:
                        header["x-timer"] = "S{:.6f},VS0,VE0".format(response_time.timestamp())
                    if "x-c" in header:
                        header["x-c"] = "cache-tyo{:d}-TYO,M".format(self.cache_index)

                    flow.response = http.Response.make(status_code,
                            content=content,
                            headers=header)
                    flow.response.refresh()
                    #ctx.log.info("WARN: {:}".format(content==flow.response.content))

                    self.cache_index += 1
        else:
            flow.response = http.Response.make(204)
    #  }}} class `Replayer` # 

addons = [
        Replayer("../../../small-web-crawler/dumps")
    ]
