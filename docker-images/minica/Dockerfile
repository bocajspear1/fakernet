FROM alpine:3.10

WORKDIR /ca

RUN apk add openssl go git make build-base
RUN git clone https://github.com/bocajspear1/minica.git
RUN cd minica && make 

ENV DOMAIN 'ca.fake'
ENV PORT 443

CMD cd /ca/minica;./minica ${DOMAIN} ${PORT}