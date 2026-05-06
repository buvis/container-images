FROM ghcr.io/buvis/koolna-base:latest@sha256:b4612ce17970262944a8514013c4961d28b0f23bc99a44b775f73dbf850c0733

ARG USERNAME=bob

ENV HOME=/home/$USERNAME

USER $USERNAME

COPY --chown=${USERNAME}:${USERNAME} assets/config/mise/config.toml /home/$USERNAME/.config/mise/config.toml

RUN bash -c 'eval "$(mise activate bash)" && mise install'

CMD ["sh", "-c", "exec sleep infinity"]
