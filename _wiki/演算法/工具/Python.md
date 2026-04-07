# Python

Python 是一種高階程式語言，適合演算法實現與資料科學。

## 基本語法

```python
# 列表推導
squares = [x**2 for x in range(10)]

# 切片
arr[1:5]  # arr[1] 到 arr[4]

# 字典
d = {'a': 1, 'b': 2}
d.get('a', 0)  # 預設值
```

## 常用資料結構

```python
# 列表 (可變)
list = [1, 2, 3]
list.append(4)

# 集合 (無序不重複)
s = {1, 2, 3}
s.add(4)

# 字典
d = {'a': 1}
d['b'] = 2
```

## 常用模組

```python
import collections  # deque, Counter, defaultdict
import heapq       # 堆積 (優先佇列)
import bisect       # 二分搜尋
```

## 相關概念

- [資料結構](../概念/資料結構.md)