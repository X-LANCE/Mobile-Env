#!/usr/bin/python3

import csv
import lxml.cssselect
import lxml.html
import load_response
import gzip
import urllib.parse
import yaml

title_selector = lxml.cssselect.CSSSelector(
        "h1#section_0>a", translator="html")
author_selector = lxml.cssselect.CSSSelector(
        "div#coauthor_byline a.coauthor_link",
        translator="html")
categ_selector = lxml.cssselect.CSSSelector(
        "ul#breadcrumb a", translator="html")

c_link_selector = lxml.cssselect.CSSSelector(
        "div.responsive_thumb>a", translator="html")
c_title_selector = lxml.cssselect.CSSSelector(
        "div.responsive_thumb_title>p", translator="html")

a_link_selector = lxml.cssselect.CSSSelector(
        "div#author_articles>a", translator="html")
a_title_selector = lxml.cssselect.CSSSelector(
        "p.author_title", translator="html")

with open("../../../../small-web-crawler/indices-t/docs/doc_meta.csv") as f:
    reader = csv.DictReader(f)
    database = {itm["doc_id"]: itm for itm in reader}

with open("stopword.list") as f:
    stopwords = set(
            map(str.strip, f))

author_set = set(
        map(lambda a: a[9:],
            filter(lambda a: a.startswith("Author%2f"),
                database.keys())))
category_set = set(
        map(lambda a: a[9:],
            filter(lambda a: a.startswith("Category:"),
                database.keys())))

article_infos = []
categ_infos = []
author_infos = []
for docid, itm in database.items():
    _, _, content = load_response.load_response("../../../../small-web-crawler/dumps/%2f{:}?wh_an=1&amp=1".format(docid))
    try:
        content = gzip.decompress(content)
        html = lxml.html.fromstring(content)
    except:
        continue

    if docid.startswith("Category:"):
        #  Category Page {{{ # 
        link_elements = c_link_selector(html)
        if len(link_elements)==0:
            continue

        categ = docid[9:]

        articles = []
        for l_elm in link_elements:
            if urllib.parse.urlparse(l_elm.get("href")).path[1:] not in database:
                continue

            title_elements = c_title_selector(l_elm)
            if len(title_elements)==0:
                continue
            title = title_elements[0].text_content().strip()
            articles.append(title)

        categ_infos.append(
            { "categ": categ
            , "articles": articles
            })
        #  }}} Category Page # 
    elif docid.startswith("Author%2f"):
        #  Author Page {{{ # 
        link_elements = a_link_selector(html)
        if len(link_elements)==0:
            continue

        author = docid[9:]

        articles = []
        for l_elm in link_elements:
            if urllib.parse.urlparse(l_elm.get("href")).path[1:] not in database:
                continue

            title_elements = a_title_selector(l_elm)
            if len(title_elements)==0:
                continue
            title = title_elements[0].text_content().strip()
            articles.append(title)

        author_infos.append(
            { "author": author
            , "articles": articles
            })
        #  }}} Author Page # 
    else:
        #  Article Page {{{ # 
        title_elements = title_selector(html)
        if len(title_elements)==0:
            continue
        title = title_elements[0].text_content().strip()[7:]

        keywords = list(
                filter(lambda kw: kw not in stopwords,
                    map(str.lower, title.split())))

        author_elements = author_selector(html)
        authors = []
        for elm in author_elements:
            author = elm.text_content().strip()
            if author=="Author Info" or author=="wikiHow Staff":
                continue
            if urllib.parse.quote_plus(author.replace(",", "").replace(" ", "-")) not in author_set:
                continue
            authors.append(author)

        categ_elements = categ_selector(html)
        categs = []
        for elm in categ_elements:
            categ = elm.text_content().strip()
            if categ=="Categories":
                continue
            if urllib.parse.quote_plus(categ.replace(" ", "-")) not in category_set:
                continue
            categs.append(categ)

        article_infos.append(
            { "title": title
            , "keywords": keywords
            , "authors": authors
            , "categs": categs
            })
        #  }}} Article Page # 

with open("article.info.yaml", "w") as f:
    yaml.dump(article_infos, f, yaml.Dumper, encoding="utf-8")

with open("categ.info.yaml", "w") as f:
    yaml.dump(categ_infos, f, yaml.Dumper, encoding="utf-8")

with open("author.info.yaml", "w") as f:
    yaml.dump(author_infos, f, yaml.Dumper, encoding="utf-8")
