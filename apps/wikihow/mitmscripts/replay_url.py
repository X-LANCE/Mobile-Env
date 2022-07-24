from mitmproxy import http
import os.path
import functools

class Replayer:
    #  class `Replayer` {{{ # 
    def request(self, flow: http.HTTPFlow):
        if flow.request.pretty_host=="www.wikihow.com":
            filename = flow.request.path.replace("/", "%2f")
            if len(filename)>100:
                filename = filename[:100]
            filename = os.path.join("mitmscripts/pages/test-mitmproxy/", filename)
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
        Replayer()
    ]
