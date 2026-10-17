FROM debian:trixie-slim@sha256:a29215f6a35e51e22adffa17f89e9d2ef06214e64a2bad10d765c46aea49f11f
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
