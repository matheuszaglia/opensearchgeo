# INPE's OpenSearch

INPE's OpenSearch is a REST web service made in Flask for search and discovery of EO products produced by INPE.

# Setup Enviroment

## Cloning and installing dependencies on Ubuntu 16.04



The system dependencies are: 
python3-pip python3-dev virtualenv libmysqlclient-dev 

The pip requirements are: flask, mysqlclient, sqlalchemy and gunicorn (optional, used only for deployment)

The following commands will clone and install **all** the dependencies:
```bash
git clone http://github.com/mzaglia/opensearchgeo
cd opensearchgeo
./venv.sh
source venv/bin/activate
```

## Running the app

To run the app, make sure you have the following enviroment variables configured:
```
PYTHONUNBUFFERED=1
DB_PASS=<db_password>
DB_USER=<db_user>
DB_NAME=<db_name>
DB_HOST=<db_host>
BASE_URL=<base_service_url>
ENCLOSURE_BASE=<base_location_for_the_scenes_products>

```

# Deploy
For deployment you can follow: [How To Serve Flask Applications with Gunicorn and Nginx on Ubuntu 16.04 ](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-16-04)