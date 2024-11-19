#!/bin/bash
apt-get update && apt-get install -y unixodbc-dev
pip install -r /home/site/wwwroot/requirements.txt
python -m flask run --host=0.0.0.0 --port=8000
