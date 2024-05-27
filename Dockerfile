# Use Ubuntu 20.04 as a parent image
FROM ubuntu:20.04

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Set the working directory in the container
WORKDIR /usr/src/app

# Install Python, MySQL and other necessary system libraries
RUN apt-get update && apt-get install -y \
    python3.8 \
    python3-pip \
    mysql-server-8.0 \
    libdbus-glib-1-dev \
    libmysqlclient-dev \
    git \
    libgirepository1.0-dev \
    python3-dbus \
    python3-gi \
    python3-apt \
    # Add any other system packages you need here
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the requirements.txt into the container at /usr/src/app
COPY requirements.txt .

# Install Python packages
RUN pip3 install --no-cache-dir -r requirements.txt

# Optional: Set up the MySQL database
# RUN service mysql start && \
#     mysql -e "create database mydb;" && \
#     mysql -e "CREATE USER 'zchef'@'localhost' IDENTIFIED BY 'cooking';" && \
#     mysql -e "GRANT ALL PRIVILEGES ON mydb.* TO 'zchef'@'localhost';"

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV NAME World

# Run app.py when the container launches (if your app is a Python app)
# CMD ["python3", "app.py"]
