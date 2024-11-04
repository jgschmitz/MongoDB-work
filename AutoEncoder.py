#for Deere 
import numpy as np
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense

# Example data combining coordinates and displacements
data = np.array([
    [3.9976, 8.3456, 9.0123, 0.1, 0.2, 0.3],  # X, Y, Z, UX, UY, UZ
    [4.1234, 2.7890, 3.5678, 0.4, 0.1, 0.0],
    [5.6789, 1.2345, 4.2345, 0.2, 0.3, 0.5],
    [7.8901, 0.4567, 8.1234, 0.6, 0.5, 0.7]
])

# Define the autoencoder
input_layer = Input(shape=(6,))  # Input shape based on number of features
encoded = Dense(3, activation='relu')(input_layer)  # Compress to 3D embedding
decoded = Dense(6, activation='sigmoid')(encoded)   # Reconstruct original data

# Model to generate embeddings
encoder = Model(input_layer, encoded)

# Train the autoencoder
autoencoder = Model(input_layer, decoded)
autoencoder.compile(optimizer='adam', loss='mse')
autoencoder.fit(data, data, epochs=100, batch_size=1)

# Generate embeddings
embeddings = encoder.predict(data)
print(embeddings)
