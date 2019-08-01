FROM alpine:3.10

WORKDIR /mail

RUN apk add postfix postfix-sqlite ca-certificates dovecot dovecot-sqlite sqlite
# Backup the packaged postfix-files file, as we need this later
RUN cp /etc/postfix/postfix-files /mail/postfix-files 
# Clear out the config directory, we will be mounting and filling those with volumes
RUN rm -rf /etc/postfix/*
RUN rm -rf /etc/dovecot/*

COPY setup.sh /mail/

CMD  /bin/ash /mail/setup.sh; /usr/sbin/postfix start; /usr/sbin/dovecot; tail -F /var/log/messages