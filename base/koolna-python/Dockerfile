FROM ghcr.io/buvis/koolna-base:latest@sha256:c9a14d3c09e0cedacb018f6a521d9291200c7d237deac0317f6ec797991bd90f

ARG USERNAME=bob

ENV HOME=/home/$USERNAME

USER $USERNAME

COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

RUN bash -c 'eval "$(mise activate bash)" && mise install'

CMD ["sh", "-c", "exec sleep infinity"]
