#!/usr/bin/python3

from pyserini.search.lucene import LuceneSearcher

searcher = LuceneSearcher("../../../../small-web-crawler/indices-t/indices")
hits = searcher.search("water dispenser")

for i, h in enumerate(hits):
    print("{:}\t{:}\t{:}".format(i, h.docid, h.score))
