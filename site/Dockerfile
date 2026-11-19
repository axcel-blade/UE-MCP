# syntax=docker/dockerfile:1

# --- build ---
FROM node:22-alpine AS build
WORKDIR /app

RUN corepack enable && corepack prepare pnpm@10.15.1 --activate

COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .

# Docker local default: site at http://localhost:8080/
# Pass ASTRO_BASE=/UE-MCP for GitHub Pages path parity.
ARG ASTRO_SITE=http://localhost:8080
ARG ASTRO_BASE=/
ENV ASTRO_SITE=$ASTRO_SITE \
    ASTRO_BASE=$ASTRO_BASE

RUN pnpm build

# --- runtime ---
FROM nginx:1.27-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1

CMD ["nginx", "-g", "daemon off;"]
