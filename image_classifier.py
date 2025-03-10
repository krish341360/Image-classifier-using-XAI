# -*- coding: utf-8 -*-
"""IMAGE CLASSIFIER.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1PpN8CykRkx0KIkpu1KuhlCYo-RCS1cfr
"""

! pip install kaggle
! mkdir ~/.kaggle
! cp kaggle.json ~/.kaggle/
! chmod 600 ~/.kaggle/kaggle.json
! kaggle datasets download -d emmarex/plantdisease
! unzip plantdisease.zip

import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split

# !unzip plantVillage.zip -d /content/

# # Load the dataset
data_dir = '/content/PlantVillage'  # Adjust this path
categories = os.listdir(data_dir)

# Initialize data and labels
data = []
labels = []

# Load images and labels
for category in categories:
    category_path = os.path.join(data_dir, category)
    for img in os.listdir(category_path):
        img_path = os.path.join(category_path, img)
        image = cv2.imread(img_path)
        if image is not None:  # Check if image loaded correctly
            image = cv2.resize(image, (64, 64))  # Resize images
            data.append(image)
            labels.append(categories.index(category))


data = np.array(data) / 255.0  # Normalize
labels = np.array(labels)

# Split the dataset
X_train, X_val, y_train, y_val = train_test_split(data, labels, test_size=0.2, random_state=42)

"""CNN MODEL"""

import tensorflow as tf
from tensorflow.keras import layers, models

# Build the model
model = models.Sequential([
    layers.Conv2D(32, (3, 3), activation='relu', input_shape=(64, 64, 3)),
    layers.MaxPooling2D(pool_size=(2, 2)),
    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.MaxPooling2D(pool_size=(2, 2)),
    layers.Conv2D(128, (3, 3), activation='relu'),
    layers.MaxPooling2D(pool_size=(2, 2)),
    layers.Flatten(),
    layers.Dense(128, activation='relu'),
    layers.Dense(len(categories), activation='softmax')
])

# Compile the model
model.compile(loss='sparse_categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

history = model.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=10, batch_size=64)

import pickle as pk
pk.dump(model, open('model_1.pkl', 'wb'))

import pickle as pk
model = pk.load(open('/content/model_1.pkl', 'rb'))

loss, accuracy = model.evaluate(X_val, y_val)
print(f"Validation Accuracy: {accuracy * 100:.2f}%")

"""RESNET50 MODEL"""

import numpy as np
from tensorflow.keras.utils import to_categorical

# Normalize the pixel values to be between 0 and 1
X_train = X_train / 255.0
X_val = X_val / 255.0

# One-hot encode the labels if not already done
num_classes = len(np.unique(y_train))  # Set num_classes based on your dataset
y_train = to_categorical(y_train, num_classes)
y_val = to_categorical(y_val, num_classes)

print(f"X_train shape: {X_train.shape}")
print(f"X_val shape: {X_val.shape}")
print(f"y_train shape: {y_train.shape}")
print(f"y_val shape: {y_val.shape}")

import tensorflow as tf
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten, GlobalAveragePooling2D
from tensorflow.keras.optimizers import Adam

# Define input shape based on the image size (for example, 128x128 with 3 color channels)
input_shape = (64, 64, 3)

# Load the ResNet50 model with pre-trained ImageNet weights, excluding the top classification layers
resnet_base = ResNet50(weights='imagenet', include_top=False, input_shape=input_shape)

# Create a new model on top of ResNet50
model2 = Sequential()
model2.add(resnet_base)
model2.add(GlobalAveragePooling2D())  # Global Average Pooling layer to reduce dimensions
model2.add(Dense(128, activation='relu'))  # Add a fully connected layer
model2.add(Dense(num_classes, activation='softmax'))  # Output layer for classification

# Freeze the ResNet base layers (Optional: you can fine-tune them later)
for layer in resnet_base.layers:
    layer.trainable = False

# Compile the model
model2.compile(optimizer=Adam(learning_rate=0.001),
              loss='categorical_crossentropy',
              metrics=['accuracy'])

# Display the model architecture
# model.summary()

# Train the model
history = model2.fit(
    X_train, y_train,
    epochs=5,
    batch_size=64,
    validation_data=(X_val, y_val),
    verbose=1
)

