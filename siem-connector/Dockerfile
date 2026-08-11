# Image Logstash open source (OSS, licence Apache 2.0), sans les modules
# proprietaires Elastic (X-Pack). Pipeline unique : reception GELF depuis
# Graylog, reformatage CEF, envoi vers Sekoia en syslog/TLS.
FROM docker.elastic.co/logstash/logstash-oss:8.14.3

USER root
COPY pipeline/ /usr/share/logstash/pipeline/
COPY config/logstash.yml /usr/share/logstash/config/logstash.yml
COPY config/pipelines.yml /usr/share/logstash/config/pipelines.yml

# Le codec CEF n'est pas inclus par defaut dans l'image OSS -> installation
# du plugin communautaire officiel (open source, maintenu par Elastic).
RUN /usr/share/logstash/bin/logstash-plugin install logstash-codec-cef

USER logstash
