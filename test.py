# -*- coding: utf-8 -*-
"""exp_lr_efficient_net.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ZgzhyzKUmKDDUMvNIE3ospjTND2vn8HF
"""

from google.colab import drive 
drive.mount('/content/MyDrive')
import sys
sys.path.append('/content/MyDrive/MyDrive/Model_files/MiDaS')

!pip install utils

import sys

sys.path.append("..")

import torch
import torch.nn as nn
import os
import torch
import numpy as np

class conv1x1(nn.Module):
    def __init__(self, channel_in, channel_out):
        super(conv1x1, self).__init__()
        self.conv = nn.ConvTranspose2d(
            channel_in, channel_out, kernel_size=3, stride=1, padding=1
        )

    def forward(self, x):
        return self.conv(x)

class conv1x1_Model2(nn.Module):
    def __init__(self, channel_in, channel_out):
        super(conv1x1_Model2, self).__init__()
        self.conv = nn.ConvTranspose2d(
            channel_in, channel_out, kernel_size=5, stride=2, padding=2, output_padding=1,
        )

    def forward(self, x):
        return self.conv(x)


class conv5x5(nn.Module):
    def __init__(self, channel_in, channel_out):
        super(conv5x5, self).__init__()
        self.conv = nn.Conv2d(
            channel_in, channel_out, kernel_size=5, stride=1, padding=2
        )
        self.activation = nn.ReLU()
        self.bnorm = nn.BatchNorm2d(channel_out)

    def forward(self, x):
        return self.bnorm(self.activation(self.conv(x)))

class conv3x3(nn.Module):
  def __init__(self,channel_in,channel_out):
    super(conv3x3,self).__init__()
    self.conv = nn.Conv2d(channel_in, channel_out, kernel_size=3, stride=1, padding=1)
    self.bnorm = nn.BatchNorm2d(channel_out)
    self.activation = nn.ReLU()
  def forward(self, x):
    return self.bnorm(self.activation(self.conv(x)))


class conv5x5_leakR(nn.Module):
  def __init__(self,channel_in,channel_out):
    super(conv5x5_leakR,self).__init__()
    self.conv = nn.Conv2d(channel_in, channel_out, kernel_size=5, stride=1, padding=2)
    self.bnorm = nn.BatchNorm2d(channel_out)
    self.activation = nn.LeakyReLU()
  def forward(self, x):
    return self.bnorm(self.activation(self.conv(x)))

class conv3x3_leakR(nn.Module):
  def __init__(self,channel_in,channel_out):
    super(conv3x3_leakR,self).__init__()
    self.conv = nn.Conv2d(channel_in, channel_out, kernel_size=3, stride=1, padding=1)
    self.bnorm = nn.BatchNorm2d(channel_out)
    self.activation = nn.LeakyReLU()
  def forward(self, x):
    return self.bnorm(self.activation(self.conv(x)))


class upconv3x3(nn.Module):
    def __init__(self, channel_in, channel_out):
        super(upconv3x3, self).__init__()
        self.conv = nn.ConvTranspose2d(
            channel_in, channel_out, kernel_size=4, stride=2, padding=1
        )
        self.activation = nn.LeakyReLU()
        self.bnorm = nn.BatchNorm2d(channel_out)

    def forward(self, x):
        return self.bnorm(self.activation(self.conv(x)))

# Commented out IPython magic to ensure Python compatibility.
# %cd MyDrive/MyDrive/Model_files/MiDaS

import os
import glob
import torch
import utils
import cv2
import argparse

from torchvision.transforms import Compose
# from midas.midas_net import MidasNet
from midas.midas_net_custom import MidasNet_small
from midas.transforms import Resize, NormalizeImage, PrepareForNet

import re
import numpy as np
import sys


def readPFM(file):
    file = open(file, 'rb')

    color = None
    width = None
    height = None
    scale = None
    endian = None

    header = file.readline().rstrip()
    if header == b'PF':
        color = True
    elif header == b'Pf':
        color = False
    else:
        raise Exception('Not a PFM file.')

    dim_match = re.match(r'^(\d+)\s(\d+)\s$', file.readline().decode('utf-8'))
    if dim_match:
        width, height = map(int, dim_match.groups())
    else:
        raise Exception('Malformed PFM header.')

    scale = float(file.readline().rstrip())
    if scale < 0:  # little-endian
        endian = '<'
        scale = -scale
    else:
        endian = '>'  # big-endian

    data = np.fromfile(file, endian + 'f')
    shape = (height, width, 3) if color else (height, width)

    data = np.reshape(data, shape)
    data = np.flipud(data)
    file.close()
    return data, scale

