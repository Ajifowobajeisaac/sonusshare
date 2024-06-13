# Use the official Python image as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Collect the static files
RUN python manage.py collectstatic --no-input

# Expose the port that the Django app will run on
EXPOSE $PORT

# Set the command to run the Django app
CMD gunicorn sonoshareweb.wsgi --bind 0.0.0.0:$PORT --limit-request-line 8192
