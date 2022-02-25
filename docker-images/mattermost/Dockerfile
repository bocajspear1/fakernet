FROM alpine:3.15
RUN apk add mysql mysql-client ca-certificates curl jq libcap wget libc6-compat

RUN wget https://releases.mattermost.com/6.4.0/mattermost-team-6.4.0-linux-amd64.tar.gz 

RUN tar -zxf mattermost-team-*-linux-amd64.tar.gz

RUN mkdir -p /mattermost/data /mattermost/plugins /mattermost/client/plugins /mattermost/config /mattermost/logs

RUN addgroup mattermost
RUN adduser -D -G mattermost -h /mattermost mattermost

RUN rm -rf /mattermost/config/config.json
RUN rm /mattermost-team-*-linux-amd64.tar.gz
RUN chmod 777 -R /mattermost  

COPY config.json.init /

RUN setcap cap_net_bind_service=+ep /mattermost/bin/mattermost
COPY entrypoint.sh /
RUN chmod +x /entrypoint.sh
WORKDIR /mattermost
RUN ls -la /mattermost
ENTRYPOINT /entrypoint.sh