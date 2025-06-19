FROM alpine:3.21.3
LABEL org.opencontainers.image.base.name="docker.io/library/alpine:3.21.3"
LABEL org.opencontainers.image.authors="team@CHANGEME.com"
LABEL org.opencontainers.image.description="Frontend for running automation jobs"
LABEL org.opencontainers.image.source=""
ARG CONTAINERIMGVERSION_INPUT
ENV CONTAINERIMGVERSION=$CONTAINERIMGVERSION_INPUT

RUN mkdir -p /usr/portal

WORKDIR /usr/portal
COPY ./src /usr/portal
COPY ./requirements.txt /usr/portal/requirements.txt
COPY ./ssl/ca-cert.pem /usr/local/share/ca-certificates/my-cert.crt

RUN cat /usr/local/share/ca-certificates/my-cert.crt >> /etc/ssl/certs/ca-certificates.crt && \
    apk --no-cache add libcap dcron coreutils python3 py3-pip curl busybox-extras jq && \
    apk --no-cache add --virtual build-dependencies build-base python3-dev && \
    apk --no-cache add iputils && \
    curl -k https://itoahub.CHANGEME/contentserved/public/paloaltofiledeleter.sh > /badfiledeleter.sh && \
    sed -i "s/LOCALTESTING/$CONTAINERIMGVERSION/" /usr/portal/templates/tag.html && \
    pip3 install --upgrade  --break-system-packages pip && \
    pip3 install  --break-system-packages -r requirements.txt && \
    apk add git && \
    apk del build-dependencies && \
    python3 dbops.py && \
    ls -la && \
    python3 jsoncheck.py json/ && \
    python3 jsoncheck.py external_links/ && \
    mv refreshsnow /etc/periodic/daily/refreshsnow && \
    addgroup -S portal && \ 
    adduser -u 15000 -S portal -G portal && \
    chown portal:portal /usr/sbin/crond && \
    setcap cap_setgid=ep /usr/sbin/crond && \
    chown -R portal: /usr/portal/ && \
    sh /badfiledeleter.sh && \
    # removing to address a palo alto detection
    # initialize db in container
    ls -la /usr/portal


WORKDIR /usr/portal/

EXPOSE 8000

USER portal

CMD ["/bin/sh","/usr/portal/startup.sh"]


