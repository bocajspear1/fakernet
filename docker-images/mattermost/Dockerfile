# Copy from https://github.com/mattermost/mattermost-docker, modified due to docker-compose usage
FROM alpine:3.9

# Some ENV variables
ENV PATH="/mattermost/bin:${PATH}"
ENV MM_VERSION=5.13.2

# Build argument to set Mattermost edition
ARG edition=team
ARG PUID=2000
ARG PGID=2000
ARG MM_BINARY=

# Install some needed packages
RUN apk add --no-cache \
	ca-certificates \
	curl \
	jq \
	libc6-compat \
	libffi-dev \
	linux-headers \
	mailcap \
	netcat-openbsd \
	xmlsec-dev \
	tzdata \
	&& rm -rf /tmp/*

# Get Mattermost
RUN mkdir -p /mattermost/data /mattermost/plugins /mattermost/client/plugins /mattermost/config /mattermost/logs \
    && if [ ! -z "$MM_BINARY" ]; then curl $MM_BINARY | tar -xvz ; \
      elif [ "$edition" = "team" ] ; then curl https://releases.mattermost.com/$MM_VERSION/mattermost-team-$MM_VERSION-linux-amd64.tar.gz | tar -xvz ; \
      else curl https://releases.mattermost.com/$MM_VERSION/mattermost-$MM_VERSION-linux-amd64.tar.gz | tar -xvz ; fi \
    && cp /mattermost/config/config.json /config.json.save \
    && rm -rf /mattermost/config/config.json \
    && addgroup -g ${PGID} mattermost \
    && adduser -D -u ${PUID} -G mattermost -h /mattermost -D mattermost

RUN chown -R mattermost:mattermost /mattermost /config.json.save /mattermost/plugins /mattermost/client/plugins

# USER mattermost

RUN chmod +s /bin/su

RUN apk add postgresql postgresql-client nginx 
RUN su postgres -c 'initdb -D /var/lib/postgresql/11/data/'
RUN ls -la /var/lib/postgresql/11/data/
RUN addgroup mattermost postgres
RUN su postgres -c 'echo "local    mattermostdb    mattermost    peer" >> /var/lib/postgresql/11/data/pg_hba.conf'
RUN mkdir -p /run/postgresql/; chown postgres:postgres /run/postgresql/; chmod 770 /run/postgresql/
# RUN cp /usr/share/postgresql/postgresql.conf.sample /var/lib/postgresql/11/data/postgresql.conf

#Healthcheck to make sure container is ready
HEALTHCHECK CMD curl --fail http://localhost:8000 || exit 1

# Configure entrypoint and command
COPY entrypoint.sh /
COPY setup.sh /
COPY config.json /

WORKDIR /mattermost
CMD su postgres -c 'pg_ctl start --pgdata=/var/lib/postgresql/11/data/ -o "--data-directory=/var/lib/postgresql/11/data/"';  /bin/ash /setup.sh; nginx; su mattermost -c "/entrypoint.sh mattermost";
