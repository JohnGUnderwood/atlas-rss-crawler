FROM node:20

# Install dependencies.



# Install Python.
RUN apt-get install -y \
python3 \
python3-pip \
python3.11-venv
# libnss3 \
# libdbus-1-3 \
# libatk1.0-0 \
# libatk-bridge2.0-0 \
# libcups2 \
# libdrm2 \
# libatspi2.0-0 \
# libxcomposite1 \
# libxdamage1 \
# libxfixes3 \
# libxrandr2 \
# libgbm1 \
# libxkbcommon0 \
# libasound2 
# sudo

# Check available versions here: https://www.ubuntuupdates.org/package/google_chrome/stable/main/base/google-chrome-stable
# RUN wget --no-verbose -O /tmp/chrome.deb https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_${CHROME_VERSION}_amd64.deb \
#   && dpkg -i /tmp/chrome.deb || true \
#   && apt install -fy \
#   && rm /tmp/chrome.deb

# Create a new user 'appuser'.
RUN useradd -m appuser

# Set the working directory.
WORKDIR /usr/src/app

# Copy the current directory contents into the container.
COPY ./ ./

# Change the ownership of the copied files to 'appuser'.
RUN chown -R appuser:appuser /usr/src/app

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

# Change the ownership of the supervisord configuration file to 'appuser'.
RUN chown appuser:appuser /etc/supervisor/conf.d/supervisord.conf

# Expose port 3000 for the frontend and 3010 for the APIs.
EXPOSE 3000 3010

# Switch to 'appuser'.
USER appuser

# Run supervisord.
CMD ["/usr/bin/supervisord"]