IMG_EXTENSIONS = [
    '.jpg', '.JPG', '.jpeg', '.JPEG',
    '.png', '.PNG', '.ppm', '.PPM', '.bmp', '.BMP',
]

from PIL import Image

def is_image_file(filename):
    return any(filename.endswith(extension) for extension in IMG_EXTENSIONS)


def default_loader(path):
    return Image.open(path).convert('RGB')


def disparity_loader(path):
    return readPFM(path)

def PFM_loader(path):
    return readPFM(path)

import random
import os
folder = 'MyDrive/MyDrive/Model_files/MiDaS/midas'
def dataloader(filepath):
    all_left_img = []
    all_right_img = []
    all_left_disp = []
    all_left_depth_clue = []
    for filename in os.listdir(filepath):
      all_left_img.append(filepath + str(filename) + '/left.png')
      all_right_img.append(filepath + str(filename) + '/right.png')
      all_left_disp.append(filepath + str(filename) + '/gt_left.pfm')
      all_left_depth_clue.append(filepath + str(filename) + '/DistgDisp.pfm')
    return all_left_img, all_right_img, all_left_disp, all_left_depth_clue
#dataloader('/content/MyDrive/MyDrive/Stereo_dataset_with_central_view/Train/')

import torch.utils.data as data
import numpy as np
import torchvision
class myImageFloder(data.Dataset):
    def __init__(self, left, right, left_disparity, depth_clue, training, loader=default_loader):#, dploader=disparity_loader):

        self.left = left
        self.right = right
        self.disp_L = left_disparity
        self.depth_clue = depth_clue
        self.loader = loader
        self.dploader = disparity_loader
        self.dcloader = PFM_loader
        self.training = training

    def __getitem__(self, index):
        left = self.left[index]
        right = self.right[index]
        disp_L = self.disp_L[index]
        depth_clue = self.depth_clue[index]

        datagt, scaleL = self.dploader(disp_L)
        datagt = np.ascontiguousarray(datagt, dtype=np.float32)
        
        datadc, scaleL = self.dcloader(depth_clue)
        datadc = np.ascontiguousarray(datadc, dtype=np.float32)
        th, tw = 256, 512

        left_img = np.array(self.loader(left))
        right_img = np.array(self.loader(right))
        
        left_img = cv2.resize(left_img,(tw,th),interpolation = cv2.INTER_CUBIC)
        right_img = cv2.resize(right_img,(tw,th),interpolation = cv2.INTER_CUBIC)
        left_img = np.rint(255*((left_img-left_img.min())/(left_img.max()-left_img.min())))
        right_img = np.rint(255*((right_img-right_img.min())/(right_img.max()-right_img.min())))
        
        left_img = np.transpose(left_img,(2,0,1)).astype(np.float32)
        right_img = np.transpose(right_img,(2,0,1)).astype(np.float32)
        left_img = (torch.from_numpy(np.array(left_img)))
        right_img = (torch.from_numpy(np.array(right_img)))

        datagt = cv2.resize(datagt,(tw,th),interpolation = cv2.INTER_CUBIC)
        datagt = np.rint(255*((datagt-datagt.min())/(datagt.max()-datagt.min())))
        datagt = (torch.from_numpy(np.array(datagt)))
        #datagt = datagt.unsqueeze(0)

        datadc = cv2.resize(datadc,(tw,th),interpolation = cv2.INTER_CUBIC)
        datadc = np.rint(255*((datadc-datadc.min())/(datadc.max()-datadc.min())))
        datadc = (torch.from_numpy(np.array(datadc)))
        #datadc = datadc.unsqueeze(0)
        
      
        return left_img, right_img, datagt, datadc

    def __len__(self):
        return len(self.left)

import torch,os
import torch.nn as nn
import torch.nn.parallel
import torch.optim as optim
import torch.utils.data
datapath = '/content/MyDrive/MyDrive/Model_files/Stereo_dataset_with_central_view/Train/'
train_left_img, train_right_img, train_left_disp, train_left_depth_clue = dataloader(datapath)
total = int(len(train_left_disp))
trainCount = int(0.9*total)

