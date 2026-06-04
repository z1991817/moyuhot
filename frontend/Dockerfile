FROM node:22-alpine AS build

WORKDIR /app

ARG API_BASE=http://api:8000/api
ARG PUBLIC_SITE_URL=https://moyuhot.com
ENV API_BASE=$API_BASE
ENV PUBLIC_SITE_URL=$PUBLIC_SITE_URL

RUN corepack enable && corepack prepare pnpm@10.33.1 --activate

COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .
RUN pnpm build

FROM node:22-alpine

WORKDIR /app

ENV HOST=0.0.0.0
ENV PORT=4321
ENV API_BASE=http://api:8000/api
ENV PUBLIC_SITE_URL=https://moyuhot.com

COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./package.json

EXPOSE 4321

CMD ["node", "dist/server/entry.mjs"]
