FROM node:22-alpine AS frontend

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

FROM golang:1.25-alpine AS backend

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY *.go ./
COPY handlers/ handlers/
COPY k8s/ k8s/

ENV CGO_ENABLED=0
RUN go build -ldflags='-s -w' -o koolna-webui .

FROM gcr.io/distroless/static:nonroot

WORKDIR /app

COPY --from=backend /app/koolna-webui /app/koolna-webui
COPY --from=frontend /app/frontend/dist /app/frontend/dist

USER nonroot:nonroot

EXPOSE 8080

ENTRYPOINT ["/app/koolna-webui"]
