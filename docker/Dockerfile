FROM ubuntu:16.04

ARG BOOBANK_SITE
ARG BOOBANK_CPT1
ARG BOOBANK_CPT1_PASS

RUN echo "Modifier la version pour forcer la recréation de l'image docker: V1.01"

RUN apt-get update && \
    apt-get install -y weboob && \
    apt-get install -y python-pip && \
    apt-get install -y firefox xvfb && \
    apt-get install -y wget && \
    pip install --upgrade pip && \
    pip install selenium && \
    pip install pyvirtualdisplay && \
    apt-get purge -y firefox && \
    cd /tmp && \
    wget http://ufpr.dl.sourceforge.net/project/ubuntuzilla/mozilla/apt/pool/main/f/firefox-mozilla-build/firefox-mozilla-build_45.0.2-0ubuntu1_amd64.deb && \
    dpkg -i firefox-mozilla-build_45.0.2-0ubuntu1_amd64.deb && \
    apt-mark hold firefox && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
    
COPY boobank.py /usr/lib/python2.7/dist-packages/weboob/applications/boobank/

COPY console.py /usr/lib/python2.7/dist-packages/weboob/tools/application/

RUN rm /usr/lib/python2.7/dist-packages/weboob/applications/boobank/boobank.pyc && \
    cd /usr/lib/python2.7/dist-packages/weboob/applications/boobank/ && \
    python -m compileall boobank.py

RUN rm /usr/lib/python2.7/dist-packages/weboob/tools/application/console.pyc && \
    cd /usr/lib/python2.7/dist-packages/weboob/tools/application/ && \
    python -m compileall console.py

RUN weboob-config add cragr website=$BOOBANK_SITE login=$BOOBANK_CPT1 password=$BOOBANK_CPT1_PASS

COPY browser.py /root/.local/share/weboob/modules/1.1/cragr/web/
COPY pages.py /root/.local/share/weboob/modules/1.1/cragr/web/
COPY module.py /root/.local/share/weboob/modules/1.1/cragr/
