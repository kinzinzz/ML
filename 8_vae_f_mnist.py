# -*- coding: utf-8 -*-
"""8_VAE_f_MNIST.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1fCCg1dUI6gXLcrix4f9lJQFPHi3zY_Ol
"""

import numpy as np
import matplotlib.pyplot as plt

from torchvision.transforms import ToTensor

from torch.utils.data import DataLoader
from torchvision import datasets, transforms

import torch.nn as nn
import torch.nn.functional as F
import torch

train_images = datasets.MNIST(
    root= 'data',
    train= True,
    download= True,
    transform= ToTensor() 
)

test_images = datasets.MNIST(
    root= 'data',
    train= False,
    download= True,
    transform= ToTensor() 
)

# 하이퍼파라미터 준비
EPOCH = 10
BATCH_SIZE = 64
LEARNING_RATE = 1e-3
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using Device:", DEVICE)

train_loader = DataLoader(train_images, batch_size = BATCH_SIZE, shuffle = True)
test_loader = DataLoader(test_images, batch_size = BATCH_SIZE, shuffle = True)

class VAE(nn.Module):
    def __init__(self, latent_dim):
        super(VAE, self).__init__()
        self.flatten = nn.Flatten()
        self.encoder = nn.Sequential(
            nn.Linear(28 * 28, 512),
            nn.ReLU(),
            nn.Linear(512, 256),
            nn.ReLU(),
        )
        self.fc_mu = nn.Linear(256, latent_dim)
        self.fc_var = nn.Linear(256, latent_dim)
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 512),
            nn.ReLU(),
            nn.Linear(512, 28 * 28),
            nn.Sigmoid(),
        )

    def encode(self, x):            
        result = self.encoder(x)
        mu = self.fc_mu(result)
        var = self.fc_var(result)
        return mu, var

    def decode(self, z):
        result = self.decoder(z)
        return result   

    def reparameterize(self, mu, var):
        std = torch.exp(var / 2)
        eps = torch.randn_like(std)
        return mu + (eps * std) 

    def forward(self, x):
        x = self.flatten(x)
        mu, var = self.encode(x)
        z = self.reparameterize(mu, var)
        out = self.decode(z)
        return  out, mu, var

model = VAE(10).to(DEVICE)
print(model)

def loss_function(recon_x, x, mu, var):
    recon_loss = F.binary_cross_entropy(recon_x, x.view(-1, 28*28), reduction='sum')
    kl_loss = -0.5 * torch.sum(1 + var - mu.pow(2) - var.exp())
    return recon_loss + kl_loss
    
optimizer = torch.optim.Adam(model.parameters(), lr= LEARNING_RATE)

def train(train_loader, model, loss_fn, optimizer):
    model.train()

    for batch, (X, y) in enumerate(train_loader):
        X, y = X.to(DEVICE), y.to(DEVICE)
        decoded, mu, var= model(X)

        # 손실계산
        loss = loss_fn(decoded, X, mu, var)

        # 역전파
        optimizer.zero_grad() 
        loss.backward()
        optimizer.step()

    # 결과 시각화
    origin_data = X[:5].view(-1, 28*28).type(torch.FloatTensor)/255.
    decoded_data = decoded[:5].view(-1, 28*28).type(torch.FloatTensor)/255.
 
    f, axs = plt.subplots(2, 5, figsize=(5, 2))    
    for i in range(5):
        img = np.reshape(origin_data.data.numpy()[i],(28, 28))
        axs[0][i].imshow(img, cmap='gray')
        axs[0][i].set_xticks(())
        axs[0][i].set_yticks(())

    for i in range(5):
        img = np.reshape(decoded_data.to("cpu").data.numpy()[i], (28, 28)) 
        axs[1][i].imshow(img, cmap='gray')
        axs[1][i].set_xticks(()) 
        axs[1][i].set_yticks(())
    plt.show()

for i in range(EPOCH):
    print(f"Epoch {i+1} \n------------------------")
    train(train_loader, model, loss_function, optimizer)