FROM python:alpine
LABEL \
	maintainer="Davide Alberani <da@mimante.net>"

RUN \
	apk add --update --no-cache \
		sqlite && \
	pip3 install praw && \
	mkdir /contamannagge
COPY contamannagge.py /contamannagge

VOLUME /contamannagge/data

WORKDIR /contamannagge

ENTRYPOINT ["python3", "contamannagge.py"]

