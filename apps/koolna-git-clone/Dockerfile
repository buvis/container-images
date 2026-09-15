FROM alpine/git@sha256:0b5f57d22181e8b8fbe8ac5ca8754faa0d577f101b9857418f1acc43955ad464

COPY clone.sh /clone.sh
COPY bootstrap.sh /bootstrap.sh
RUN chmod +x /clone.sh /bootstrap.sh

ENTRYPOINT ["/clone.sh"]
