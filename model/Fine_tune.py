import torch
from torch import nn
import torch.nn.functional as F
from torch.utils.data import Dataset
from torch.utils.data import DataLoader
import numpy as np
import matplotlib.pyplot as plt

BATCH_SIZE = 1
SEQ_LEN = 20


# 输入Part1的批量大小应为BATCH_SIZE * SEQ_LEN


class EEGdataset(Dataset):
    def __init__(self, is_train):
        filename = 'E:/data/combine_data.txt' if is_train \
            else 'E:/test/data_7'
        data = np.loadtxt(filename, delimiter=',', dtype=np.float32)
        self.batch_size = BATCH_SIZE * SEQ_LEN
        num_batch = int(data.shape[0] / self.batch_size)
        data = data[:num_batch * self.batch_size]
        self.len = data.shape[0]
        self.x_data = torch.from_numpy(data[:, :-1])
        self.y_data = torch.LongTensor(data[:, -1])

    def __getitem__(self, index):
        return self.x_data[index], self.y_data[index]

    def __len__(self):
        return self.len


class part1(nn.Module):
    def __init__(self):
        super(part1, self).__init__()
        self.DP = nn.Dropout(0.5)
        self.cnn1 = nn.Sequential(nn.Conv1d(in_channels=1, out_channels=64, padding=(10,),
                                            kernel_size=(50,), stride=(6,)),
                                  nn.MaxPool1d(kernel_size=8, stride=8),
                                  nn.ReLU(),
                                  nn.Dropout(0.5),
                                  nn.Conv1d(64, 128, (8,), (1,), padding=(4,)), nn.ReLU(),
                                  nn.Conv1d(128, 128, (8,), (1,), padding=(4,)), nn.ReLU(),
                                  nn.Conv1d(128, 128, (8,), (1,), padding=(4,)), nn.ReLU(),
                                  nn.MaxPool1d(4, 4))
        self.cnn2 = nn.Sequential(nn.Conv1d(in_channels=1, out_channels=64, padding=(10,),
                                            kernel_size=(200,), stride=(16,)),
                                  nn.MaxPool1d(kernel_size=6, stride=6),
                                  nn.ReLU(),
                                  nn.Dropout(0.5),
                                  nn.Conv1d(64, 128, (7,), (1,), padding=(4,)), nn.ReLU(),
                                  nn.Conv1d(128, 128, (7,), (1,), padding=(4,)), nn.ReLU(),
                                  nn.Conv1d(128, 128, (7,), (1,), padding=(4,)), nn.ReLU(),
                                  nn.MaxPool1d(3, 3))
        self.cnn3 = nn.Sequential(nn.Conv1d(in_channels=1, out_channels=64, padding=(10,),
                                            kernel_size=(400,), stride=(50,)),
                                  nn.MaxPool1d(kernel_size=4, stride=4),
                                  nn.ReLU(),
                                  nn.Dropout(0.5),
                                  nn.Conv1d(64, 128, (6,), (1,), padding=(3,)), nn.ReLU(),
                                  nn.Conv1d(128, 128, (6,), (1,), padding=(3,)), nn.ReLU(),
                                  nn.Conv1d(128, 128, (6,), (1,), padding=(3,)), nn.ReLU(),
                                  nn.MaxPool1d(2, 2))
        self.encode_layer = nn.TransformerEncoderLayer(d_model=3000, nhead=8)
        self.transformer = nn.TransformerEncoder(self.encode_layer, num_layers=2)

    def forward(self, x):
        x = x.view(BATCH_SIZE * SEQ_LEN, 1, -1)
        # x_tmp1 = torch.tensor([[0] * 1480] * BATCH_SIZE*SEQ_LEN)
        # x_tmp2 = x.view(BATCH_SIZE*SEQ_LEN, -1)
        # x_add = torch.cat((x_tmp1, x_tmp2), dim=1)
        #
        # x = self.transformer(x)

        x1 = self.cnn1(x)  # x1的size为BATCH_SIZE*128*16
        x2 = self.cnn2(x)  # x2的size为BATCH_SIZE*128*11
        x3 = self.cnn3(x)  # x3的size为BATCH_SIZE*128*8

        x1 = x1.view(BATCH_SIZE * SEQ_LEN, -1)
        x2 = x2.view(BATCH_SIZE * SEQ_LEN, -1)
        x3 = x3.view(BATCH_SIZE * SEQ_LEN, -1)

        x = torch.cat((x1, x2, x3), dim=1)
        # x = x + x_add

        return self.DP(x)  # x的size为BATCH_SIZE*4480


