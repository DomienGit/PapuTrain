# Obraz frontendu PapuTrain — dwa etapy (multi-stage):
# 1. build: node buduje produkcyjną paczkę Vite (katalog dist/)
# 2. serve: nginx serwuje statyczne pliki (lekki, ~50 MB)
# Od świata (TLS) chroni Caddy — ten nginx działa tylko w sieci compose.
FROM node:22-alpine AS build
WORKDIR /app

# Najpierw manifesty zależności — warstwa cache'owana do zmiany package.json.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
