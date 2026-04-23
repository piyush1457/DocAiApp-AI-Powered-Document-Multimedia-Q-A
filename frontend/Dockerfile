# Stage 1: Build stage
FROM node:20-alpine as builder

WORKDIR /app

# Install dependencies using clean install
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Build the application (Vite outputs to /dist by default)
RUN npm run build

# Stage 2: Production serve stage
FROM nginx:alpine

# Copy the build output from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy the custom nginx configuration
# This simple config handles SPA routing and basic proxying
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Security: Adjust permissions to run as non-root
RUN touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx/conf.d && \
    chown -R nginx:nginx /usr/share/nginx/html

# Switch to the non-root 'nginx' user
USER nginx

EXPOSE 80

# Health check to ensure nginx is serving
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget -qO- http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
