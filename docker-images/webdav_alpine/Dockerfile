FROM alpine:3.10

WORKDIR /webdav

RUN apk add apache2 apache2-webdav apr-util-dbm_db apache2-ssl apache2-utils ca-certificates
RUN rm /etc/apache2/conf.d/dav.conf 
RUN rm /etc/apache2/conf.d/userdir.conf 

# Setup file directories
RUN mkdir mkdir /var/www/localhost/htdocs/files/
RUN mkdir mkdir /var/www/localhost/htdocs/files/public
RUN chown -R /var/www/localhost/htdocs

# Dir for locks
RUN mkdir /var/lib/dav
RUN chown apache:apache /var/lib/dav
RUN chmod 755 /var/lib/dav

COPY setup.sh /webdav/
COPY davserver.conf /etc/apache2/conf.d/davserver.conf
COPY ssl.conf /etc/apache2/conf.d/ssl.conf
COPY index.html /var/www/localhost/htdocs/index.html

ENV DOMAIN 'webdav.fake'

CMD  /bin/ash /webdav/setup.sh ${DOMAIN}; /usr/sbin/apachectl -DFOREGROUND