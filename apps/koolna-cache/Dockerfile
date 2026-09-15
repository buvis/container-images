FROM debian:trixie-slim@sha256:d7e12182ce18b85b93007c1dedf31f2d29e01ccf3182cc4017c709b6259bc132
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
