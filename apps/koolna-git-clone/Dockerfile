FROM alpine/git@sha256:ae0f6f4bce38d2b8c40becc0d6241a08d9f57186ea03029de2189a2b5e722d94

COPY clone.sh /clone.sh
COPY bootstrap.sh /bootstrap.sh
RUN chmod +x /clone.sh /bootstrap.sh

ENTRYPOINT ["/clone.sh"]
