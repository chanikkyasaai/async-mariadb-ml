# Dockerfile for MariaDB
# This file allows you to run a local MariaDB instance for testing.

# Use the official MariaDB image
FROM mariadb:11.8.3

# Set environment variables for the database
# IMPORTANT: Replace these with your desired credentials.
# These will be used by the database server.
ENV MARIADB_ROOT_PASSWORD=root_password
ENV MARIADB_DATABASE=your_db
ENV MARIADB_USER=your_user
ENV MARIADB_PASSWORD=your_password

# Expose the default MariaDB port
EXPOSE 3306

# The entrypoint script in the base image will handle database initialization.
