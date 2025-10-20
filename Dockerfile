FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install --production

# Copy application files
COPY server.js ./
COPY public/ ./public/

# Create workspace directories
RUN mkdir -p /workspace/config /workspace/prompts /workspace/analysis /workspace/uploads && \
    chmod -R 755 /workspace

EXPOSE 8888

ENV NODE_ENV=production
ENV PORT=8888

CMD ["node", "server.js"]
