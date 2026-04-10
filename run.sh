#!/usr/bin/env bash

# export PORT=5006
export SECRET_KEY="kristofer"
# honcho start

# you can ALSO or RATHER use the following command to run the app
flask --app forum.app run --port 8000
