import torch
import torch.nn as nn

# Implementation of Deep Metric Learning by Online Soft Mining and Class-Aware Attention
# https://arxiv.org/pdf/1811.01459v2.pdf

class OSPM_CAA_Loss(nn.Module):
    def __init__(self, alpha=1.2, l=0.5, ):
        super(CenterLoss, self).__init__()
        self.alpha = 1.2 # margin of weighted contrastive loss, as mentioned in the paper 
        self.l = 0.5 #  hyperparameter controlling weights of positive set and the negative set  
        # I haven't been able to figure out the use of \sigma CAA 0.18 
        self.osm_sigma = 0.8  \sigma OSM (0.8) as mentioned in paper
        
    def forward(self, x, labels , embd):
        x = nn.functional.normalize(x, p=2, dim=1) # normalize the features
        n = x.size(0)

        # Compute pairwise distance, replace by the official when merged
        dist = torch.pow(x, 2).sum(dim=1, keepdim=True).expand(n, n)
        dist = dist + dist.t()
        dist.addmm_(1, -2, x, x.t())
        dist = dist.clamp(min=1e-12).sqrt()  # for numerical stability & pairwise distance, dij

        S = torch.exp( -1.0 *  torch.pow(dist, 2)  / (self.osm_sigma * self.osm_sigma) )
        S_ = torch.clamp( self.alpha - dist , min=0.0)  # max(0, self.alpha − dij ) 

        p_mask = labels.expand(n, n).eq(labels.expand(n, n).t()) # same label == 1
        n_mask = 1- p_mask # oposite label == 1   
        
        S = S * p_mask.float()
        S = S + S_ * n_mask.float()
        
        #embd is the weights of the FC layer for classification R^(dxC) 
        denominator = torch.sum(torch.exp(torch.mm(x , embd)),1) 
        
        A = [] #attention corresponding to each feature fector
        for i in range(n):
            a_i = torch.exp(torch.dot(x[i] , embd[:,y[i]])) / denominator[i] 
            A.append(a_i)

        atten_class = torch.stack(A)
        
        A = torch.min(atten_class.expand(n,n) , atten_class.view(-1,1).expand(n,n) ) # pairwise minimum of attention weights 
        
        W = S * A 
        W_P = W * p_mask.float()
        W_N = W * n_mask.float()
        W_P = W_P * (1 - torch.eye(n, n).float())
        W_N = W_N * (1 - torch.eye(n, n).float())
        
        L_P = 1.0/2 * torch.sum(W_P * torch.pow(dist, 2)) / torch.sum(W_P)
        L_N = 1.0/2 * torch.sum(W_N * torch.pow(S_ , 2)) / torch.sum(W_N)
        
        L = (1- l) * L_P + l * L_N

        return L 
