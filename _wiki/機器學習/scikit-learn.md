# scikit-learn

scikit-learn 是 Python 的機器學習經典庫，適合傳統 ML 演算法。

## 基本流程

```python
from sklearn import datasets
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

# 載入資料
iris = datasets.load_iris()
X, y = iris.data, iris.target

# 分割資料
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# 標準化
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# 訓練
model = LogisticRegression()
model.fit(X_train, y_train)

# 預測
pred = model.predict(X_test)
print(accuracy_score(y_test, pred))
```

## 常見模組

- **datasets**: 載入範例資料
- **model_selection**: 交叉驗證、網格搜尋
- **preprocessing**: 標準化、編碼
- **linear_model**: 線性/邏輯回歸
- **ensemble**: 隨機森林、AdaBoost
- **cluster**: K-means, DBSCAN
- **decomposition**: PCA, SVD

## 相關概念

- [監督式學習](監督式學習.md)
- [非監督式學習](非監督式學習.md)