#!/bin/bash
source .env
echo "Using args ${MDBCONNSTR}"

echo
echo "+================================"
echo "| START: ATLAS RSS CRAWLER"
echo "+================================"
echo

datehash=`date | md5sum | cut -d" " -f1`
abbrvhash=${datehash: -8}
name="rsscrawler"

echo 
echo "Building container using tag ${abbrvhash} and buildx"
echo
docker build --platform linux/amd64 -t johnunderwood197/${name}:latest -t johnunderwood197/${name}:${abbrvhash} .