test_left_img, test_right_img, test_left_disp, test_left_depth_clue= train_left_img[trainCount:], train_right_img[trainCount:], train_left_disp[trainCount:], train_left_depth_clue[trainCount:]

train_left_img, train_right_img, train_left_disp, train_left_depth_clue = train_left_img[:trainCount], train_right_img[:trainCount], train_left_disp[:trainCount], train_left_depth_clue[:trainCount]
print('train: ',len(train_left_img), 'val: ',len(test_left_img))

TrainImgLoader = torch.utils.data.DataLoader(
    myImageFloder(train_left_img, train_right_img, train_left_disp, train_left_depth_clue, True),
    batch_size=4, shuffle=True, num_workers=2, drop_last=False)

TestImgLoader = torch.utils.data.DataLoader(
    myImageFloder(test_left_img, test_right_img, test_left_disp, test_left_depth_clue, False),
    batch_size=1, shuffle=False, num_workers=2, drop_last=False)

from tqdm.notebook import tqdm

"""# Model 10 efficient_attn"""

import torch
import math
import torch.nn as nn
import torch.nn.functional as F

class base_layer_1(nn.Module):
  def __init__(self, in_channel,out_channel):
    super(base_layer_1, self).__init__()
    self.maxpool = nn.MaxPool2d(2)
    self.convntom = conv3x3_leakR(in_channel, out_channel)
    self.convmtom = conv3x3_leakR(out_channel, out_channel)

  def forward(self,x):
    x = self.convntom(x)
    x1 = self.convmtom(x)
    x = self.maxpool(x1)
    return x,x1

class EfficientAttention(nn.Module):
    
    def __init__(self, in_channels, key_channels, head_count, value_channels):
        super().__init__()
        self.in_channels = in_channels
        self.key_channels = key_channels
        self.head_count = head_count
        self.value_channels = value_channels

        self.keys = nn.Conv2d(in_channels, key_channels, 1)
        self.queries = nn.Conv2d(in_channels, key_channels, 1)
        self.values = nn.Conv2d(in_channels, value_channels, 1)
        self.reprojection = nn.Conv2d(value_channels, in_channels, 1)

    def forward(self, input_):
        n, _, h, w = input_.size()
        keys = self.keys(input_).reshape((n, self.key_channels, h * w))
        queries = self.queries(input_).reshape(n, self.key_channels, h * w)
        values = self.values(input_).reshape((n, self.value_channels, h * w))
        head_key_channels = self.key_channels // self.head_count
        head_value_channels = self.value_channels // self.head_count
        
        attended_values = []
        for i in range(self.head_count):
            key = F.softmax(keys[
                :,
                i * head_key_channels: (i + 1) * head_key_channels,
                :
            ], dim=2)
            query = F.softmax(queries[
                :,
                i * head_key_channels: (i + 1) * head_key_channels,
                :
            ], dim=1)
            value = values[
                :,
                i * head_value_channels: (i + 1) * head_value_channels,
                :
            ]
            context = key @ value.transpose(1, 2)
            attended_value = (
                context.transpose(1, 2) @ query
            ).reshape(n, head_value_channels, h, w)
            attended_values.append(attended_value)

        aggregated_values = torch.cat(attended_values, dim=1)
        reprojected_value = self.reprojection(aggregated_values)
        attention = reprojected_value + input_

        return attention

import torch
import torch.nn as nn
import torch.nn.functional as F



