FROM python:3-alpine
MAINTAINER Carolina Galvão <carolina.santos_datainfo@inpe.br> 

# Install dependencies
RUN apk update
RUN apk add --no-cache gcc musl-dev mariadb-dev

# Prepare work directory
RUN mkdir -p /usr/src/osapp
WORKDIR /usr/src/osapp

# Get opensearch source and install python requirements
COPY requirements.txt /usr/src/osapp
RUN pip install -r requirements.txt

# Setting environment variables
ENV PYTHONUNBUFFERED 1

# Expose the Flask port
EXPOSE 5002

# Run the opensearch application
CMD [ "python3", "wsgi.py" ]