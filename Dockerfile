FROM octoprint/octoprint:latest

RUN  mkdir -p /opt/octoprint/remtty

COPY OctoRemtty.py /opt/octoprint/remtty

RUN mkdir -p /etc/services.d/remtty

COPY remtty /etc/services.d/remtty
