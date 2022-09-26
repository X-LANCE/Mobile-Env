from mitmproxy import http
from mitmproxy import ctx
import os.path
import functools
import classify_url
import load_response
import datetime
import locale
import gzip
import lxml.html
import lxml.cssselect
from pyserini.search.lucene import LuceneSearcher
import csv
import urllib.parse
from typing import List
from typing import Mapping
from mitmproxy.coretypes.multidict import MultiDict
import random

class Replayer:
    #  class `Replayer` {{{ # 
    def __init__(self, start_cache_index: int,
            replay_path: str,
            template_path: str,
            index_path: str,
            meta_path: str):
        self.cache_index: int = start_cache_index

        self.replay_path: str = replay_path
        self.template_path: str = template_path
        self.index_path: str = index_path
        self.meta_path: str = meta_path
        with open(meta_path) as f:
            reader = csv.DictReader(f)
            self.meta_database: Dict[str, Mapping[str, str]]\
                    = {itm["doc_id"]: itm for itm in reader}
        self.doc_list: List[str] = list(self.meta_database.keys())

        locale.setlocale(locale.LC_TIME, "en_US.utf8")
        self.dateformat: str = "%a, %d %b %Y %H:%M:%S GMT"
        self.searcher: LuceneSearcher = LuceneSearcher(self.index_path)

        #  CSS Selectors {{{ # 
        self.search_input_selector: lxml.cssselect.CSSSelector\
                = lxml.cssselect.CSSSelector("input#hs_query", translator="html")
        self.result_list_selector: lxml.cssselect.CSSSelector\
                = lxml.cssselect.CSSSelector("div#searchresults_list.wh_block", translator="html")
        self.result_list_anchor_selector: lxml.cssselect.CSSSelector\
                = lxml.cssselect.CSSSelector("div#search_adblock_bottom", translator="html")
        self.result_footer_anchor_selector: lxml.cssselect.CSSSelector\
                = lxml.cssselect.CSSSelector("div#searchresults_footer>div.sr_text", translator="html")

        self.result_thumb_selector: lxml.cssselect.CSSSelector\
                = lxml.cssselect.CSSSelector("div.result_thumb", translator="html")
        self.result_title_selector: lxml.cssselect.CSSSelector\
                = lxml.cssselect.CSSSelector("div.result_title", translator="html")
        self.result_view_selector: lxml.cssselect.CSSSelector\
                = lxml.cssselect.CSSSelector("li.sr_view", translator="html")
        self.result_updated_selector: lxml.cssselect.CSSSelector\
                = lxml.cssselect.CSSSelector("li.sr_updated", translator="html")
        self.result_verif_selector: lxml.cssselect.CSSSelector\
                = lxml.cssselect.CSSSelector("li.sp_verif", translator="html")
        self.sha_index_selector: lxml.cssselect.CSSSelector\
                = lxml.cssselect.CSSSelector("input[name=\"sha_index\"]", translator="html")
        self.sha_id_selector: lxml.cssselect.CSSSelector\
                = lxml.cssselect.CSSSelector("input[name=\"sha_id\"]", translator="html")
        self.sha_title_selector: lxml.cssselect.CSSSelector\
                = lxml.cssselect.CSSSelector("input[name=\"sha_title\"]", translator="html")
        #  }}} CSS Selectors # 

        self.search_page_capacity: int = 30
        self.search_capacity: int = 300

    def request(self, flow: http.HTTPFlow):
        url_path = flow.request.path
        url_key = classify_url.classify(url_path)
        if url_key in [ r"/x/collect\?t={first,later}&*"
                      , r"/x/collect\?t={exit,amp}&*"
                      , r"/x/amp-view\?*"
                      , r"/ev/*"
                      ]:
            #  Control Flows {{{ # 
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
            #  }}} Control Flows # 
        elif url_path.startswith("/wikiHowTo?search="):
            #  Search Pages {{{ # 
            url_items = urllib.parse.urlparse(url_path)
            queries = urllib.parse.parse_qs(url_items.query)
            search_keywords = queries["search"][0]
            start_index = int(queries.get("start", ["0"])[0])

            hits = self.searcher.search(search_keywords, k=self.search_capacity)
            response_time = datetime.datetime.utcnow()

            # build the webpage
            page_body = lxml.html.parse(
                    os.path.join(self.template_path, "search-page.html.template")).getroot()

            # 1. fill the parameters in the page body
            search_input = self.search_input_selector(page_body)[0]
            search_input.set("value", search_keywords)

            # 2. prepare result list
            #result_list = self.result_list_selector(page_body)[0]
            result_list_bottom = self.result_list_anchor_selector(page_body)[0]
            with open(os.path.join(self.template_path, "search-item.html.template")) as f:
                result_item_html = "".join(f.readlines())
            for i, h in zip(range(start_index, start_index+self.search_page_capacity),
                    hits[start_index:start_index+self.search_page_capacity]):
                docid = h.docid
                article_path = docid.replace("%2f", "/")

                result_item = lxml.html.fromstring(result_item_html)

                #  Update Item Parameters {{{ # 
                result_item.set("href", "https://www.wikihow.com/{:}".format(article_path))

                result_thumb = self.result_thumb_selector(result_item)[0]
                thumb_url = self.meta_database[docid]["thumb_url"]
                if thumb_url!="":
                    result_thumb.set("style",
                        "background-image: url(https://www.wikihow.com{:})".format(thumb_url.replace("%2f", "/")))
                else:
                    result_thumb.set("style",
                        "background-image: url(https://www.wikihow.com/5/5f/{doc_id:}-Step-2.jpg/-crop-250-145-193px-{doc_id}-Step-2.jpg)".format(doc_id=article_path))

                new_result_title = lxml.html.fromstring(
                        "<div class=\"result_title\">{:}</div>"\
                            .format(" ".join(
                                map(lambda w: "<b>" + w + "</b>",
                                    ["How", "to"] + urllib.parse.unquote_plus(article_path.replace("-", " "))\
                                            .split()))))
                result_title = self.result_title_selector(result_item)[0]
                result_title.getparent().replace(result_title, new_result_title)

                result_view = self.result_view_selector(result_item)[0]
                view_counts = self.meta_database[docid]["sr_view"]
                if view_counts!="":
                    result_view.text = "{:} views\t\t\t\t\t\t".format(view_counts)
                else:
                    result_view.text = "0 views\t\t\t\t\t\t"

                result_updated = self.result_updated_selector(result_item)[0]
                updated_date = self.meta_database[docid]["sr_updated"]
                if updated_date!="":
                    updated_date = datetime.datetime.strptime(updated_date,
                            "%B %d, %Y")
                    updating_duration = response_time - updated_date
                    #  Calculate Time Diff String {{{ # 
                    days = updating_duration.days
                    if days<7:
                        time_diff_str = "{:} day{:} ago".format(
                                days, "" if days==1 else "s")
                    elif days<30:
                        weeks = days // 7
                        time_diff_str = "{:} week{:} ago".format(
                                weeks, "" if weeks==1 else "s")
                    elif days<365:
                        months = days // 30
                        time_diff_str = "{:} month{:} ago".format(
                                months, "" if months==1 else "s")
                    else:
                        years = days // 365
                        time_diff_str = "{:} year{:} ago".format(
                                years, "" if years==1 else "s")
                    #  }}} Calculate Time Diff String # 
                    list(result_updated)[0].tail = time_diff_str + "\t\t\t\t\t\t"
                else:
                    list(result_updated)[0].tail = "12 hours ago\t\t\t\t\t\t"

                result_verif = self.result_verif_selector(result_item)[-1]
                verif_type = self.meta_database[docid]["sr_verif"]
                if verif_type=="E":
                    result_verif.text = "Expert Co-Authored\t\t\t\t\t\t\t"
                elif verif_type=="Q":
                    result_verif.text = "Quality Tested\t\t\t\t\t\t\t"
                else:
                    result_verif.getparent().remove(result_verif)

                sha_index = self.sha_index_selector(result_item)[0]
                sha_index.set("value", str(i+1))

                sha_id = self.sha_id_selector(result_item)[0]
                sha_id.set("value", self.meta_database[docid]["sha_id"])

                sha_title = self.sha_title_selector(result_item)[0]
                sha_title.set("value", article_path)
                #  }}} Update Item Parameters # 

                result_list_bottom.addprevious(result_item)

            # 3. prepare footer
            result_footer_bottom = self.result_footer_anchor_selector(page_body)[0]
            with open(os.path.join(self.template_path, "search-button.html.template")) as f:
                result_footer = lxml.html.fromstring("".join(f.readlines()))
            next_button, previous_button, statistics_text = list(result_footer)

            if start_index+self.search_page_capacity<self.search_capacity:
                # has next
                next_button.set("href", "/wikiHowTo?search={:}&start={:}&wh_an=1".format(
                        urllib.parse.quote_plus(search_keywords),
                        start_index+self.search_page_capacity))
                result_footer_bottom.addprevious(next_button)
            else:
                disabled_next = lxml.html.fromstring(
                        "<span class=\"button buttonright primary disabled\">Next ></span>")
                result_footer_bottom.addprevious(disabled_next)

            if start_index>0:
                # has previous
                enabled_previous = lxml.html.fromstring(
                        "<a class=\"button buttonleft primary\">&lt; Previous</a>")
                enabled_previous.set("href",
                    "/wikiHowTo?search={:}&start={:}&wh_an=1".format(
                        urllib.parse.quote_plus(search_keywords),
                        start_index-self.search_page_capacity))
                result_footer_bottom.addprevious(enabled_previous)
            else:
                result_footer_bottom.addprevious(previous_button)

            statistics_text.text = "{:} Results".format(self.search_capacity)
            result_footer_bottom.addprevious(statistics_text)

            # 4. return result
            full_page = lxml.html.tostring(page_body)

            headers = {}
            headers["content-type"] = "text/html; charset=UTF-8"
            headers["content-language"] = "en"
            headers["x-frame-options"] = "SAMEORIGIN"
            headers["x-p"] = "ma"
            headers["expires"] = (response_time + datetime.timedelta(days=1))\
                    .strftime(self.dateformat)
            headers["cache-control"] = "s-maxage=86400, must-revalidate, max-age=0"
            headers["content-encoding"] = "gzip"
            headers["accept-ranges"] = "bytes"
            headers["date"] = response_time.strftime(self.dateformat)
            headers["age"] = "0"
            headers["x-timer"] = "S{:.6f},VS0,VE0".format(response_time.timestamp())
            headers["x-c"] = "cache-tyo{:d}-TYO,M".format(self.cache_index)
            headers["x-content-type-options"] = "nosniff"
            headers["x-xss-protection"] = "1; mode=block"
            headers["strict-transport-security"] = "max-age=31536000; includeSubDomains; preload"
            headers["set-cookie"] =\
                "whv=lbYVTnTp1cUHHoDGDOwR; expires={:}; domain=.wikihow.com; path=/; secure"\
                    .format((response_time + datetime.timedelta(days=3654)).strftime(self.dateformat))
            headers["vary"] = "Cookie, Accept-Encoding"

            flow.response = http.Response.make(200,
                    content=full_page,
                    headers=headers)

            self.cache_index += 1
            #  }}} Search Pages # 
        elif url_path.startswith("/Special:Randomizer"):
            #  Random Page {{{ # 
            random_index = random.randrange(len(self.doc_list))
            doc_id = self.doc_list[random_index]
            article_path = doc_id.replace("%2f", "/")

            headers = {}

            response_time = datetime.datetime.utcnow()
            headers["content-type"] = "text/html; charset=UTF-8"
            headers["expires"] = "Thu, 01 Jan 1970 00:00:00 GMT"
            headers["cache-control"] = "private, must-revalidate, max-age=0"
            headers["x-p"] = "ma"
            headers["location"] = "https://www.wikihow.com/{:}".format(article_path)
            headers["content-encoding"] = "gzip"
            headers["accept-ranges"] = "bytes"
            headers["date"] = response_time.strftime(self.dateformat)
            headers["x-timer"] = "S{:.6f},VS0,VE0".format(response_time.timestamp())
            headers["x-c"] = "cache-tyo{:d}-TYO,M".format(self.cache_index)
            headers["x-content-type-options"] = "nosniff"
            headers["x-xss-protection"] = "1; mode=block"
            headers["strict-transport-security"] = "max-age=31536000; includeSubDomains; preload"
            headers["vary"] = "Cookie, Accept-Encoding"

            flow.response = http.Response.make(302,
                    headers=headers)

            self.cache_index += 1
            #  }}} Random Page # 
        elif url_path.startswith("/Special:RateItem"):
            #  Reting Flows {{{ # 
            headers = {}

            response_time = datetime.datetime.utcnow()
            headers["content-type"] = "text/html; charset=UTF-8"
            headers["access-control-allow-credentials"] = "true"
            headers["access-control-allow-origin"] = "https://www.wikihow.com"
            headers["access-control-expose-headers"] = "AMP-Access-Control-Allow-Source-Origin"
            headers["amp-access-control-allow-source-origin"] = "https://www.wikihow.com"
            #headers["set-cookie"] =\
                    #"UseDC=master; expires={:}; Max-Age=10; path=/; domain=www.wikihow.com; secure; HttpOnly"
            headers["content-language"] = "en"
            headers["x-frame-options"] = "SAMEORIGIN"
            headers["expires"] = "Thu, 01 Jan 1970 00:00:00 GMT"
            headers["cache-control"] = "private, must-revalidate, max-age=0"
            headers["x-p"] = "ck ma"
            headers["content-encoding"] = "gzip"
            headers["accept-ranges"] = "bytes"
            headers["date"] = response_time.strftime(self.dateformat)
            headers["x-timer"] = "S{:.6f},VS0,VE0".format(response_time.timestamp())
            headers["x-c"] = "cache-tyo{:d}-TYO,M".format(self.cache_index)
            headers["x-content-type-options"] = "nosniff"
            headers["x-xss-protection"] = "1; mode=block"
            headers["strict-transport-security"] = "max-age=31536000; includeSubDomains; preload"
            headers["vary"] = "Cookie, Accept-Encoding"

            flow.response = http.Response.make(200,
                    content=b'{"result":"true"}',
                    headers=headers)

            cookies_attribute = MultiDict([
                        ("expires", (response_time + datetime.timedelta(seconds=10))\
                                .strftime(self.dateformat)),
                        ("Max-Age", "10"),
                        ("path", "/"),
                        ("domain", "www.wikihow.com"),
                        ("secure", None),
                        ("HttpOnly", None)
                    ])
            flow.response.cookies["UseDC"] = ("master", cookies_attribute)
            flow.response.cookies["UseCDNCache"] = ("false", cookies_attribute.copy())

            self.cache_index += 1
            #  }}} Reting Flows # 
        else:
            #  Normal Pages {{{ # 
            if url_key==r"/Special:RCWidget\?*":
                filename = "%2fSpecial:RCWidget?function=WH.RCWidget.rcwOnLoadData&GuVHo&nabrequest=0&anonview=1"
            else:
                filename = url_path.replace("/", "%2f")
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
                        ctx.log.info(str(e))

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
            #  }}} Normal Pages # 
    #  }}} class `Replayer` # 

addons = [
        Replayer(15090,
            "/mnt/xlancefs/home/dyz32/wikihow/dumps",
            "/mnt/xlancefs/home/dyz32/wikihow/templates",
            "/mnt/xlancefs/home/dyz32/wikihow/indices-t/indices",
            "/mnt/xlancefs/home/dyz32/wikihow/indices-t/docs/doc_meta.csv")
    ]
