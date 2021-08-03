FROM ubuntu:18.04

WORKDIR /opt/bepasty

RUN apt-get update
RUN apt-get install -y build-essential nginx python3-dev git-core python3-pip sudo ca-certificates

RUN useradd -d /opt/bepasty -s /bin/false bepasty
RUN git clone https://github.com/bepasty/bepasty-server.git /opt/bepasty/repo
RUN mkdir /opt/bepasty/storage; mkdir /opt/bepasty/logs;
RUN chown -R bepasty:bepasty /opt/bepasty
RUN chmod 755 /opt/bepasty
RUN cd repo && pip3 install -e .
RUN pip3 install greenlet
RUN pip3 install eventlet==0.30.2
RUN pip3 install gunicorn[eventlet]

COPY setup.sh /opt/bepasty/
COPY bepasty.conf.init /opt/bepasty/
COPY start_bepasty /opt/bepasty/

RUN chmod +x /opt/bepasty/start_bepasty

RUN rm /etc/nginx/sites-enabled/*
COPY nginx-bepasty.conf.init /etc/nginx/sites-enabled/

ENV DOMAIN 'bepasty.fake'

CMD  /bin/bash /opt/bepasty/setup.sh ${DOMAIN}; nginx; /opt/bepasty/start_bepasty