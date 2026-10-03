FROM debian:trixie-slim@sha256:a99cfc517144bc59b1978475ec53b46ecabec7e43635402ee5b77cc54cd1b20a
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
