# Use an official Python runtime as a parent image
FROM python:3.10

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install django==3.2.7 'channels[daphne]' Pillow

# Copy the current directory contents into the container at /app
COPY . /app/

# Expose the port the application runs on
EXPOSE 8000

# Run the Django setup commands and start the development server
CMD python manage.py makemigrations && \
    python manage.py migrate && \
    python manage.py runserver 0.0.0.0:8000