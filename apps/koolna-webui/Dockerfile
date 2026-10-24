FROM node:24-alpine@sha256:06d7adf3e0ef61a13f1d28682726366f97a15aa1888c934d3ecec86c33918b53 AS frontend

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

FROM golang:1.27-alpine@sha256:b8c9b82affbbb82a020bbcf998dad2ba9516944ac7e883524642a481a9505e9c AS backend

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY *.go ./
COPY handlers/ handlers/
COPY k8s/ k8s/

ENV CGO_ENABLED=0
RUN go build -ldflags='-s -w' -o koolna-webui .

FROM gcr.io/distroless/static:nonroot@sha256:18f4cc26c9ffa7f20a359298be7deadac5c607c8e03a02b8119f1a5fc2f82c99

WORKDIR /app

COPY --from=backend /app/koolna-webui /app/koolna-webui
COPY --from=frontend /app/frontend/dist /app/frontend/dist

USER nonroot:nonroot

EXPOSE 8080

ENTRYPOINT ["/app/koolna-webui"]
