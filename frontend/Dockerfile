# Stage 1: Build the Next.js application
FROM node:18-alpine AS builder

WORKDIR /app/frontend

# Copy package.json and package-lock.json
COPY package.json package-lock.json ./

# Install dependencies
RUN npm install

# Copy the rest of the frontend application code
COPY . .

# Build the Next.js application
# The `output: 'standalone'` option in next.config.js is recommended for Docker
# It creates a folder with all necessary files including a standalone server
RUN npm run build

# Stage 2: Create the production image
FROM node:18-alpine AS runner

WORKDIR /app/frontend

# Copy the standalone output from the builder stage
COPY --from=builder /app/frontend/.next/standalone ./ 
COPY --from=builder /app/frontend/.next/static ./.next/static
COPY --from=builder /app/frontend/public ./public

# Set environment variables for Next.js
ENV NODE_ENV production
# NEXT_PUBLIC_API_URL will be set in docker-compose.yml

# Expose the port Next.js runs on
EXPOSE 3000

# Command to run the Next.js application
CMD ["node", "server.js"]
