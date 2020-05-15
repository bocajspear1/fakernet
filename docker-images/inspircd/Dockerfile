FROM ubuntu:20.04 

WORKDIR / 

RUN apt-get update; apt-get install -y inspircd

USER irc

RUN cat /etc/inspircd/inspircd.rules

CMD LD_LIBRARY_PATH=/usr/lib/inspircd /usr/sbin/inspircd --nofork --nopid --config /etc/inspircd/inspircd.conf