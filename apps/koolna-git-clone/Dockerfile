FROM alpine/git@sha256:ce84fd6a057b4dc5cf5009da2dd832f1c6d096c1984bf50496cf3c256402264d

COPY clone.sh /clone.sh
COPY bootstrap.sh /bootstrap.sh
RUN chmod +x /clone.sh /bootstrap.sh

ENTRYPOINT ["/clone.sh"]
