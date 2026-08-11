FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    squid \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages redis==5.0.4

COPY squid/squid.conf /etc/squid/squid.conf
COPY squid/session_helper.py /usr/local/bin/session_helper.py
COPY squid/gelf_shipper.py /usr/local/bin/gelf_shipper.py
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /usr/local/bin/session_helper.py \
             /usr/local/bin/gelf_shipper.py \
             /entrypoint.sh

EXPOSE 3128

ENTRYPOINT ["/entrypoint.sh"]
