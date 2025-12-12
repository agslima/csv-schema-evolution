# Stage 1: Nginx Runtime
FROM nginx:alpine

# Remove default Nginx website
RUN rm -rf /usr/share/nginx/html/*

# Copy Static Assets
COPY . /usr/share/nginx/html

# Copy Custom Nginx Configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose HTTP Port
EXPOSE 80

# Start Nginx in foreground
CMD ["nginx", "-g", "daemon off;"]