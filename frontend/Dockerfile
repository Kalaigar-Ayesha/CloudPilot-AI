# Stage 1: Build React static bundle assets
FROM node:20-alpine AS builder

WORKDIR /build

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build


# Stage 2: Serve compiled web pages via Nginx
FROM nginx:1.25-alpine

COPY --from=builder /build/dist /usr/share/nginx/html

# Copy custom nginx configuration for routing fallbacks
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost || exit 1

CMD ["nginx", "-g", "daemon off;"]
