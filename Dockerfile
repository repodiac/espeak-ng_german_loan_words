ARG BASEDIR=/pyapp

FROM python:3.8-slim-buster as py-base
ARG BASEDIR
WORKDIR $BASEDIR

RUN apt update
RUN apt install -y --no-install-recommends build-essential gcc wget
RUN pip install pip --upgrade
RUN pip install ipapy
COPY generate_espeak-ng_import.py $BASEDIR

FROM py-base as py-parse
ARG BASEDIR
WORKDIR $BASEDIR

CMD echo 'Downloading wiktionary file...\n' ; \
wget https://dumps.wikimedia.org/dewiktionary/latest/dewiktionary-latest-pages-articles.xml.bz2 ; \
echo 'Extracting wiktionary file...\n' ; \
bunzip2 -d dewiktionary-latest-pages-articles.xml.bz2 ; \
echo 'Parsing wiktionary file, generating espeak-ng import file...\n' ; \
python generate_espeak-ng_import.py -i dewiktionary-latest-pages-articles.xml -o /wik_out/