# Evaluate the model on validation set
val_loss, val_acc = model2.evaluate(X_val, y_val, verbose=2)
print(f"Validation accuracy: {val_acc * 100:.2f}%")

import pickle as pk
pk.dump(model2, open('model_2.pkl', 'wb'))

import pickle as pk
model = pk.load(open('/content/model_1.pkl', 'rb'))

"""SALIENCY MAP"""

import tensorflow as tf
from tensorflow.keras import layers, models
def get_saliency_map(model, image, class_index):
    image = tf.convert_to_tensor(image)
    image = tf.expand_dims(image, axis=0)
    with tf.GradientTape() as tape:
        tape.watch(image)
        preds = model(image)
        loss = preds[0][class_index]
    grads = tape.gradient(loss, image)
    saliency = tf.reduce_max(tf.abs(grads), axis=-1)
    return saliency.numpy()[0]

# Example usage
test_image = X_val[5]
predicted_class = np.argmax(model.predict(np.expand_dims(test_image, axis=0)))

saliency_map = get_saliency_map(model, test_image, predicted_class)

def plot_saliency(image, saliency):
    plt.imshow(image)
    plt.imshow(saliency, cmap='jet', alpha=0.5)  # Overlay
    plt.axis('off')
    plt.show()

plot_saliency(test_image, saliency_map)

import pickle
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
import cv2

import tensorflow as tf
def preprocess_image_array(image_array, target_size=(64, 64)):
    # If the image needs resizing, do so here (optional, depending on your model input size)
    img = tf.image.resize(image_array, target_size)

    # Normalize the image (assuming pixel values range between 0-255)
    img = img / 255.0  # Normalize to [0,1]

    # Expand dimensions to match model input format (batch_size, height, width, channels)
    img = np.expand_dims(img, axis=0)

    return img

# Use the modified function
img_array = preprocess_image_array(X_val[0], target_size=(64, 64))

import tensorflow as tf
def get_img_array(img_path, size):
    # `img` is a PIL image of size 299x299
    img = tf.keras.utils.load_img('/content/PlantVillage/Pepper__bell___Bacterial_spot/0022d6b7-d47c-4ee2-ae9a-392a53f48647___JR_B.Spot 8964.JPG', target_size=size)
    # `array` is a float32 Numpy array of shape (299, 299, 3)
    array = tf.keras.utils.img_to_array(img)
    # We add a dimension to transform our array into a "batch"
    # of size (1, 299, 299, 3)
    array = np.expand_dims(array, axis=0)
    return array



"""LIME MODEL"""

!pip install lime

import numpy as np
from lime import lime_image
from skimage.segmentation import mark_boundaries
import matplotlib.pyplot as plt

# Define preprocess function (if applicable)
def preprocess_image(image):
    return image / 255.0  # Normalize the image to the same range as during training

# Prediction function that handles batches
def predict_fn(images):
    # Apply preprocessing to all images in the batch
    processed_images = np.array([preprocess_image(image) for image in images])

    # Use your pre-trained model to predict (ensure batch processing is supported)
    return model.predict(processed_images)  # This should return predictions for the batch

# Initialize LIME Image Explainer
explainer = lime_image.LimeImageExplainer()

# Generate explanation for the image
explanation = explainer.explain_instance(X_val[0], predict_fn, top_labels=5, hide_color=0, num_samples=800)

# Visualize the explanation for the top predicted class
temp, mask = explanation.get_image_and_mask(explanation.top_labels[0], positive_only=True, num_features=5, hide_rest=False)

# Display the image with highlighted explanation
plt.imshow(mark_boundaries(temp, mask))
plt.show()







"""SHAP MODEL"""

from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.vgg16 import preprocess_input

# Load and preprocess the image
img_path = '/content/PlantVillage/Pepper__bell___Bacterial_spot/0022d6b7-d47c-4ee2-ae9a-392a53f48647___JR_B.Spot 8964.JPG'
img = image.load_img(img_path, target_size=(64, 64))  # Resize image as per model's input
img_array = image.img_to_array(img)
# img_array = preprocess_input(img_array)
img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension

!pip install shap

import shap
import numpy as np

# Create a SHAP GradientExplainer
explainer = shap.GradientExplainer(model, img_array)

# Generate SHAP values for the preprocessed image
shap_values = explainer.shap_values(img_array)

# Visualize the SHAP values
shap.image_plot(shap_values, img_array)

