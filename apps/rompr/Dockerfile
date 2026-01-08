# hadolint ignore=DL3007
FROM ghcr.io/buvis/debian-slim:latest

ARG VERSION

USER root

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV HOME=/app

# Install prerequisites
# hadolint ignore=DL3008,DL3015,SC2086
RUN \
  apt-get update \
  && apt-get install -y apt-transport-https \
  && apt-get update \
  && apt-get install -y --no-install-recommends \
  curl \
  imagemagick \
  nginx \
  php-curl \
  php-fpm \
  php-gd \
  php-json \
  php-mbstring \
  php-mysql \
  php-sqlite3 \
  php-xml \
  unzip \
  && apt-get autoremove -y \
  && apt-get clean -y \
  && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* ~/.cache

# Get latest rompr release
# hadolint ignore=DL3008,DL3015,SC2086
RUN \
  curl -k -L -o rompr.zip https://github.com/fatg3erman/RompR/releases/download/${VERSION}/rompr-${VERSION}.zip \
  && unzip -d /app rompr.zip \
  && rm rompr.zip \
  && mkdir /app/rompr/{prefs,albumart} \
  && chown -R www-data:www-data /app \
  && printf "umask %d" "${UMASK}" >> /etc/bash.bashrc

# Configure web server
RUN \
  mkdir -p /run/php \
  && PHP_VERSION=$(php -v | head -n 1 | tail -n 1 | cut -d " " -f 2 | cut -c 1-3) \
  && sed -ri -e  's/^allow_url_fopen =.*/allow_url_fopen = On/g' /etc/php/${PHP_VERSION}/fpm/php.ini \
  && sed -ri -e  's/^memory_limit =.*/memory_limit = 128M/g' /etc/php/${PHP_VERSION}/fpm/php.ini \
  && sed -ri -e  's/^max_execution_time =.*/max_execution_time = 1800/g' /etc/php/${PHP_VERSION}/fpm/php.ini \
  && sed -ri -e  's/^post_max_size =.*/post_max_size = 256M/g' /etc/php/${PHP_VERSION}/fpm/php.ini \
  && sed -ri -e  's/^upload_max_filesize =.*/upload_max_filesize = 8M/g' /etc/php/${PHP_VERSION}/fpm/php.ini \
  && sed -ri -e  's/^max_file_uploads =.*/max_file_uploads = 50/g' /etc/php/${PHP_VERSION}/fpm/php.ini \
  && sed -ri -e  's/^display_errors =.*/display_errors = On/g' /etc/php/${PHP_VERSION}/fpm/php.ini \
  && sed -ri -e  's/^display_startup_errors =.*/display_startup_errors = On/g' /etc/php/${PHP_VERSION}/fpm/php.ini \
  && echo "<?php phpinfo(); ?>" > /app/rompr/phpinfo.php \
  && update-rc.d php${PHP_VERSION}-fpm defaults

# Switch to app directory
WORKDIR "/app"

# Open the ports
EXPOSE 8123

# Create volumes
VOLUME ["/app"]

# Copy the configuration and scripts
COPY ./config/nginx_default /etc/nginx/sites-available/default
COPY ./entrypoint.sh /entrypoint.sh

# Start rompr
CMD ["/entrypoint.sh"]

LABEL \
  org.opencontainers.image.title="Rompr" \
  org.opencontainers.image.source="https://github.com/buvis/container-images/tree/main/apps/rompr" \
  org.opencontainers.image.version="${VERSION}"
