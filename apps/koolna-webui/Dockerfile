FROM node:24-alpine@sha256:d1b3b4da11eefd5941e7f0b9cf17783fc99d9c6fc34884a665f40a06dbdfc94f AS frontend

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

FROM golang:1.26-alpine@sha256:91eda9776261207ea25fd06b5b7fed8d397dd2c0a283e77f2ab6e91bfa71079d AS backend

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY *.go ./
COPY handlers/ handlers/
COPY k8s/ k8s/

ENV CGO_ENABLED=0
RUN go build -ldflags='-s -w' -o koolna-webui .

FROM gcr.io/distroless/static:nonroot@sha256:e3f945647ffb95b5839c07038d64f9811adf17308b9121d8a2b87b6a22a80a39

WORKDIR /app

COPY --from=backend /app/koolna-webui /app/koolna-webui
COPY --from=frontend /app/frontend/dist /app/frontend/dist

USER nonroot:nonroot

EXPOSE 8080

ENTRYPOINT ["/app/koolna-webui"]
