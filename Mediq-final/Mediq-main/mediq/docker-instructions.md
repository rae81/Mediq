# Docker Instructions for MedIQ Project

## Overview
This document provides instructions for building and running the MedIQ Healthcare Appointment System using Docker.

## Prerequisites
- Docker installed on your system
- Docker Compose installed on your system

## Files
The Docker setup includes:
- `Dockerfile`: Defines the Docker image for the application
- `docker-compose.yml`: Configures the application service and volumes
- `.dockerignore`: Specifies files to exclude from the Docker build
- `requirements.txt`: Lists all Python dependencies

## Getting Started

### 1. Build and Start the Application
Navigate to the directory containing the `docker-compose.yml` file and run:

```bash
docker-compose up --build
```

This command will:
- Build the Docker image for the application
- Start the application container
- Set up the required volumes for static files and media

### 2. Access the Application
Once the containers are running, you can access the application at:
- Patient portal: http://localhost:8000/
- Admin panel: http://localhost:8000/admin/

### 3. Running Database Migrations
If you need to run migrations or create a superuser, you can use:

```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

### 4. Populating Initial Data
To seed the database with predefined doctors:

```bash
docker-compose exec web python manage.py populate_doctors
```

### 5. Environmental Variables
For production, modify the environment variables in the `docker-compose.yml` file:
- Replace the placeholder SECRET_KEY
- Update EMAIL_HOST_USER and EMAIL_HOST_PASSWORD
- Set DEBUG to False for production

## Stopping the Application

To stop the application, press `Ctrl+C` in the terminal running the containers, or run:

```bash
docker-compose down
```

To remove all data volumes as well:

```bash
docker-compose down -v
``` 