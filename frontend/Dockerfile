FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Configure NPM to use Taobao/npmmirror registry for faster installation
RUN npm config set registry https://registry.npmmirror.com/

# Install dependencies
RUN npm ci

# Copy the rest of the application
COPY . .

# Disable Next.js telemetry to prevent build hang
ENV NEXT_TELEMETRY_DISABLED=1

# Limit CPU workers and increase Node memory limit to prevent Docker build hangs/OOM on small servers
ENV NEXT_PRIVATE_WORKER_CPUS=1
ENV NODE_OPTIONS="--max-old-space-size=2048"

# Build the Next.js application
RUN npm run build

# Production stage
FROM node:20-alpine AS runner

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1

# Copy built assets from builder
COPY --from=builder /app/public ./public

# Automatically leverage output traces to reduce image size
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Expose port and start
EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
