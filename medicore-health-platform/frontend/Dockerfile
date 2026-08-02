# Multi-stage build. `docker build --target dev` gives a hot-reloading Vite
# dev server for docker-compose; the default (no --target) final stage
# builds static assets and serves them with nginx, for use in Kubernetes.

FROM node:20-alpine AS base
WORKDIR /app
COPY package*.json ./
RUN npm install

# ---- dev: used by docker-compose for local hot-reload ----
FROM base AS dev
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ---- build: compiles static assets ----
FROM base AS build
COPY . .
RUN npm install
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# ---- production: nginx serving the compiled SPA ----
FROM nginx:1.27-alpine AS production
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
RUN adduser -D -H -u 1000 appuser && \
    chown -R appuser /usr/share/nginx/html /var/cache/nginx /var/run /var/log/nginx && \
    touch /var/run/nginx.pid && chown appuser /var/run/nginx.pid
USER appuser
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD wget -q --spider http://localhost:8080/ || exit 1
CMD ["nginx", "-g", "daemon off;"]
