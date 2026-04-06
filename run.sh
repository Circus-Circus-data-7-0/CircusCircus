#!/bin/bash
export SECRET_KEY="kristofer"

if [ "$1" = "--server" ]; then
    cd ./forum && flask run --host=0.0.0.0 --port=8000
else
    cd ./forum && flask run --port=8000
fi

# To run the server, use: ./run.sh --server
# To run the server in development mode, use: ./run.sh
