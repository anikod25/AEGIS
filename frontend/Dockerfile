# Stage 1: build the React app
FROM node:22-alpine AS build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci --prefer-offline
COPY frontend/ ./
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# Stage 2: export the built dist to the shared volume
FROM busybox:1.36
COPY --from=build /app/dist /dist
CMD ["sh", "-c", "cp -r /dist/. /output/"]
