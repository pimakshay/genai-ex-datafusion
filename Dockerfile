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

# set the working directory to /datafusion/ai
WORKDIR $HOME/datafusion/ai

# start FASTAPI App on port 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

