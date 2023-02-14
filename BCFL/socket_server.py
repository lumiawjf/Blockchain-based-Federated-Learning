# -*- coding: utf-8 -*-
import socket
import jsons
import ipfshttpclient
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import datasets, transforms
import torchvision
import torchvision.transforms as transforms
from io import BytesIO
from typing import cast
import numpy as np
import time
import logging
from threading import Thread
from copy import deepcopy
import sys
import pprint
import json
import os

### Digital Signature ###
import Crypto
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto import Random
from Crypto.Signature import pkcs1_15
from Crypto.Cipher.PKCS1_v1_5 import new
import base64
## Web3 & Smart contract ###
from web3 import Web3
from web3.providers.eth_tester import EthereumTesterProvider
from solcx import compile_source
import solcx
import os
import argparse


#parser argparse
parser = argparse.ArgumentParser(description='smart contract')
parser.add_argument('-dc', '--deploy_contract', type=bool, default=True, help="First time to deploy contract.")
args = parser.parse_args()

"""
Digital Signature
"""
def sign(privatekey,data):
    return base64.b64encode(str((privatekey.sign(data,''))[0]).encode())

def verify(publickey,data,sign):
     return publickey.verify(data,(int(base64.b64decode(sign)),))

def pkcs5_pad(s, BLOCK_SIZE=16):                                                                                                                                                              
    return (s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(                                                                                                                                     
            BLOCK_SIZE - len(s) % BLOCK_SIZE                                                                                                                                                      
            )).encode('utf-8') 

"""
Smart Contract
"""
def compile_source_file(file_path):
    solcx.install_solc(version='0.8.9')
    solcx.set_solc_version('0.8.9')
    with open(file_path, 'r') as f:
        source = f.read()
        # print(source)
    return solcx.compile_source(source)

def deploy_contract(w3, abi, bytecode):
    tx_hash = w3.eth.contract(
        abi=abi,
        bytecode=bytecode).constructor().transact()
    return tx_hash


