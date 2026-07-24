FROM debian:trixie-slim@sha256:020c0d20b9880058cbe785a9db107156c3c75c2ac944a6aa7ab59f2add76a7bd
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
