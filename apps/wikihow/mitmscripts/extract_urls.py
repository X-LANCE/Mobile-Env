#!/usr/bin/python3

from mitmproxy import http
from mitmproxy import addonmanager
from mitmproxy import io

import re
import classify_url

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
#grouped_by_sec_fectch_sites = {}
#grouped_by_origin = {}
#  }}} Data Structure Definition # 

#  Main Structure {{{ # 
with open("../flows/wikihow-20220511-f.flow", "rb") as fl_f:
        #, open("wikihow-requets.list", "wb") as opt_f\
        #:
    flow_reader = io.FlowReader(fl_f)
    counter = 0
    for f in flow_reader.stream():
        if isinstance(f, http.HTTPFlow) and f.request.pretty_host=="www.wikihow.com":
            #opt_f.write(f.request.path + "\n")

            #for k, v in f.request.headers.items():
                #if k not in attributes:
                    #attributes[k] = set()
                    #new_attributes.add(k)
                #attributes[k].add(v)

            #accept_value = f.request.headers["accept"]
            #if accept_value not in grouped_by_accepts:
                #grouped_by_accepts[accept_value] = []
            #grouped_by_accepts[accept_value].append(f.request.path)

            #url = f.request.path
            #url_key = classify_url.classify(url)

            #if url_key==r"/Special:SherlockController":
                #opt_f.write(f.request.content + b"\r")

            print(f.request.path_components)

            counter += 1
            if counter==10:
                break

            #grouped_by_urls[url_key].add(f.request.headers.get("x-requested-with", None))
            #grouped_by_urls[url_key].add(f.request.method)
            #grouped_by_urls[url_key].add(f.request.headers.get("sec-fetch-mode", None))
            #grouped_by_urls[url_key].add(f.request.headers.get("sec-fetch-dest", None))
            #grouped_by_urls[url_key].add(f.request.headers.get("sec-fetch-site", None))
            #grouped_by_urls[url_key].add(f.request.headers.get("accept-encoding", None))
            #grouped_by_urls[url_key].add(f.request.headers.get("content-type", None))
            #grouped_by_urls[url_key].add(f.request.headers.get("origin", None))
            #grouped_by_urls[url_key].add(f.request.headers.get("upgrade-insecure-requests", None))
            #grouped_by_urls[url_key].add("sec-fetch-size" in f.request.headers)
            #grouped_by_urls[url_key].add(f.request.headers.get("sec-fetch-user", None))
            #grouped_by_urls[url_key].add(f.request.headers.get("accept-language", None))
            #grouped_by_urls[url_key].add(f.request.headers.get("range", None))

            #if url_key=="/x/*":
                #if f.request.method not in grouped_by_methods:
                    #grouped_by_methods[f.request.method] = []
                #grouped_by_methods[f.request.method].append(url)

            #if url_key in {
                        #r"[[:others:]]",
                        ##r"/x/collect\?t={exit,amp}&*",
                        ##r"/x/amp-view\?*",
                        ##r"/images/*"
                    #}:
                #sec_fetch_site = f.request.headers.get("sec-fetch-site", None)
                #if sec_fetch_site not in grouped_by_sec_fectch_sites:
                    #grouped_by_sec_fectch_sites[sec_fetch_site] = []
                #grouped_by_sec_fectch_sites[sec_fetch_site].append(url)

            #if url_key in\
                    #{ r"/x/collect\?t={exit,amp}&*"
                    #, r"/x/amp-view\?*"
                    #}:
                #origin = f.request.headers.get("origin", None)
                #if origin not in grouped_by_origin:
                    #grouped_by_origin[origin] = []
                #grouped_by_origin[origin].append(url)

            #if f.response is not None:
                #status_codes.add(f.response.status_code)
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

#with open("sec_fetch_site-url.list", "w") as f:
    #for val, urls in grouped_by_sec_fectch_sites.items():
        #f.write("{:}:\n".format(val))
        #for url in urls:
            #f.write("{:}\n".format(url))
        #f.write("\n")

#with open("origin-url.list", "w") as f:
    #for val, urls in grouped_by_origin.items():
        #f.write("{:}:\n".format(val))
        #for url in urls:
            #f.write("{:}\n".format(url))
        #f.write("\n")

#with open("url-x_requested_with.list", "w") as f:
#with open("url-method.list", "w") as f:
#with open("url-sec_fetch_mode.list", "w") as f:
#with open("url-sec_fetch_dest.list", "w") as f:
#with open("url-sec_fetch_site.list", "w") as f:
#with open("url-accept_encoding.list", "w") as f:
#with open("url-content_type.list", "w") as f:
#with open("url-origin.list", "w") as f:
#with open("url-upgrade_insecure_requests.list", "w") as f:
#with open("url-sec_fetch_size.list", "w") as f:
#with open("url-sec_fetch_user.list", "w") as f:
#with open("url-accept_language.list", "w") as f:
#with open("url-range.list", "w") as f:
    #for val, attrbs in grouped_by_urls.items():
        #f.write("{:}:\n".format(val))
        #for attrb in attrbs:
            #f.write("{:}\n".format(attrb))
        #f.write("\n")
#  }}} Output # 
