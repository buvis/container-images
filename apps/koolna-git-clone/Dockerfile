FROM alpine/git@sha256:77418e6e7c7f434c4a98eaff04ef16840cf03649c881c03948e3e213923e3136

COPY clone.sh /clone.sh
COPY bootstrap.sh /bootstrap.sh
RUN chmod +x /clone.sh /bootstrap.sh

ENTRYPOINT ["/clone.sh"]
