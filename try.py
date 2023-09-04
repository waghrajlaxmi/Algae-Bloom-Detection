import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor
import joblib
from sklearn.model_selection import train_test_split

# Load your dataset and perform necessary preprocessing
data1 = pd.read_csv('sensorDataFile.csv')

# Extract features (X) and target (y)
X = data1[['ph', 'temperature', 'tds', 'turbidity']]
y_categorical = data1['dependent_values']

# Convert categorical labels to numeric labels using LabelEncoder
label_encoder = LabelEncoder()
y_numerical = label_encoder.fit_transform(y_categorical)

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y_numerical, test_size=0.2, random_state=42)

# Create an instance of the RandomForestRegressor model
model = RandomForestRegressor(n_estimators=100, random_state=42)

# Train the model
model.fit(X_train, y_train)

# Save the trained model to a file
model_filename = 'trained_model.pkl'
joblib.dump(model, model_filename)

# Save the label encoder to a file
label_encoder_filename = 'label_encoder.pkl'
joblib.dump(label_encoder, label_encoder_filename)


