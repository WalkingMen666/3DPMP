# Target Base Image: ubuntu:25.04 (Plucky Puffin) as per version.md
FROM ubuntu:25.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Update package lists and install system dependencies
# - python3: Python 3.13 (default in 25.04)
# - python3-pip, python3-venv: For managing python packages
# - prusa-slicer: The slicing engine
# - libgl1-mesa-glx: Often needed for GUI apps/slicers even in CLI mode (though prusa-slicer-console might be fine, safer to include)
# - git: For version control if needed
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    prusa-slicer \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create a virtual environment to avoid conflicts with system python packages
# Although version.md says "Use default system packages (apt) where possible", 
# it also says "Python Dependencies (Pip) Managed by requirements.txt".
# Using a venv is best practice even inside docker.
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy requirements file
# (We will create a placeholder requirements.txt next)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Expose the port Django runs on
EXPOSE 8000

# Default command (can be overridden in docker-compose)
# Using gunicorn or python manage.py runserver for dev
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