class part2(nn.Module):
    def __init__(self):
        super(part2, self).__init__()
        self.GRU1 = nn.GRU(input_size=4480, hidden_size=512,
                           num_layers=1, bidirectional=True)
        self.DP = nn.Dropout(0.5)
        self.GRU2 = nn.GRU(input_size=2 * 512, hidden_size=512,
                           num_layers=1, bidirectional=True)
        self.Linear = nn.Linear(4480, 1024)
        self.Relu = nn.ReLU()
        self.Tanh = nn.Tanh()

    def forward(self, x):
        x1 = x.view(SEQ_LEN, BATCH_SIZE, -1)

        x1, _ = self.GRU1(x1)
        x1 = self.DP(x1)
        x1 = self.Tanh(x1)
        x1, _ = self.GRU2(x1)
        x1 = self.DP(x1).view(SEQ_LEN * BATCH_SIZE, -1)
        x1 = self.Tanh(x1)

        x2 = self.Tanh(self.Linear(x))

        return x1 + x2


class part3(nn.Module):
    def __init__(self):
        super(part3, self).__init__()
        self.DP = nn.Dropout(0.5)
        self.Linear = nn.Linear(1024, 5)

    def forward(self, x):
        x = self.Linear(self.DP(x))
        return x


train_data = EEGdataset(is_train=True)
train_loader = DataLoader(dataset=train_data, batch_size=BATCH_SIZE * SEQ_LEN, shuffle=False)

test_data = EEGdataset(is_train=False)
test_loader = DataLoader(dataset=test_data, batch_size=BATCH_SIZE * SEQ_LEN, shuffle=False)

# =====================================================================================================
model1 = part1()
model2 = part2()
model3 = part3()
checkpoint = torch.load('C:/Users/jhon/Desktop/Sg/models/pre-train.pth')
model1.load_state_dict(checkpoint['part1'])

criterion = torch.nn.CrossEntropyLoss()
optimizer = torch.optim.Adam([{'params': model1.parameters(), 'lr': 3e-5},
                              {'params': model2.parameters(), 'lr': 3e-5},
                              {'params': model3.parameters(), 'lr': 3e-5}])
# =======================================================================================================

# ========================================= CUDA ======================================================
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
model1.to(device)
model2.to(device)
model3.to(device)
# =====================================================================================================

def train():
    running_loss, correct = 0, 0
    for idx, (inputs, labels) in enumerate(train_loader):
        inputs, labels = inputs.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model1(inputs)
        outputs = model2(outputs)
        outputs = model3(outputs)
        loss = criterion(outputs, labels)
        running_loss += loss.item()
        loss.backward()
        optimizer.step()

        _, prediction = outputs.max(dim=1)
        correct += (prediction == labels).sum().item()

    running_loss = running_loss / len(train_data)
    running_acc = correct / len(train_data)
    return running_loss, running_acc


def test():
    test_loss, correct = 0, 0

    with torch.no_grad():
        for idx, (inputs, labels) in enumerate(test_loader):
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model1(inputs)
            outputs = model3(model2(outputs))
            loss = criterion(outputs, labels)
            test_loss += loss.item()

            _, prediction = outputs.max(dim=1)
            correct += (prediction == labels).sum().item()

    test_loss = test_loss / len(test_data)
    test_acc = correct / len(test_data)
    return test_loss, test_acc


epoch_list = []
loss_list = []
acc_list = []
test_loss_list = []
test_acc_list = []
for epoch in range(100):
    running_loss, running_acc = train()

    print('Epoch : %d Loss : %.3f Accuracy: %.3f' % (epoch, running_loss, running_acc))
    epoch_list.append(epoch)
    loss_list.append(running_loss)
    acc_list.append(running_acc)

    test_loss, test_acc = test()

    test_loss_list.append(test_loss)
    test_acc_list.append(test_acc)

fig = plt.figure()
ax1 = fig.add_subplot(111)
ax2 = ax1.twinx()
ax1.plot(np.array(epoch_list), np.array(loss_list),
         label='Train_loss', marker='o', linestyle='dashed', markersize=5)
ax2.plot(np.array(epoch_list), np.array(acc_list), label='Train_accuracy',
         marker='s', markersize=5)
ax1.plot(np.array(epoch_list), np.array(test_loss_list),
         label='Test_loss', marker='o', linestyle='dashed', markersize=5)
ax2.plot(np.array(epoch_list), np.array(test_acc_list), label='Test_Accuracy',
         marker='s', markersize=5)
ax1.set_ylim(0.02, 0.09)
ax1.set_xlabel('Epoch')
ax1.set_ylabel('Loss')
ax2.set_ylim(0, 1)
ax2.set_ylabel('Accuracy')
ax1.legend(loc=2)
ax2.legend(loc=0)
plt.show()
