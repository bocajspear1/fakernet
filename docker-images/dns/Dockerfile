FROM alpine:3.10

WORKDIR / 

RUN apk add bind bind-tools

EXPOSE 53/udp 53/tcp

CMD rndc-confgen -a -u named && named -4 -u named -g -c /etc/bind/named.conf