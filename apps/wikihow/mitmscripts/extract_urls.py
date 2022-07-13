from mitmproxy import http
from mitmproxy import addonmanager
from mitmproxy import io

import re

#  Data Structure Definition {{{ # 
attributes = [
        "upgrade-insecure-requests",
        "user-agent",
        "accept",
        "x-requested-with",
        "sec-fetch-size",
        "sec-fetch-mode",
        "sec-fetch-user",
        "sec-fetch-dest",
        "sec-fetch-site",
        "accept-encoding",
        "accept-language",
        "cookie",
        "content-type",
        "content-length",
        "range",
        "origin",
        "referer",
    ]
attributes = {attrb: set() for attrb in attributes}
new_attributes = set()

status_codes = set()

url_categories = [
        r"[[:others:]]",
        r"/x/collect\?t={first,later}&*",
        r"/x/zscsucgm\?",
        r"/x/collect\?t={exit,amp}&*",
        r"/x/amp-view\?*",
        r"/ev/*",
        r"R /load.php?.\+$\(only=styles\)\@!",
        r"/video/*",
        r"/Special:SherlockController",
        r"/Special:RCWidget\?*",
        r"/load.php\?*only=styles*",
        r"/extensions/wikihow/*",
        r"/images/*",
        r"/skins/*"
    ]

#grouped_by_accepts = {}
grouped_by_urls = {url_ctgr: set() for url_ctgr in url_categories}
#grouped_by_methods = {}
#  }}} Data Structure Definition # 

#  Main Structure {{{ # 
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

            #accept_value = f.request.headers["accept"]
            #if accept_value not in grouped_by_accepts:
                #grouped_by_accepts[accept_value] = []
            #grouped_by_accepts[accept_value].append(f.request.path)

            #  URL Classification {{{ # 
            url = f.request.path
            if url.startswith("/x/collect?t="):
                if url[13:].startswith("first") or url[13:].startswith("later"):
                    url_key = r"/x/collect\?t={first,later}&*"
                elif url[13:].startswith("exit") or url[13:].startswith("amp"):
                    url_key = r"/x/collect\?t={exit,amp}&*"
                else:
                    print("\x1b[1;31mError!\x1b[0m")
                    exit
            elif url=="/x/zscsucgm?":
                url_key = r"/x/zscsucgm\?"
            elif url.startswith("/x/amp-view?"):
                url_key = r"/x/amp-view\?*"
            elif url.startswith("/ev/"):
                url_key = r"/ev/*"
            elif url.startswith("/load.php?"):
                if "only=styles" in url:
                    url_key = r"/load.php\?*only=styles*"
                else:
                    url_key = r"R /load.php?.\+$\(only=styles\)\@!"
            elif url.startswith("/video/"):
                url_key = r"/video/*"
            elif url=="/Special:SherlockController":
                url_key = r"/Special:SherlockController"
            elif url.startswith("/Special:RCWidget?"):
                url_key = r"/Special:RCWidget\?*"
            elif url.startswith("/extensions/wikihow/"):
                url_key = r"/extensions/wikihow/*"
            elif url.startswith("/images/"):
                url_key = r"/images/*"
            elif url.startswith("/skins/"):
                url_key = r"/skins/*"
            else:
                url_key = "[[:others:]]"
            #  }}} URL Classification # 

            #grouped_by_urls[url_key].add(f.request.headers.get("x-requested-with", None))
            grouped_by_urls[url_key].add(f.request.method)
            #grouped_by_urls[url_key].add(f.request.headers.get("sec-fetch-mode", None))

            #if url_key=="/x/*":
                #if f.request.method not in grouped_by_methods:
                    #grouped_by_methods[f.request.method] = []
                #grouped_by_methods[f.request.method].append(url)

            if f.response is not None:
                status_codes.add(f.response.status_code)
#  }}} Main Structure # 

#  Output {{{ # 
#with open("attribute_statistics.list", "w") as f:
    #print("\x1b[32mNew Attributes\x1b[0m", file=f)
    #for k in new_attributes:
        #print(k, file=f)
    #print(file=f)
#
    #for k in attributes:
        #if k=="cookie" or k=="referer":
            #continue
        #print("\x1b[32mAttribute {:}\x1b[0m".format(k), file=f)
        #for v in attributes[k]:
            #print(v, file=f)
        #print(file=f)
#
    #print("\x1b[32mStatus Codes\x1b[0m", file=f)
    #for c in status_codes:
        #print(c, file=f)

#with open("accept-url.list", "w") as f:
    #for val, urls in grouped_by_accepts.items():
        #f.write("{:}:\n".format(val))
        #for url in urls:
            #f.write("{:}\n".format(url))
        #f.write("\n")

#with open("method-url.list", "w") as f:
    #for val, urls in grouped_by_methods.items():
        #f.write("{:}:\n".format(val))
        #for url in urls:
            #f.write("{:}\n".format(url))
        #f.write("\n")

#with open("url-x_requested_with.list", "w") as f:
with open("url-method.list", "w") as f:
#with open("url-sec_fetch_mode.list", "w") as f:
    for val, attrbs in grouped_by_urls.items():
        f.write("{:}:\n".format(val))
        for attrb in attrbs:
            f.write("{:}\n".format(attrb))
        f.write("\n")
#  }}} Output # 
