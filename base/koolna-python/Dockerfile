FROM ghcr.io/buvis/koolna-base:latest@sha256:296591719c075273cd530112c0bf23a8e8e6aa4ef0bdb6421f538b9822ab215f

ARG USERNAME=bob

ENV HOME=/home/$USERNAME

USER $USERNAME

COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

RUN bash -c 'eval "$(mise activate bash)" && mise install'

CMD ["sh", "-c", "exec sleep infinity"]
