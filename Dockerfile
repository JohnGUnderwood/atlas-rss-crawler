FROM node:20

# Install Python.
RUN apt-get update && apt-get install -y python3 python3-pip python3.11-venv

# Set the working directory.
WORKDIR /usr/src/app

# Copy the current directory contents into the container.
COPY ./ ./

# Change to the 'frontend' directory.
WORKDIR /usr/src/app/frontend

# Install Node.js dependencies.
RUN npm install

# Build the Node.js app.
RUN npm run build

# Change back to the main directory.
WORKDIR /usr/src/app

# Set up a virtual environment and install Python dependencies.
RUN python3 -m venv venv && . venv/bin/activate && pip3 install -r requirements.txt

# Install supervisord.
RUN apt-get install -y supervisor

# Copy supervisord configuration file.
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose port 3000 for the frontend and 3010 for the APIs.
EXPOSE 3000 3010

# Run supervisord.
CMD ["/usr/bin/supervisord"]