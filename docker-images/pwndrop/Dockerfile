FROM alpine:3.13

WORKDIR /

RUN apk add openssl go git make build-base
RUN git clone https://github.com/kgretzky/pwndrop.git
RUN cd pwndrop && make 
RUN mkdir -p /pwndrop/build/data
RUN mkdir -p /pwndrop/build/admin

CMD cd /pwndrop/build;./pwndrop -no-autocert -no-dns -config ./admin/config.ini