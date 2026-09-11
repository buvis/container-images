FROM alpine/git@sha256:6f3b5029566da8e90b24945933dcd806be866b64b1e706f51828bf84faccf21b

COPY clone.sh /clone.sh
COPY bootstrap.sh /bootstrap.sh
RUN chmod +x /clone.sh /bootstrap.sh

ENTRYPOINT ["/clone.sh"]
