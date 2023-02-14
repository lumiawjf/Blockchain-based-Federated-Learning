#!/bin/bash

echo "set all eth environment"
bootnode --verbosity=9 --nodekey=boot.key   &   sleep 3 &
geth --mine --miner.threads 2 --syncmode "full" --miner.gasprice=0 --networkid 8787 --bootnodes 'enode://d806feaee2f057182580ec56941c47753edbfca886e7d1334db3cf34a75d2620590c7665564cf4b66b96c1af9e18238bf4f32bb05d73333001707a477e839a2b@127.0.0.1:0?discport=30301' --datadir miner1/data --unlock "0xca38618860d047b63592cab7CB26c6DF2554141F" --password password.txt --http --http.addr 0.0.0.0 --http.port 8547 --http.corsdomain '*' --http.api 'admin,eth,net,web3,personal,miner' --ws --ws.addr 0.0.0.0 --ws.port 8548 --port 30304 --ws.origins '' --ws.api 'eth,net,web3' --nousb --allow-insecure-unlock   &   sleep 3 &
geth --mine --miner.threads 2 --syncmode "full" --miner.gasprice=0 --networkid 8787 --bootnodes 'enode://d806feaee2f057182580ec56941c47753edbfca886e7d1334db3cf34a75d2620590c7665564cf4b66b96c1af9e18238bf4f32bb05d73333001707a477e839a2b@127.0.0.1:0?discport=30301' --datadir miner2/data --unlock "0x086e0Fcab268b9eE0C781a58D93D8de524D58fBf" --password password.txt --http --http.addr 0.0.0.0 --authrpc.port 8542 --http.corsdomain '*' --http.api 'admin,eth,net,web3,personal,miner' --ws --ws.addr 0.0.0.0 --ws.port 8549 --port 30305 --ws.origins '' --ws.api 'eth,net,web3' --nousb --allow-insecure-unlock & sleep 2 &
cd BCFL && ipfs daemon

# Enable CTRL+C to stop all background processes
trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM
# Wait for all background processes to complete
wait