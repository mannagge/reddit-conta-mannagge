#!/bin/bash

export CONTAMANNAGGE_USERNAME=""
export CONTAMANNAGGE_PASSWORD=""
export CONTAMANNAGGE_CLIENT_ID=""
export CONTAMANNAGGE_CLIENT_SECRET=""
export CONTAMANNAGGE_SUBS=""
#export CONTAMANNAGGE_USER_AGENT=""
#export CONTAMANNAGGE_BOT_NAME="ContaMannagge"

mkdir -p data

docker build -t reddit-conta-mannagge .

docker run --rm -ti -v `pwd`/data:/contamannagge/data \
	-e CONTAMANNAGGE_USERNAME \
	-e CONTAMANNAGGE_PASSWORD \
	-e CONTAMANNAGGE_CLIENT_ID \
	-e CONTAMANNAGGE_CLIENT_SECRET \
	-e CONTAMANNAGGE_SUBS \
	-e CONTAMANNAGGE_USER_AGENT \
	-e CONTAMANNAGGE_BOT_NAME \
	reddit-conta-mannagge
