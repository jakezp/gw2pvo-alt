FROM alpine:3.12

RUN apk add --no-cache python3 tzdata bash && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache && \
    pip install paho-mqtt && \
    pip install https://github.com/sffjunkie/astral/archive/1.10.1.tar.gz && \
    pip install https://github.com/jakezp/gw2pvo-alt/raw/main/dist/gw2pvo-1.4.3-alt.tar.gz

ENTRYPOINT exec /usr/bin/gw2pvo --config gw2pvo.cfg --pvo-interval 5 --log info --skip-offline
