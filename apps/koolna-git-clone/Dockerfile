FROM alpine/git@sha256:4f9488b7295baec153a9953479690f835ad4699b1d9f11e3897a4485c224fc3e

COPY clone.sh /clone.sh
COPY bootstrap.sh /bootstrap.sh
RUN chmod +x /clone.sh /bootstrap.sh

ENTRYPOINT ["/clone.sh"]
