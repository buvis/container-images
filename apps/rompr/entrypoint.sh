#!/usr/bin/env bash
rm /run/nginx.pid
set -e

PHP_VERSION=$(php -v | head -n 1 | tail -n 1 | cut -d " " -f 2 | cut -c 1-3)

/etc/init.d/php${PHP_VERSION}-fpm restart
exec /usr/sbin/nginx -g 'daemon off;'
