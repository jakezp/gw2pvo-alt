FROM alpine:3.12

RUN apk add --no-cache python3 libffi openssl tzdata bash gcc g++ python3-dev libffi-dev openssl-dev && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache && \
    pip install paho-mqtt python-telegram-bot && \
    pip install https://github.com/sffjunkie/astral/archive/1.10.1.tar.gz && \
    pip install https://github.com/jakezp/gw2pvo-alt/raw/main/dist/gw2pvo-1.5.0-alt.tar.gz

ENTRYPOINT exec /usr/bin/gw2pvo --config gw2pvo.cfg