class _2TUnet(nn.Module):
    def __init__(self):
        super(_2TUnet, self).__init__()

        c0, c1, c2, c3, c4, c5 = [64, 128, 256, 512, 1024, 2048]
        self.maxpool = nn.MaxPool2d(2)

        self.layer_1_4to64 = base_layer_1(4,c0)
        self.layer_1_3to64 = base_layer_1(3,c0) 
        self.layer_2_64to128 = base_layer_1(c0,c1)

        self.layer_3_128to256 = base_layer_1(c1,c2)
        self.layer_4_256to512 = base_layer_1(c2,c3)
        self.layer_5_512to1024 = base_layer_1(c3,c4)

        self.conv1024to2048 = conv3x3_leakR(c4,c5)
        
        self.conv64to64 = conv3x3_leakR(c0,c0)
        self.conv128to128 = conv3x3_leakR(c1, c1)
        self.conv256to256 = conv3x3_leakR(c2, c2)
        self.conv512to512 = conv3x3_leakR(c3, c3)
        self.conv1024to1024 = conv3x3_leakR(c4, c4)
        self.conv2048to2048 = conv3x3_leakR(c5, c5)
        
        self.conv2048to2048 = conv3x3_leakR(c5, c5)

        self.conv128to64 = conv3x3_leakR(c1, c0)
        self.conv256to128 = conv3x3_leakR(c2, c1)
        self.conv512to256 = conv3x3_leakR(c3, c2)
        self.conv1024to512 = conv3x3_leakR(c4, c3)
        self.conv2048to1024 = conv3x3_leakR(c5,c4)

        self.upconv2048to1024 = upconv3x3(c5,c4)
        self.upconv1024to512 = upconv3x3(c4, c3)
        self.upconv512to256 = upconv3x3(c3, c2)
        self.upconv256to128 = upconv3x3(c2, c1)
        self.upconv128to64 = upconv3x3(c1, c0)

        self.conv64to1 = conv1x1(c0, 1)

        #Attention maps
        # the number of keys and values must be divisible by the number of heads
        self.effatn64 = EfficientAttention(c0,64,8,64)
        self.effatn128 = EfficientAttention(c1,64,8,64)
        self.effatn256 = EfficientAttention(c2,64,8,64)
        self.effatn512 = EfficientAttention(c3,64,8,64)
        self.effatn1024 = EfficientAttention(c4,64,8,64)
        self.effatn2048 = EfficientAttention(c5,64,8,64)

        # self.MHSA64 = MultiHeadSelfAttention(64)
        # self.MHSA128 = MultiHeadSelfAttention(128)
        # self.MHSA256 = MultiHeadSelfAttention(256)
        # self.MHSA512 = MultiHeadSelfAttention(512)
        # self.MHSA = MultiHeadSelfAttention(512)
        
    def forward(self, x, y, depth_clue):
        #print("x " + str(x.shape))
        #print("y " + str(y.shape))
        #print("depth_clue " + str(depth_clue.shape))
        x = torch.cat([x, depth_clue],dim=1)
        x,x1 = self.layer_1_4to64(x)
        y,y1 = self.layer_1_3to64(y)
        
        x,x2 = self.layer_2_64to128(x)
        y,y2 = self.layer_2_64to128(y)

        x,x3 = self.layer_3_128to256(x)
        y,y3 = self.layer_3_128to256(y)

        x,x4 = self.layer_4_256to512(x)
        y,y4 = self.layer_4_256to512(y)

        x,x5 = self.layer_5_512to1024(x)
        y,y5 = self.layer_5_512to1024(y)
        
        x = self.conv1024to2048(x)
        x = self.conv2048to2048(x)
        #print("self.conv1024to1024(x) " +str(x.shape))
        x = self.upconv2048to1024(x)
        a5 = self.effatn2048(torch.concat([x5,y5],dim=1))
        a5 = self.conv2048to1024(a5)
        x = self.conv2048to1024(torch.cat([x,a5],dim=1))
        x = self.conv1024to1024(x)

        x = self.upconv1024to512(x)
        #print("self.upconv1024to512(x) " +str(x.shape))
        a4 = self.effatn1024(torch.concat([x4,y4],dim=1))
        a4 = self.conv1024to512(a4)
        x = self.conv1024to512(torch.cat([x, a4], dim=1))
        #print("self.conv1024to512(x) " +str(x.shape))

        x = self.conv512to512(x)
        x = self.upconv512to256(x)
        #print("self.upconv512to256(x) " +str(x.shape))
        a3 = self.effatn512(torch.concat([x3,y3],dim=1))
        a3 = self.conv512to256(a3) 
        x = self.conv512to256(torch.cat([x, a3], dim=1))
        #print("self.conv512to256(x) " +str(x.shape))
        x = self.conv256to256(x)
        x = self.upconv256to128(x)
        #print("self.upconv256to128(x) " +str(x.shape))
        a2 = self.effatn256(torch.concat([x2,y2],dim=1))
        a2 = self.conv256to128(a2) 
        x = self.conv256to128(torch.cat([x, a2], dim=1))
        #print("self.conv256to128(x) " +str(x.shape))
        x = self.conv128to128(x)
        x = self.upconv128to64(x)
        #print("self.upconv128to64(x) " +str(x.shape))
        a1 = self.effatn128(torch.concat([x1,y1],dim=1))
        a1 = self.conv128to64(a1) 
        x = self.conv128to64(torch.cat([x, a1], dim=1))
        #print("self.conv128to64(x) " +str(x.shape))
        x = self.conv64to64(x)
        #print("self.conv64to64(x) " +str(x.shape))
        x = self.conv64to1(x)
        #print("x output = " +str(x.shape))
        return x


