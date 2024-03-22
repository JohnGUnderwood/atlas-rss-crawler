#!/bin/bash
source .env
echo "Using args:"
echo "\t${MDBCONNSTR}\n"
echo "\t${MDB_DB}\n"
echo "\t${PROVIDER}\n"
echo "\t${OPENAIAPIKEY}\n"
echo
echo "Pulling docker image from johnunderwood197/rsscrawler:latest"
docker pull johnunderwood197/rsscrawler:latest
echo 
echo "Starting container"
echo
docker stop rsscrawler
docker rm rsscrawler
docker run -t -i -d -p 3000:3000 -p 3010:3010 --name rsscrawler \
-e "MDBCONNSTR=${MDBCONNSTR}" \
-e "MDB_DB=${MDB_DB}" \
-e "OPENAIAPIKEY=${OPENAIAPIKEY}" \
-e "PROVIDER=${PROVIDER}" \
--restart unless-stopped johnunderwood197/rsscrawler:latest