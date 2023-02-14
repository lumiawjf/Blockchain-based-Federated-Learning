#!/bin/bash

echo "start socket_server"
python socket_server.py --deploy_contract True &

for i in `seq 0 1 2`; 
do
    echo "Starting server $i";
    python server_8081.py & python server_8787.py & sleep 3;  # Sleep for 3s to give the server enough time to start

    echo "Start client $i";
    python client_8081.py && python socket_client.py -p="8081";
    python client_8787.py && python socket_client.py -p="8787";
done

# for i in `seq 0 1`; do
#     echo "Starting client $i"
#     python client_8081.py &&
# done

# Enable CTRL+C to stop all background processes
trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM
# Wait for all background processes to complete
wait