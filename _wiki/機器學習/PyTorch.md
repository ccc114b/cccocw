# PyTorch

PyTorch 是 Facebook 開發的深度學習框架，廣泛用於研究與開發。

## 基本操作

```python
import torch

# 張量
x = torch.randn(3, 4)
y = torch.randn(3, 4)

# 運算
z = x + y
z = torch.matmul(x, y.T)

# 自動微分
x = torch.tensor([1., 2., 3.], requires_grad=True)
y = x ** 2
y.sum().backward()
print(x.grad)  # 梯度
```

## 神經網路模組

```python
import torch.nn as nn

class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(784, 10)
    
    def forward(self, x):
        return self.fc(x)

model = Net()
```

## 訓練迴圈

```python
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
criterion = nn.CrossEntropyLoss()

for epoch in range(10):
    for data, target in dataloader:
        optimizer.zero_grad()
        output = model(data)
        loss = criterion(output, target)
        loss.backward()
        optimizer.step()
```

## 相關概念

- [TensorFlow](TensorFlow.md)
- [深度學習](深度學習.md)