FROM alpine/git@sha256:6a1fdb962814ca11508ca8d1bab94375b5b7ac4e4a9a40981c29fc32c02f095d

COPY clone.sh /clone.sh
COPY bootstrap.sh /bootstrap.sh
RUN chmod +x /clone.sh /bootstrap.sh

ENTRYPOINT ["/clone.sh"]
