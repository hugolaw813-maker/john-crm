FROM node:20-alpine AS base

# Install pnpm
RUN corepack enable && corepack prepare pnpm@9.15.0 --activate

# ─── Stage 1: Install dependencies ───────────────────────────────────
FROM base AS deps
WORKDIR /app

COPY package.json pnpm-workspace.yaml pnpm-lock.yaml* ./
COPY apps/web/package.json ./apps/web/
COPY packages/shared/package.json ./packages/shared/

RUN pnpm install --frozen-lockfile || pnpm install

# ─── Stage 2: Build the application ──────────────────────────────────
FROM base AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/apps/web/node_modules ./apps/web/node_modules
RUN mkdir -p ./packages/shared/node_modules
COPY --from=deps /app/packages/shared/node_modules ./packages/shared/node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_OUTPUT=standalone
ARG DATABASE_URL=postgresql://postgres:postgres@db:5432/openclaw
ARG NEXT_PUBLIC_APP_URL=http://localhost:3000
ARG BETTER_AUTH_SECRET=change-me-to-a-random-secret-at-least-32-chars
ARG GITHUB_CLIENT_ID=
ARG GITHUB_CLIENT_SECRET=
ARG GOOGLE_CLIENT_ID=
ARG GOOGLE_CLIENT_SECRET=
ENV DATABASE_URL=${DATABASE_URL}
ENV NEXT_PUBLIC_APP_URL=${NEXT_PUBLIC_APP_URL}
ENV BETTER_AUTH_SECRET=${BETTER_AUTH_SECRET}
ENV GITHUB_CLIENT_ID=${GITHUB_CLIENT_ID}
ENV GITHUB_CLIENT_SECRET=${GITHUB_CLIENT_SECRET}
ENV GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
ENV GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}

# Build shared package first, then web app
RUN pnpm --filter @openclaw-crm/shared build && \
    pnpm --filter @openclaw-crm/web build

# ─── Stage 3: Production runner ──────────────────────────────────────
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy standalone build output
COPY --from=builder /app/apps/web/public ./apps/web/public
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/static ./apps/web/.next/static

# Copy drizzle config and schema for db:push at startup
COPY --from=builder /app/apps/web/drizzle.config.ts ./apps/web/
COPY --from=builder /app/apps/web/src/db ./apps/web/src/db
COPY --from=builder /app/packages/shared ./packages/shared

# Copy app content for runtime access (sitemap, dynamic pages)
COPY --from=builder /app/apps/web/content ./apps/web/content

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "apps/web/server.js"]
