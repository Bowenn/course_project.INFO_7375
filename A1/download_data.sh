#!/bin/bash

ROOT=https://data.commoncrawl.org/crawl-data/CC-MAIN-2018-17/segments/1524125937193.1/

# Note: the --no-clobber arg required curl 7.83. If it doesn't work for you,
# you can either update curl or remove that argument.

mkdir -p dataset

curl -o dataset/data.warc.gz --no-clobber ${ROOT}warc/CC-MAIN-20180420081400-20180420101400-00000.warc.gz
gunzip dataset/data.warc.gz

curl -o dataset/data.wet.gz --no-clobber ${ROOT}wet/CC-MAIN-20180420081400-20180420101400-00000.warc.wet.gz
gunzip dataset/data.wet.gz

curl -o dataset/data.wat.gz --no-clobber ${ROOT}wat/CC-MAIN-20180420081400-20180420101400-00000.warc.wat.gz
gunzip dataset/data.wat.gz