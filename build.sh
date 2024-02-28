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
echo "Building container using tag ${abbrvhash}"
echo
docker build -t johnunderwood197/${name}:latest -t johnunderwood197/${name}:${abbrvhash} --platform=linux/amd64 .

EXITCODE=$?

if [ $EXITCODE -eq 0 ]
    then

    echo 
    echo "Starting container"
    echo
    docker stop ${name}
    docker rm ${name}
    docker run -t -i -d -p 3000:3000 -p 3010:3010 --name ${name} -e "MDBCONNSTR=${MDBCONNSTR}" -e --restart unless-stopped johnunderwood197/${name}:latest

    echo
    echo "+================================"
    echo "| END:  ATLAS RSS CRAWLER"
    echo "+================================"
    echo
else
    echo
    echo "+================================"
    echo "| ERROR: Build failed"
    echo "+================================"
    echo
fi