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

def ipfs_cat(hash_ipfs):
    api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001/http') 
    line = str(api.cat(hash_ipfs))
    line = line.replace('\'', '\"')
    line = line[2:len(line)-1]
    weight = jsons.loads(line)
    return weight


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
    
weight=[]
IPFS=[]
path = '/workspaces/Blockchain-based-Federated-Learning/BCFL/hash.txt'
with open(path) as f:
    IPFS = f.readlines()
weight1 = np.array( ipfs_cat(IPFS[0].replace("\n", ""))['tensors'],dtype=object)
weight2 = np.array( ipfs_cat(IPFS[1].replace("\n", ""))['tensors'],dtype=object )
assert weight1.all()!= weight2.all(), "two weights are the same."
np.savetxt("w1.txt", weight1,fmt='%s')
np.savetxt("w2.txt", weight2,fmt='%s')

# for i in range(weight1.shape[0]):
    



# weight.append(ipfs_cat(IPFS[0].replace("\n", "")))
# weight.append(ipfs_cat(IPFS[1].replace("\n", "")))



# device = torch.device("cpu")
# model_ae = Net().to(device)
# init_weight = model_ae.state_dict()
# #assert 命令 true则无事发生 false则报错
# assert weight[0]['tensors'] != weight[1]['tensors'], "two weights are the same."

# for i in range(np.array(weight[0]['tensors'],dtype=object).shape[0]):    
#     we0 = np.array(weight[0]['tensors'][i],dtype=object)
#     we1 = np.array(weight[1]['tensors'][i],dtype=object)
#     weight[0]['tensors'][i] = ( (we0 +we1) / 2).astype(int).tolist()
#     print(we0.shape)
#     print(we1.shape)

# assert weight[0]['tensors'] != weight[1]['tensors'], "two weights are the same."

# path = '/workspaces/Blockchain-based-Federated-Learning/BCFL/weight'
# with open(path, 'w+') as f:
#     f.write(str(jsons.dumps(weight[0])))
# api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001/http')
# res = api.add(path)
# return res['Hash']