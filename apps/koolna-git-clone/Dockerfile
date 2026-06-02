FROM alpine/git@sha256:8786a6a02273827d0aa039d174aacd5e017fcce9aba0af62596d991970cab01a

COPY clone.sh /clone.sh
COPY bootstrap.sh /bootstrap.sh
RUN chmod +x /clone.sh /bootstrap.sh

ENTRYPOINT ["/clone.sh"]