criterion = nn.MSELoss()
# criterion = RMSELoss()
model = _2TUnet()#(Bottleneck, [3, 4, 6, 3])
optimiser = optim.Adam(model.parameters(),lr=0.1)



def berhu_loss(y_true, y_pred, c=0.2):
    
    # Calculate the absolute error between the true and predicted values
    abs_diff = torch.abs(y_true - y_pred)
    
    # Calculate the maximum absolute error
    max_abs_diff = torch.max(abs_diff)
    
    # Calculate the threshold parameter
    threshold = c * max_abs_diff
    
    # Calculate the loss value
    if threshold == 0:
        loss = abs_diff.mean()
    else:
        # Calculate the Huber loss value
        huber_loss = torch.where(abs_diff < threshold, 
                                 0.5 * abs_diff ** 2, 
                                 c * (abs_diff - (0.5 * threshold)))
        
        # Calculate the absolute value of the Huber loss
        loss = torch.mean(torch.abs(huber_loss))
    
    return loss
def sobel(preds,img):
  # tensor = torch.rand([1,1, 183, 275])
  weights_x = torch.tensor([[1., 0., -1.],
                          [2., 0., -2.],
                          [1., 0., -1.]])
  weights_y = torch.tensor([[1., 2., 1.],
                          [0., 0., 0.],
                          [-1., -2., -1.]])

  if img.shape[0] == 4:
    weights_x = weights_x.view(1, 1, 3, 3).repeat(1, 4, 1, 1)
    weights_y = weights_y.view(1, 1, 3, 3).repeat(1, 4, 1, 1)
  elif img.shape[0]==1:
    weights_x = weights_x.view(1, 1, 3, 3).repeat(1, 1, 1, 1)
    weights_y = weights_y.view(1, 1, 3, 3).repeat(1, 1, 1, 1)
  weights_x= weights_x.cuda()
  weights_y= weights_y.cuda()

  pred_output_x = F.conv2d(preds, weights_x)
  img_output_x = F.conv2d(img, weights_x)

  pred_output_y = F.conv2d(preds, weights_y)
  img_output_y = F.conv2d(img, weights_y)

  output = torch.mean(torch.abs(pred_output_x-img_output_x) + torch.abs(pred_output_y-img_output_y)).data.cpu().numpy()

  # output = torch.abs(output_x) + torch.abs(output_y)
  return output

def ssim_loss(img, preds):
  def ssim_enh(img):
    weights = torch.tensor([[0.,-1.,0.],
                            [-1.,5.,-1.],
                            [0.,-1.,0.]])
    weights = weights.view(1, 1, 3, 3).repeat(1, 4, 1, 1)
    weights = weights.cuda()
    out = F.conv2d(img, weights,stride=1, padding=1)
    return out
  print(np.squeeze(ssim_enh(img).detach().cpu().numpy()).shape)
  print(np.squeeze(preds.detach().cpu().numpy()).shape)
  final_out = (1 - np.mean(ssim(np.squeeze(ssim_enh(img).detach().cpu().numpy()),np.squeeze(preds.detach().cpu().numpy()),win_size = 3)))
  return final_out


def depth_loss_function(predicted_depth, ground_truth_depth):
    
    # Point-wise depth
    ##l_depth = K.mean(K.abs(y_pred - y_true), axis=-1)
    ber_loss = berhu_loss(ground_truth_depth,predicted_depth)
    sobel_loss = sobel(predicted_depth, ground_truth_depth)
    
    # ssim_ = ssim_loss(ground_truth_depth,predicted_depth)
    # print(ber_loss)
    # print(sobel_loss)
    # print(ssim_)

    # Weights
    w1 = 1.0
    w2 = 1.0
    w3 = 1.0

    return  (w1 * ber_loss) + (w2 * sobel_loss) #+ (w3 * ssim_)

