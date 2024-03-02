# Use an official Node.js runtime as a parent image
FROM --platform=$BUILDPLATFORM node:20-slim AS node-build
ARG TARGETPLATFORM
ARG BUILDPLATFORM
RUN echo "I am running on $BUILDPLATFORM, building for $TARGETPLATFORM" > /log

# Set the working directory in the container to /app
WORKDIR /usr/src/app

# Copy the current directory contents into the container.
COPY ./ ./

# Install Python and aptitude package manager which we need to install chromium
RUN apt-get update && apt-get install -y \
python3 \
python3-pip \
python3.11-venv \
aptitude

# Install chromium and chromedriver dependencies
RUN aptitude install -y chromium-driver chromium

# Set up a virtual environment and install Python dependencies.
RUN python3 -m venv venv && . venv/bin/activate && pip3 install -r requirements.txt

# Create a new user 'appuser'.
RUN useradd -m appuser

# Change the ownership of the copied files to 'appuser'.
RUN chown -R appuser:appuser /usr/src/app

# Install backend dependencies
WORKDIR /usr/src/app/backend
RUN npm install

# Check if .env file exists and create it if it doesn't
RUN touch .env

RUN echo "\nCHROME_PATH=\"/usr/bin/chromium\"" >> .env && \
    echo "CHROMEDRIVER_PATH=\"/usr/bin/chromedriver\"" >> .env;

# Install frontend dependencies
WORKDIR /usr/src/app/frontend
RUN npm install
RUN npm run build

# Go back to /app directory
WORKDIR /usr/src/app

# Expose port 3000 for the frontend and 3010 for the APIs.
EXPOSE 3000 3010

# Switch to 'appuser'.
USER appuser

# Run supervisord on start.
CMD ["/bin/bash", "-c", "source venv/bin/activate && supervisord"]