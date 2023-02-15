import warnings
from collections import OrderedDict
import flwr as fl
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision.datasets import CIFAR10
from torchvision.transforms import Compose, Normalize, ToTensor
from tqdm import tqdm
import socket
import jsons
import argparse
import time
# #############################################################################
# 1. Regular PyTorch pipeline: nn.Module, train, test, and DataLoader
# #############################################################################
warnings.filterwarnings("ignore", category=UserWarning)
# DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
DEVICE = torch.device("cpu")


class Net(nn.Module):
    """Model (simple CNN adapted from 'PyTorch: A 60 Minute Blitz')"""
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


def train(net, trainloader, epochs):
    """Train the model on the training set."""
    criterion = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(net.parameters(), lr=0.001, momentum=0.9)
    for _ in range(epochs):
        for images, labels in tqdm(trainloader):
            optimizer.zero_grad()
            criterion(net(images.to(DEVICE)), labels.to(DEVICE)).backward()
            optimizer.step()


def test(net, testloader):
    """Validate the model on the test set."""
    criterion = torch.nn.CrossEntropyLoss()
    correct, total, loss = 0, 0, 0.0
    with torch.no_grad():
        for images, labels in tqdm(testloader):
            outputs = net(images.to(DEVICE))
            labels = labels.to(DEVICE)
            loss += criterion(outputs, labels).item()
            total += labels.size(0)
            correct += (torch.max(outputs.data, 1)[1] == labels).sum().item()
    return loss / len(testloader.dataset), correct / total


def load_data():
    """Load CIFAR-10 (training and test set)."""
    trf = Compose([ToTensor(), Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])
    trainset = CIFAR10("./data", train=True, download=True, transform=trf)
    testset = CIFAR10("./data", train=False, download=True, transform=trf)
    # 按ID对训练集合的拆分
    id = 0
    all_range = list(range(len(trainset)))
    data_len = int(len(trainset) / 2)
    indices = all_range[id * data_len: (id + 1) * data_len]
    print(str(indices[0]),"-",str(indices[-1]))
    # 生成一个数据加载器
    train_loader = torch.utils.data.DataLoader(
        # 制定父集合
        trainset,
        # batch_size每个batch加载多少个样本(默认: 1)
        batch_size=32,
        # 指定子集合
        # sampler定义从数据集中提取样本的策略
        sampler=torch.utils.data.sampler.SubsetRandomSampler(indices)
    )
    
    return train_loader, DataLoader(testset)


# #############################################################################
# 2. Federation of the pipeline with Flower
# #############################################################################
# Load model and data (simple CNN, CIFAR-10)
net = Net().to(DEVICE)
trainloader, testloader = load_data()

# Define Flower client
class FlowerClient(fl.client.NumPyClient):
    def get_parameters(self):
        return [val.cpu().numpy() for _, val in net.state_dict().items()]

    def set_parameters(self, parameters):
        params_dict = zip(net.state_dict().keys(), parameters)
        state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
        net.load_state_dict(state_dict, strict=True)

    def fit(self, parameters, config):
        # print(self.get_parameters())
        self.set_parameters(parameters)
        train(net, trainloader, epochs=1)
        # print(self.get_parameters())
        torch.save(net, "mnist_cnn.pt")
        # test = jsons.dump(some_utcdate)
        return self.get_parameters(), len(trainloader.dataset), {}

    def evaluate(self, parameters, config):
        self.set_parameters(parameters)
        loss, accuracy = test(net, testloader)
        return loss, len(testloader.dataset), {"accuracy": accuracy}

# Start the flower client
fl.client.start_numpy_client("0.0.0.0:8787", client=FlowerClient())

HOST = '127.0.0.1'
PORT = 8000
clientMessage = 'Hello!'
parser = argparse.ArgumentParser(description='train')
parser.add_argument('-p', '--port', type=str, default='8080', help="port")
args = parser.parse_args()

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))
path = 'hash.txt'
IPFS=[]

with open(path) as f:
    IPFS = f.readlines()

LM_IPFS = IPFS[1].replace("\n", "")

GM_VerID = 1.0
print("I'm "+ args.port)
info_json={}

# Local Model IPFS hash
info_json['LM_IPFS'] = LM_IPFS
print("info_json['LM_IPFS']", info_json['LM_IPFS'])

# Global Model IPFS hash
info_json['GM_VerID'] = GM_VerID
print("info_json['GM_VerID']", info_json['GM_VerID'])

# Client Number
info_json['Client_Num'] = args.port
jsonstr = jsons.dumps(info_json)
print('jsonstr', jsonstr)

client.sendall(jsonstr.encode())
    
while True:
    Message = str(client.recv(1024), encoding='utf-8')
    if Message == None:
        Message="{""serverMessage"" : ""NOT YET"",""done_Num"": 0 }"
    print(Message)
    info_json = jsons.loads(Message)
    serverMessage = info_json['serverMessage']
    done_Num = info_json['done_Num']

    print('Server:', done_Num)
    print('Server:', serverMessage)
    first=0
    if done_Num ==2:
        break

client.close()