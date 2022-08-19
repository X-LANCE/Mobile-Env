#!/bin/bash

python -m pyserini.index.lucene \
  --collection JsonCollection \
  --input ../../../../small-web-crawler/indices-t/docs \
  --index ../../../../small-web-crawler/indices-t/indices \
  --generator DefaultLuceneDocumentGenerator \
  --threads 1 \
  --storePositions --storeDocvectors --storeRaw
