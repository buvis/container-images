FROM node:24-alpine@sha256:50c8e8ca1d27439048670df5883f32d57cf81cff6233222c893fd0d9884cbd81 AS frontend

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

FROM golang:1.27-alpine@sha256:cf6fca6641884b8433441b2b0652976f975e1d0fdd26d177eaaf8596087f3125 AS backend

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY *.go ./
COPY handlers/ handlers/
COPY k8s/ k8s/

ENV CGO_ENABLED=0
RUN go build -ldflags='-s -w' -o koolna-webui .

FROM gcr.io/distroless/static:nonroot@sha256:e2e927ec666bae08560abb3c55d0659eceabb657f56b6782ab500a9fc7f555e3

WORKDIR /app

COPY --from=backend /app/koolna-webui /app/koolna-webui
COPY --from=frontend /app/frontend/dist /app/frontend/dist

USER nonroot:nonroot

EXPOSE 8080

ENTRYPOINT ["/app/koolna-webui"]
