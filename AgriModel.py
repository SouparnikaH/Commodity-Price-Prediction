import numpy as np
import pandas as pd
import pickle
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split


data = pd.read_csv("csvFiles/AgriCommodityData.csv")


label_encoder_commodity = LabelEncoder()
data['Commodity_encoded'] = label_encoder_commodity.fit_transform(data['Commodity'])

label_encoder_brand = LabelEncoder()
data['Brand_Name_encoded'] = label_encoder_brand.fit_transform(data['Brand Name'])

# separate features and target
X = data[['Commodity_encoded', 'Brand_Name_encoded', 'Quantity']].values
y = data['Price'].values

# Split the dataset
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=0)

# Train a Random Forest Regressor
regressor = RandomForestRegressor(n_estimators=10, random_state=0)
regressor.fit(X_train, y_train)

# Save the regressor and label encoders
with open("Agrimodel.pkl", "wb") as model_file:
    pickle.dump((regressor, label_encoder_commodity, label_encoder_brand), model_file)
