FROM alpine/git@sha256:29cff25811f790b9f72fc266bf8009a5a911714c0e03c31c47339c50909d9aef

COPY clone.sh /clone.sh
COPY bootstrap.sh /bootstrap.sh
RUN chmod +x /clone.sh /bootstrap.sh

ENTRYPOINT ["/clone.sh"]
