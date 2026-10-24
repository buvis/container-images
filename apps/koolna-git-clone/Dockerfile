FROM alpine/git@sha256:4fac439ee3b9204bec99c712b8a15942999632458f716ae8149fbb97cb760cd4

COPY clone.sh /clone.sh
COPY bootstrap.sh /bootstrap.sh
RUN chmod +x /clone.sh /bootstrap.sh

ENTRYPOINT ["/clone.sh"]