#from torchsummary import summary
!pip install albumentations
!echo "$(pip freeze | grep albumentations) is successfully installed"
#summary(model,[(3,512,256),(3,512,256)])
#import torchvision.transforms as T
#from albumentations.pytorch import ToTensorV2
import albumentations as T
transform = T.Compose([T.RandomSizedCrop(min_max_height=(50,250),height=256, width=512,p=0.9)],
                      additional_targets={'image0': 'image', 'image1': 'image', 'image2': 'image', 'image3': 'image'}
                      )

transform4LeftRight = T.Compose([#T.RandomBrightnessContrast(p=0.5)#,
                                #  T.RandomGamma(p=0.5),
                                #  T.Blur(p=0.5),
                                #  T.Emboss(alpha=(0.2,0.7),strength=(0.2,0.7),always_apply=False, p=0.5)
                                #  T.RGBShift(r_shift_limit=30, g_shift_limit=30, b_shift_limit=30, p=1)#,
                                 #T.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
                                 ],
                                additional_targets={'image0': 'image', 'image1': 'image'}
                                )
#A_img = transform(TrainImgLoader)

model = model.cuda() 
model.load_state_dict(torch.load('/content/MyDrive/MyDrive/Nov 2TUNet/2TUNet_ResNet Encoder SEAttention Dark Channel.pt'))
#optimiser.load_state_dict(torch.load('/content/MyDrive/MyDrive/2TUNet/IC3D2021_2T_UNET/model_saved/2TUNet_optimiser(7+5+5)'+'.pt'))


DirL = '/content/MyDrive/MyDrive/2TUNet/IC3D2021_2T_UNET/DATASET/test/image_L/'
DirR = '/content/MyDrive/MyDrive/2TUNet/IC3D2021_2T_UNET/DATASET/test/image_R/'
saveResults = '/content/MyDrive/MyDrive/Nov 2TUNet/Result/ResNetEnc SE Dark Channel/'
leftImages = [DirL + image for image in sorted(os.listdir(DirL))]
rightImages = [DirR + image for image in sorted(os.listdir(DirR))]
from PIL import Image

th, tw = 256, 512
for i in range(len(leftImages)):
#for i in range(395,440):


        #print(range(len(leftImages)))
        #print(i)
        #print(type(Image.open(leftImages[i])))
        #print(type(Image.open(rightImages[i])))

        left_img = np.ascontiguousarray(np.array(cv2.imread(leftImages[i])), dtype=np.float32)
        right_img = np.ascontiguousarray(np.array(cv2.imread(rightImages[i])), dtype=np.float32)
        saveName = leftImages[i].split('/')[-1].split('.')[0]
        left_img = cv2.resize(left_img,(tw,th),interpolation = cv2.INTER_CUBIC)
        right_img = cv2.resize(right_img,(tw,th),interpolation = cv2.INTER_CUBIC)

        I = (left_img - left_img.min())/(left_img.max() - left_img.min())
        I = left_img.astype(np.float32);
        dark = DarkChannel(I,15);
        A = AtmLight(I,dark);
        te = TransmissionEstimate(I,A,15);
        dark_channel_prior = TransmissionRefine(left_img,te);

        dark_channel_prior = np.expand_dims(dark_channel_prior, axis=0).astype(np.float32)
        dark_channel_prior = torch.from_numpy(np.array(dark_channel_prior))

        l = np.rint(255*(left_img-left_img.min())/(left_img.max()-left_img.min()))
        r = np.rint(255*(right_img-right_img.min())/(right_img.max()-right_img.min()))
        l = np.transpose(l,(2,0,1))
        r = np.transpose(r,(2,0,1))

        l = torch.unsqueeze(torch.from_numpy(l),0)
        r = torch.unsqueeze(torch.from_numpy(r),0)
        dark_channel_prior = torch.unsqueeze(dark_channel_prior,0)

        #print(type(l))
        #print(type(r))
        #print(type(dark_channel_prior))

        #print(l.shape)
        #print(r.shape)
        #print(dark_channel_prior.shape)
        
        if torch.cuda.is_available():
            l, dark_prior, r  = l.cuda(), dark_channel_prior.cuda(), r.cuda() 
        predicted_depth_stereo =torch.squeeze(model(l, dark_prior, r)).detach().cpu().numpy()
        im = Image.fromarray(predicted_depth_stereo)
        im.show()
        im = im.convert('L')

        #print(im.size)
        #print(im)
        im.save(saveResults + saveName + '.png') 
        #im.save(saveResults + saveName + '.png')  
        #break     
