import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import joblib
import os

# Load dataset
df = pd.read_csv("data/ipv6_training_dataset.csv")

# Features
X = df[["APNIC", "Google", "Cloudflare", "IPv6_Pulse"]]

# Target
y = df["adoption_score"]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Random Forest model
model = RandomForestRegressor(
    n_estimators=300,
    max_depth=6,
    random_state=42
)

# Train model
model.fit(X_train, y_train)

# Evaluate model
score = model.score(X_test, y_test)

print("Random Forest R² Score:", score)

# Create models folder if not exists
os.makedirs("models", exist_ok=True)

# Save model
joblib.dump(model, "models/ipv6_adoption_model.pkl")

print("Model saved → models/ipv6_adoption_model.pkl")