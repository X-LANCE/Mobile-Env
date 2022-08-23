#!/usr/bin/python3

import csv
import json
import os.path
import os
import random

thumbs = list(
        filter(lambda l: l.startswith("%2fimages%2fthumb%2f"),
            os.listdir("../../../../small-web-crawler/dumps")))

sr_verifs = ["", "Q", "E"]

with open("../../../../small-web-crawler/indices-t/docs/doc_index.t.jsonl") as in_f,\
        open("../../../../small-web-crawler/indices-t/docs/doc_meta.csv", "w") as out_f:
    writer = csv.DictWriter(out_f, ["doc_id", "thumb_url", "sr_view", "sr_updated", "sr_verif", "sha_id"])
    writer.writeheader()
    for l in in_f:
        doc = json.loads(l.strip())
        meta = {}
        meta["doc_id"] = doc["id"]

        image_path = doc["id"]
        if len(image_path)>71:
            image_path = image_path[:71]
        underlying_thumbs = []
        for l in thumbs:
            if l[29:29+len(image_path)]==image_path:
                underlying_thumbs.append(l)
        if len(underlying_thumbs)==0:
            meta["thumb_url"] = ""
        else:
            for l in underlying_thumbs:
                if "-crop-250-1" in l: # 250x145
                    meta["thumb_url"] = l
                    break
            if "thumb_url" not in meta:
                meta["thumb_url"] = underlying_thumbs[0]

        meta["sr_view"] = random.randrange(3000, 100_0000)
        meta["sr_updated"] = random.randrange(3 + 11 + 5) # 1-3 weeks, 1-11 months, 1-5 years
        meta["sr_verif"] = sr_verifs[random.randrange(3)]
        meta["sha_id"] = random.randrange(1_0000_0000)
        writer.writerow(meta)
