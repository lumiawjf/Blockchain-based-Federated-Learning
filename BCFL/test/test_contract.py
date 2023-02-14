### Digital Signature ###
import Crypto
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto import Random
from Crypto.Signature import pkcs1_15
from Crypto.Cipher.PKCS1_v1_5 import new
import base64
import pprint
## Web3 & Smart contract ###
from web3 import Web3
from web3.providers.eth_tester import EthereumTesterProvider
from solcx import compile_source
import solcx
import os
import argparse

def pkcs5_pad(s, BLOCK_SIZE=16):                                                                                                                                                              
    return (s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(                                                                                                                                     
            BLOCK_SIZE - len(s) % BLOCK_SIZE                                                                                                                                                      
            )).encode('utf-8') 

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


with open("/workspaces/Blockchain-based-Federated-Learning/BCFL/task_owner_key/private.pem", "rb") as f:
    private_key = RSA.importKey(f.read())
path = '/workspaces/Blockchain-based-Federated-Learning/BCFL/latest_GMhash.txt'
f = open(path, 'r')
LM_IPFS = f.readline()
print(LM_IPFS)
signer = pkcs1_15.new(private_key)
hasher = SHA256.new(pkcs5_pad(LM_IPFS))
signature = str(signer.sign(hasher))
print(signature)
# signature_str = signature.decode('utf-16', 'replace')


   # Set up Web3.py instance
w3 = Web3(Web3.HTTPProvider("http://localhost:8547",
          request_kwargs={'timeout': 60}))

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

going_to_deploy_contract = True
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

    print(f"Fetching transaction instance by contract address : {address}...\n ")
    store_contract = w3.eth.contract(address=address, abi=abi)

    new_transaction = store_contract.functions.setFLUpdate(signature, LM_IPFS).transact()
    new_tx_receipt = w3.eth.wait_for_transaction_receipt(new_transaction)
    print("Transaction receipt mined:")
    pprint.pprint(dict(new_tx_receipt))

    returned_var = store_contract.functions.getFLUpdate().call()
    print("signature is: "+ signature)
    print(f'Returned information  = {returned_var}')
