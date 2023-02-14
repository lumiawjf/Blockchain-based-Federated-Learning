#!/bin/bash
for i in `seq 0 1 2`; 
do
    echo "Starting server $i";
    python server_8787.py & sleep 3;  # Sleep for 3s to give the server enough time to start

    echo "Start client $i";
    python client_8787.py && python socket_client.py -p="8787";
done

# for i in `seq 0 1`; do
#     echo "Starting client $i"
#     python client_8787.py &&
# done