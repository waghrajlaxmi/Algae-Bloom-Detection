import numpy as np
import pandas as pd
import joblib

# Load your trained model and label encoder
model = joblib.load('trained_model.pkl')  # Load your trained model using the correct filename
label_encoder = joblib.load('label_encoder.pkl')  # Load your trained label encoder using the correct filename

# Define the ranges for each parameter
ph_range = (8.5, 9.5)
temperature_range = (25.5, 30)
tds_range = (250, 360)
turbidity_range = (5, 100)

# Assuming you have real-time data as variables: real_time_ph, real_time_temperature, real_time_tds, real_time_turbidity
real_time_ph = 9.5
real_time_temperature = 28
real_time_tds = 252
real_time_turbidity = 5

# Check if all parameters are within the specified ranges
if (ph_range[0] <= real_time_ph <= ph_range[1]) and \
   (temperature_range[0] <= real_time_temperature <= temperature_range[1]) and \
   (tds_range[0] <= real_time_tds <= tds_range[1]) and \
   (turbidity_range[0] <= real_time_turbidity <= turbidity_range[1]):

    # Prepare the real-time data in the same format as your training data
    real_time_data = np.array([[real_time_ph, real_time_temperature, real_time_tds, real_time_turbidity]])
    
    # Make predictions using the loaded model
    predicted_numerical = model.predict(real_time_data)
    
    # Convert the predicted numeric label to integer
    predicted_numerical = np.round(predicted_numerical).astype(int)
    
    # Convert the predicted numeric label back to the original categorical label
    predicted_category = label_encoder.inverse_transform(predicted_numerical)
    
    print(f"Predicted category for real-time data: {predicted_category[0]}")
    print("Algae is present")
else:
    print("Warning: Real-time data is out of specified parameter ranges.")

    
# # Create a DataFrame for visualization
# data = {'Prediction': ['Algae Not Present', 'Algae Present'],
#         'Probability': [1 - predicted_numerical[0], predicted_numerical[0]]}
# df = pd.DataFrame(data)

# # Set the style of seaborn
# sns.set(style="whitegrid")

# # Create a bar plot using Seaborn
# plt.figure(figsize=(6, 4))
# sns.barplot(x='Prediction', y='Probability', data=df, palette=["red", "green"])
# plt.ylim(0, 1)  # Set y-axis limit from 0 to 1 for probability
# plt.xlabel('Prediction')
# plt.ylabel('Probability')
# plt.title('Algae Presence Prediction')
# plt.show()