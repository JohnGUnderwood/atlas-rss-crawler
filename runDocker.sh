#!/bin/bash
source backend/.env
echo "Using args ${MDBCONNSTR}"
echo "Using args ${MDB_DB}"
echo
echo "Pulling docker image from johnunderwood197/rsscrawler:latest"
docker pull johnunderwood197/rsscrawler:latest
echo 
echo "Starting container"
echo
docker stop rsscrawler
docker rm rsscrawler
docker run -t -i -d -p 3000:3000 -p 3010:3010 --name rsscrawler -e "MDBCONNSTR=${MDBCONNSTR}" -e "MDB_DB=${MDB_DB}" --restart unless-stopped johnunderwood197/rsscrawler:latest