FROM alpine:3.10

WORKDIR /mail

RUN apk add postfix postfix-sqlite ca-certificates dovecot dovecot-sqlite dovecot-lmtpd sqlite 
RUN apk add apache2 apache2-ssl php7-apache2 php7-iconv php7-curl php7-json php7-xml php7-dom php7-pdo_sqlite php7-mbstring php7-openssl php7-zip php7-pspell php7-fileinfo php7-sockets php7-session
# Backup the packaged postfix-files file, as we need this later
RUN cp /etc/postfix/postfix-files /mail/postfix-files 
RUN cp -r /etc/postfix/dynamicmaps.cf.d /mail/dynamicmaps.cf.d
# Clear out the config directory, we will be mounting and filling those with volumes
RUN rm -rf /etc/postfix/*
RUN rm -rf /etc/dovecot/*

# Roundcube setup
RUN wget https://github.com/roundcube/roundcubemail/releases/download/1.3.9/roundcubemail-1.3.9-complete.tar.gz
RUN tar -zxv -C /var/www/localhost/htdocs/ -f roundcube*.tar.gz
RUN mv /var/www/localhost/htdocs/roundcube* /var/www/localhost/htdocs/roundcube
RUN chown -R apache:apache /var/www/localhost/htdocs/roundcube/temp
RUN chown -R apache:apache /var/www/localhost/htdocs/roundcube/logs

RUN mkdir -p /var/www/localhost/db/
RUN cat /var/www/localhost/htdocs/roundcube/SQL/sqlite.initial.sql | sqlite3 /var/www/localhost/db/roundcube.db
RUN chown -R apache:apache /var/www/localhost/db/
RUN chmod -R 775 /var/www/localhost/db/

RUN addgroup -S maildb
RUN addgroup apache maildb

COPY setup.sh /mail/

COPY apache/01-access.conf /etc/apache2/conf.d/01-access.conf
COPY apache/ssl.conf /etc/apache2/conf.d/ssl.conf

COPY apache/mini.min.css /var/www/localhost/htdocs/mini.min.css
COPY apache/newaccount.php /var/www/localhost/htdocs/newaccount.php
COPY apache/index.html /var/www/localhost/htdocs/index.html

ENV DOMAIN 'mail.fake'

CMD  /bin/ash /mail/setup.sh ${DOMAIN}; /usr/sbin/postfix start; /usr/sbin/dovecot; /usr/sbin/httpd; tail -f /var/log/dovecot.log