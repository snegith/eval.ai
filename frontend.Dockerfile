# Build stage
FROM node:18-alpine as build
WORKDIR /app

# Copy package and install dependencies
COPY frontend/package*.json ./
RUN npm install

# Copy all frontend code
COPY frontend/ .

# Build the Vite project
RUN npm run build

# Serve stage
FROM nginx:alpine
# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy build artifacts to NGINX
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
