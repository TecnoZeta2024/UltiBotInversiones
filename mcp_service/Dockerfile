# MCP (Model Context Protocol) Server Dockerfile
# Based on doggybee/mcp-server-ccxt for UltiBotInversiones

# Use Node.js as base image for the MCP Server
FROM node:18-slim AS mcp-builder

WORKDIR /build

# Install necessary tools and dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-dev gcc g++ make \
    && rm -rf /var/lib/apt/lists/*

# Install basic packages
COPY mcp_service/package.json mcp_service/package-lock.json* ./
RUN npm ci

# Copy source files
COPY mcp_service/src ./src
COPY mcp_service/tsconfig.json ./
COPY mcp_service/.env* ./

# Build the project
RUN npm run build

# Production stage
FROM node:18-slim

# Install Python 3 dependencies (for CCXT)
RUN apt-get update && apt-get install -y \
    python3 python3-pip curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy built artifacts
COPY --from=mcp-builder /build/dist ./dist
COPY --from=mcp-builder /build/node_modules ./node_modules
COPY --from=mcp-builder /build/package.json ./
COPY --from=mcp-builder /build/.env* ./

# Setup MCP specific Python environment
COPY mcp_service/requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# Create log directory
RUN mkdir -p /app/logs && chmod 777 /app/logs

# Default environment variables
ENV NODE_ENV=production \
    PORT=3000

EXPOSE 3000

CMD ["node", "dist/index.js"]
