FROM node:20-alpine AS build

WORKDIR /app

COPY kusor-ui/package*.json ./
RUN npm ci --legacy-peer-deps

COPY kusor-ui/ ./
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist/kusor-ui/browser /usr/share/nginx/html
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
