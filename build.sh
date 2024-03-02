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
docker buildx create --name rsscrawlerbuilder --use
docker buildx build --platform linux/amd64,linux/arm64 -t johnunderwood197/${name}:latest -t johnunderwood197/${name}:${abbrvhash} --push .
docker buildx stop rsscrawlerbuilder
docker buildx rm rsscrawlerbuilder