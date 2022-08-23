#!/usr/bin/python3

import csv
import load_response
import gzip
import lxml.html

with open("../../../../small-web-crawler/indices-t/docs/doc_meta.csv") as f:
    reader = csv.DictReader(f)
    items = list(reader)

with open("../../../../small-web-crawler/indices-t/docs/doc_meta.csv", "w") as f:
    writer = csv.DictWriter(f, ["doc_id", "thumb_url", "sr_view", "sr_updated", "sr_verif", "sha_id"])
    writer.writeheader()
    for itm in items:
        _, _, content = load_response.load_response("../../../../small-web-crawler/dumps/%2f{:}?wh_an=1&amp=1".format(itm["doc_id"]))
        try:
            content = gzip.decompress(content)
            html = lxml.html.fromstring(content)
        except Exception as e:
            print(itm["doc_id"])
            print(e)
            writer.writerow(itm)
            continue

        author_line = html.cssselect("div#coauthor_byline a.coauthor_link.coauthor_checkstar")
        if len(author_line)>0:
            itm["sr_verif"] = "E"
        else:
            test_line = html.cssselect("div#coauthor_byline a.eat_tag")
            if any(map(lambda a: a.text_content()=="Tested", test_line)):
                itm["sr_verif"] = "Q"
            else:
                itm["sr_verif"] = ""

        itm["sr_updated"] = ""
        itm["sr_view"] = ""
        sp_stats_box = html.cssselect("div.sp_box.sp_stats_box.sp_fullbox>div.sp_text")
        for b in sp_stats_box:
            if b.text_content().strip().startswith("Updated:"):
                itm["sr_updated"] = b.text_content().strip()[9:]
            elif b.text_content().strip().startswith("Views:"):
                itm["sr_view"] = b.text_content().strip()[7:]

        writer.writerow(itm)