"""Validation function"""
#LeNet5 Co Po Co Po FC FC FC
class Net(nn.Module):
    def __init__(self) -> None:
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(3, 6, 5)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(6, 16, 5)
        self.fc1 = nn.Linear(16 * 5 * 5, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = x.view(-1, 16 * 5 * 5)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.fc3(x)
    
def parameters_to_weights(parameters):
    """Convert parameters object to NumPy weights."""
    return [bytes_to_ndarray(tensor) for tensor in parameters]

def bytes_to_ndarray(tensor):
    """Deserialize NumPy ndarray from bytes."""
    bytes_io = BytesIO(bytes(tensor))
    ndarray_deserialized = np.load(bytes_io, allow_pickle=False)
    return cast(np.ndarray, ndarray_deserialized)

#validate certain weight on the model. 
def validation(weight):
    device = torch.device("cpu")
    model_ae = Net().to(device)
    init_weight = model_ae.state_dict()
    for i,layer in enumerate(init_weight.keys()):
        init_weight[layer] = torch.from_numpy(parameters_to_weights(weight['tensors'])[i])
        # print(i,layer)

    model_ae.load_state_dict(init_weight)
    model_ae.eval()
    transform = transforms.Compose( [transforms.ToTensor(),
     transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])

    batch_size = 16
    testset = torchvision.datasets.CIFAR10(root='./data', train=False,
                                           download=True, transform=transform)
    testloader = torch.utils.data.DataLoader(testset, batch_size=batch_size,
                                             shuffle=False, num_workers=2)
    classes = ('plane', 'car', 'bird', 'cat','deer', 'dog', 'frog', 'horse', 'ship', 'truck')
    
    correct = 0
    total = 0
    with torch.no_grad():
        for data in testloader:
            images, labels = data
            outputs = model_ae(images)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    print(f'\nAccuracy of the network on the 10000 test images: {100 * correct / total} %\n')
    with open("accuracy.txt", 'a+') as f:  
        f.write(f"{100 * correct / total}\n")
    return  str(100 * correct // total) 


def weights_to_parameters(weights):
    """Convert NumPy weights to parameters object."""
    tensors = [ndarray_to_bytes(ndarray) for ndarray in weights]
    return Parameters(tensors=tensors, tensor_type="numpy.ndarray")


def ipfs_cat(hash_ipfs):
    api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001/http') 
    line = str(api.cat(hash_ipfs))
    line = line.replace('\'', '\"')
    line = line[2:len(line)-1]
    weight = jsons.loads(line)
    return weight
    

def aggregated(checked):
    weight=[]
    IPFS=[]
    path = '/workspaces/Blockchain-based-Federated-Learning/BCFL/hash.txt'
    
    with open(path) as f:
        IPFS = f.readlines()
    weight.append(ipfs_cat(IPFS[0].replace("\n", "")))
    weight.append(ipfs_cat(IPFS[1].replace("\n", "")))
    
    device = torch.device("cpu")
    model_ae = Net().to(device)
    init_weight = model_ae.state_dict()
    #assert 命令 true则无事发生 false则报错
    assert weight[0]['tensors'] != weight[1]['tensors'], "two weights are the same."
    
    for i in range(np.array(weight[0]['tensors'],dtype=object).shape[0]):    
        we0 = np.array(weight[0]['tensors'][i],dtype=object)
        we1 = np.array(weight[1]['tensors'][i],dtype=object)
        if (we0==(we0+we1)/2).all():
            cp = deepcopy(list(map(float, weight[0]['tensors'][i])))
            weight[0]['tensors'][i] = ( (we0 +we1) / 2).astype(int).tolist()
            print(we0.shape)
            print(we1.shape)
            print(weight[0]['tensors'][i].shape)

    path = '/workspaces/Blockchain-based-Federated-Learning/BCFL/weight'
    with open(path, 'w+') as f:
        f.write(str(jsons.dumps(weight[0])))
    api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001/http')
    res = api.add(path)
    return res['Hash']

if __name__ == '__main__':

    done = []
    checked = []
    user = {}  # Dictionary{addr:name}
    clients = set()


    """
    RSA Public key and private key
    """
    # RSA private key
    with open("/workspaces/Blockchain-based-Federated-Learning/BCFL/task_owner_key/private.pem", "rb") as f:
        private_key = RSA.importKey(f.read())

    # # RSA Public key
    # if not 'public.pem' in os.listdir(task_owner_path):
    #     file = 'task_owner_key/public.pem'
    #     open(file, 'a').close()
    #     publicKey = key.publickey().export_key()
    #     with open("task_owner_key/public.pem", "wb") as f:
    #         f.write(publicKey)
    # else:
    #     with open(task_owner_path+"public.pem", "rb") as f:
    #         public_key = RSA.importKey(f.read())

    """
    Web3 & Smart contract
    """
    # Set up Web3.py instance 
    w3 = Web3(Web3.HTTPProvider("http://localhost:8547", request_kwargs={'timeout': 60}))

    # Set pre-funded account as sender
    w3.eth.default_account = w3.eth.accounts[0]
    print(f'Using miner 1 address = {w3.eth.default_account}')
    chain_id = 8787
    contract_path = "/workspaces/Blockchain-based-Federated-Learning/BCFL/contract.sol"

    # Compile contract, get contract ID & interface
    compiled_sol = compile_source_file(contract_path)
    contract_id, contract_interface = compiled_sol.popitem()

    # Get abi & bytecode from contract interface
    abi = contract_interface['abi']
    bytecode = contract_interface['bin']

    going_to_deploy_contract = args.deploy_contract
    if going_to_deploy_contract:
        # Deploy compiled contract, get txHash : hasn't been mined yet (i.e. is pending)
        print(f'First time to deploy contract......')
        tx_hash = deploy_contract(w3, abi, bytecode)
        tx_hash = w3.eth.contract(
                abi=abi,
                bytecode=bytecode).constructor().transact()
        print(f'Tx_hash = ')
        pprint.pprint(tx_hash)
        print(f'Waiting to deploy smart contract.......')

        # tx_receipt : the transaction is mined (contained execution status[success/fail] & emitted event logs)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        # print(f'Contract deployed successful !\ntx_receipt = \n')
        # pprint.pprint(dict(tx_receipt))
        address = w3.eth.get_transaction_receipt(tx_hash)['contractAddress']
        print(f'Deployed to address : {address}.\n')
    i = 0
    HOST = '127.0.0.1'
    PORT = 8000
    while True:
        i = i + 1
        print("%d epoch" % i)

        try:
            #set server
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            server.bind((HOST, PORT))
            server.listen(10)
            conn, addr = server.accept()
            clients.add(conn)
            print("\naddr"+str(addr))
            # print("\nconn"+str(conn))

            if not addr in user:    # as long as the client isn't in user list, to perform below:
                #received msg from client
                user[addr] = str(conn.recv(1024), encoding='utf-8') 
                clientMessage = user[addr]
                info_json = jsons.loads(clientMessage)
                
                # Local Model IPFS hash
                LM_IPFS = info_json['LM_IPFS']
                Client_Num = info_json['Client_Num'] 
                print('Client Local Model IPFS hash is:', LM_IPFS)

                # Validation phase
                weight = ipfs_cat(LM_IPFS)
                accuracy = validation(weight)
                serverMessage = 'Validated!Accuracy = '+accuracy+ '%'
                checked.append(Client_Num)
                done.append(Client_Num)

                if len(done) == 2:
                    
                    print("Aggregating...")
                    LM_IPFS = aggregated(checked)
                    accuracy2 = validation(weight)
                    print("accuracy after aggregating is: %s" % accuracy2)
                    serverMessage = 'Next Global Model hash:'+ LM_IPFS

                    # print('serverMessage: ', serverMessage)
                    info_json['serverMessage'] = serverMessage
                    info_json['done_Num'] = len(done)

                    # Build transaction and wait to be mined
                    # Fetch contract by contractAddress & abi
                    address = w3.eth.get_transaction_receipt(tx_hash)['contractAddress']
                    # print(f"Fetching transaction instance by contract address : {address}...\n ")
                    store_contract = w3.eth.contract(address=address, abi=abi)
                    
                    # Sign the transaction hash with task owner's private key 
                    # signer = PKCS1_v1_5.new(private_key)
                    signer = pkcs1_15.new(private_key)

                    hasher = SHA256.new(pkcs5_pad(LM_IPFS))
                    signature = signer.sign(hasher)
                    signature_str = signature.decode('utf-16', 'ignore')
                    # print(f"Signature : {signature}, can be verified by task owner's public key, transaction hash & signature")
                    # print(f"Fetched contract instance succesfully :{store_contract}\nStart sending transaction...\n ")
                    # print(f"signature_str: {signature_str}")
                    new_transaction = store_contract.functions.setFLUpdate(signature_str, LM_IPFS).transact()
                    new_tx_receipt = w3.eth.wait_for_transaction_receipt(new_transaction)
                    # print("Transaction receipt mined:")
                    # pprint.pprint(dict(new_tx_receipt))
                    # print("\nWas transaction successful?")
                    # pprint.pprint(new_tx_receipt["status"])

                    returned_var = store_contract.functions.getFLUpdate().call()
                    # print(f'Returned information  = {returned_var}')
                    
                    serverMessage = jsons.dumps(info_json)                    
                    path = '/workspaces/Blockchain-based-Federated-Learning/BCFL/latest_GMhash.txt'
                    f = open(path, 'w')
                    f.write(LM_IPFS)
                    f.close()
                
                    path = '/workspaces/Blockchain-based-Federated-Learning/BCFL/hash.txt'
                    f = open(path, 'w')
                    f.close()
                    
                    #  Return Global Model IPFS hash
                    for c in clients:
                        c.sendall(serverMessage.encode())
                        
                    user={}
                    done = []
                    checked = []

                else :
                    info_json['serverMessage'] = serverMessage
                    info_json['done_Num'] = '0'
                    serverMessage = jsons.dumps(info_json)
                    conn.sendall(serverMessage.encode())
                              
            else:
                info_json['serverMessage'] = 'NOT YET'
                info_json['done_Num'] = '0'
                serverMessage = jsons.dumps(info_json)
                conn.sendall(serverMessage.encode())

            server.close()

        except ConnectionResetError:
            logging.warning('Someone meets error.')