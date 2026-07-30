# --- ETAPA 1: Construcción ---
FROM golang:1.25.5-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o mi-backend ./cmd/api

# --- ETAPA 2: Ejecución ---
FROM alpine:3.20

WORKDIR /app
RUN apk add --no-cache ca-certificates


RUN adduser -D -g '' appuser

COPY --from=builder --chown=appuser:appuser /app/mi-backend .
RUN chmod +x ./mi-backend

USER appuser

EXPOSE 8080

CMD ["./mi-backend"]