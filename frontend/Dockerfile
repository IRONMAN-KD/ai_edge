# ---- Build Stage ----
# Use a Node.js image to build the Vue application
FROM node:18.19.0 AS builder

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json to leverage Docker cache
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Build the application for production
RUN npm run build

# ---- Serve Stage ----
# Use a lightweight Nginx image to serve the built files
FROM nginx:1.25.3

# Remove the default Nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy the custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the built files from the build stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# The default command for Nginx is to run in the foreground, which is correct for Docker.
# No CMD needed here. 