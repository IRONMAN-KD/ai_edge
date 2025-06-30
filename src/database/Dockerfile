FROM arm64v8/mysql:8.0

# Copy the SQL initialization script directly into the entrypoint directory.
# The official entrypoint script will automatically execute any .sh or .sql file
# in this directory after the database server is ready, which is more robust
# than using a custom shell script wrapper.
COPY init.sql /docker-entrypoint-initdb.d/ 