import numpy as np
import random
import math
from collections import deque
from itertools import count

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

import agent

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")