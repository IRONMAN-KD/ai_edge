# Use a lightweight Nginx image to serve the built files
FROM nginx:alpine

# Remove the default Nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy the custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the pre-built files directly
COPY dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# The default command for Nginx is to run in the foreground, which is correct for Docker.
# No CMD needed here. 