# Use official Python image
FROM python:3.11-slim

# Set environment vars
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work dir
WORKDIR /

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project files
COPY . .

EXPOSE 8000

# Run migrations and start dev server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
