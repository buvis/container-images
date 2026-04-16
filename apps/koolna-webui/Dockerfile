FROM node:24-alpine@sha256:ff2c02f071f9e56778013b47d70f7524f5d4eacb032027f0f434838d77cf25e0 AS frontend

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

FROM golang:1.26-alpine@sha256:27f829349da645e287cb195a9921c106fc224eeebbdc33aeb0f4fca2382befa6 AS backend

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
