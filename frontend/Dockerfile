# Build Stage
FROM node:22 AS builder

WORKDIR /app

# Copy package definition files
COPY package*.json ./

# Install dependencies
# Note: We assume package-lock.json exists, if not, this might warn but proceed with package.json
RUN npm install

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production Stage
FROM nginx:1.26

# Copy build artifacts from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
