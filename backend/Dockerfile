FROM node:20-alpine

# Install bash, curl, jq for shell scripts
RUN apk add --no-cache bash curl jq

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy app files
COPY . .

# Create reports directory
RUN mkdir -p /app/reports

# Expose port
EXPOSE 4000

# Start development server
CMD ["npm", "run", "dev"]
