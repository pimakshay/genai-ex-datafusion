# Use the official Python image from the Docker Hub
FROM python:3.12.4

# Set the working directory
WORKDIR /datafusion

# Copy the current directory contents into the container at /datafusion
COPY --chown=user ./requirements.txt /datafusion/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade -r /datafusion/requirements.txt

# Set up a new user named "user"
RUN useradd user

# Switch to the "user" user
USER user

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/datafusion

# copy the data to data
COPY --chown=user . $HOME/datafusion

# Make the start.sh script executable
RUN chmod +x $HOME/datafusion/start.sh

# Expose the necessary ports
EXPOSE 8000
EXPOSE 8001

# Use the start.sh script to run both FastAPI apps
CMD ["$HOME/datafusion/start.sh"]

