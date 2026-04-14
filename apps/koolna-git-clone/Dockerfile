FROM alpine/git@sha256:d453f54c83320412aa89c391b076930bd8569bc1012285e8c68ce2d4435826a3

COPY clone.sh /clone.sh
RUN chmod +x /clone.sh

ENTRYPOINT ["/clone.sh"]
