FROM debian:trixie-slim@sha256:4ffb3a1511099754cddc70eb1b12e50ffdb67619aa0ab6c13fcd800a78ef7c7a
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
  squid-openssl \
  ca-certificates \
  openssl \
  curl \
  && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /var/spool/squid /var/log/squid /etc/squid/ssl_cert \
  && chown -R proxy:proxy /var/spool/squid /var/log/squid /etc/squid/ssl_cert
COPY squid.conf /etc/squid/squid.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
EXPOSE 3128
ENTRYPOINT ["/entrypoint.sh"]
