FROM nikolaik/python-nodejs:python3.11-nodejs19

# ✅ FIX: Remove Yarn repo (GPG error fix)
RUN rm -f /etc/apt/sources.list.d/yarn.list && \
    rm -f /etc/apt/trusted.gpg.d/yarn.gpg && \
    sed -i 's|http://deb.debian.org/debian|http://archive.debian.org/debian|g' /etc/apt/sources.list && \
    sed -i '/security.debian.org/d' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg aria2 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy App Files
COPY . /app/
WORKDIR /app/

# Upgrade pip
RUN python -m pip install --no-cache-dir --upgrade pip

# Install Requirements
RUN pip3 install --no-cache-dir --upgrade -r requirements.txt

# Start Bot
CMD bash start
