#!/usr/bin/python3

import json
import urllib.parse

with open("../../../../small-web-crawler/SearchList.list") as l_f,\
        open("../../../../small-web-crawler/doc_index.t.jsonl", "w") as idx_f:
    for l in l_f:
        # filename starts with "%2f" and ends with "?wh_an=1&amp=1"
        name = l.strip()[3:-14]
        if name.endswith("?amp=1"):
            continue
        content = urllib.parse.unquote(name.replace("%2f", "/").replace("-", "%20"))
        idx_f.write(json.dumps({"id": name, "contents": content}, ensure_ascii=False))
        idx_f.write("\n")
