# TensorFlow

TensorFlow 是 Google 開發的深度學習框架，支援大規模部署。

## 基本操作

```python
import tensorflow as tf

# 張量
x = tf.constant([[1., 2.], [3., 4.]])

# 運算
y = x + 1
z = tf.matmul(x, x)

# 自動微分
with tf.GradientTape() as tape:
    y = x ** 2
grad = tape.gradient(y, x)
```

## Keras API

```python
from tensorflow import keras

model = keras.Sequential([
    keras.layers.Dense(256, activation='relu', input_shape=(784,)),
    keras.layers.Dense(10, activation='softmax')
])

model.compile(
    optimizer='adam',
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

model.fit(x_train, y_train, epochs=10)
```

## TensorFlow Lite

```python
# 轉換為行動裝置格式
converter = tf.lite.TFLiteConverter.from_saved_model(model_dir)
tflite_model = converter.convert()
```

## 相關概念

- [PyTorch](工具/PyTorch.md)
- [深度學習](概念/深度學習.md)