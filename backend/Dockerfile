#1 image base
FROM golang:1.25.5-alpine


#2 Directorio dentro del contenedor
WORKDIR /app

#3 Copia de las dependenccias
COPY go.mod go.sum ./
 

#4 Descargar paquetes usados en el proyecto
RUN go mod download

#5 Copiar el resto del codigo
COPY . .

#Exponer el puerto 
EXPOSE 8080

#
RUN go build -o mi-backend ./cmd/api

CMD ["./mi-backend"] 
