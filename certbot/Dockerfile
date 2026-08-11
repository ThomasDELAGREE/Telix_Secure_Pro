FROM certbot/certbot:v3.1.0

COPY entrypoint.sh /entrypoint.sh
USER root
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
