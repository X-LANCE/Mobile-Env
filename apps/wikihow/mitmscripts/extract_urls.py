from mitmproxy import http
from mitmproxy import addonmanager
from mitmproxy import io

#import io

#class URLDumper:
    #def load(self, loader: addonmanager.Loader):
        ##  method `load` {{{ # 
        #self.filename: str = "wikihow-urls.list"
        #self.file: io.TextIOWrapper = open(self.filename, "w")
        ##  }}} method `load` # 
#
    #def response(self, flow: http.HTTPFlow):
        #if flow.host=="www.wikihow.com":
            #self.file.write(flow.url)
#
    #def done(self):
        #self.file.flush()
        #self.file.close()
#
#addons = [
        #URLDumper()
    #]

attributes = [
        "upgrade-insecure-requests",
        "user-agent",
        "accept",
        "x-requested-with",
        "sec-fetch-size",
        "sec-fetch-mode",
        "sec-fetch-user",
        "sec-fetch-dest",
        "accept-encoding",
        "accept-language",
        "cookie"
    ]
attributes = {attrb: set() for attrb in attributes}
new_attributes = set()

status_codes = set()

with open("../flows/wikihow-20220511-f.flow", "rb") as fl_f:
        #open("wikihow-urls.list", "w") as opt_f:
    flow_reader = io.FlowReader(fl_f)
    for f in flow_reader.stream():
        if isinstance(f, http.HTTPFlow) and f.request.pretty_host=="www.wikihow.com":
            #opt_f.write(f.request.url + "\n")

            for k, v in f.request.headers.items():
                if k not in attributes:
                    attributes[k] = set()
                    new_attributes.add(k)
                attributes[k].add(v)

            if f.response is not None:
                status_codes.add(f.response.status_code)

print("\x1b[32mNew Attributes\x1b[0m")
for k in new_attributes:
    print(k)
print()

for k in attributes:
    if k=="cookie" or k=="referer":
        continue
    print("\x1b[32mAttribute {:}\x1b[0m".format(k))
    for v in attributes[k]:
        print(v)
    print()

print("\x1b[32mStatus Codes\x1b[0m")
for c in status_codes:
    print(c)
