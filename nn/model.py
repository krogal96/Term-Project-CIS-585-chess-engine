#Contains the definition of the evaluation Neural Network model

import torch.nn as nn
import torch.nn.functional as F

class EvalNetwork(nn.Module):
    def __init__(self):
        super(EvalNetwork, self).__init__()
        self.linear1 = nn.Linear(454,2048)
        self.linear2 = nn.Linear(2048,1024)
        self.linear3 = nn.Linear(1024,1024)
        self.linear4 = nn.Linear(1024,256)
        self.linear5 = nn.Linear(256,64)
        self.linear6 = nn.Linear(64,1)
        self.Tanh = nn.Tanh()
        self.Tanhshrink = nn.Tanhshrink()
        self.Sigmoid = nn.Sigmoid()
        
    def forward(self,x):
        x = F.leaky_relu(self.linear1(x))
        x = F.leaky_relu(self.linear2(x))
        x = F.leaky_relu(self.linear3(x))
        x = F.leaky_relu(self.linear4(x))
        x = F.leaky_relu(self.linear5(x))
        x = F.leaky_relu(self.linear6(x))
        return x
        
        