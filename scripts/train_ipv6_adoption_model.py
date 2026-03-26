import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
import joblib
import os
import numpy as np

# Load dataset
DATA_PATH = "data/ipv6_training_dataset.csv"
if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"Missing {DATA_PATH}. Run export script first.")

df = pd.read_csv(DATA_PATH)

# Feature selection (Truly Independent)
FEATURES = ["year", "Google", "Cloudflare", "IPv6_Pulse"]
X = df[FEATURES]
y = df["adoption_score"]
weights = df["samples"]

# Train-test split (with weights)
indices = np.arange(len(df))
X_train, X_test, y_train, y_test, w_train, w_test = train_test_split(
    X, y, weights, test_size=0.2, random_state=42
)

# Random Forest model with Hyperparameter Tuning
rf = RandomForestRegressor(random_state=42)
param_grid = {
    'n_estimators': [100, 300, 500],
    'max_depth': [4, 6, 8, None],
    'min_samples_leaf': [1, 2]
}

print("Running Weighted Random Forest Training with GridSearchCV...")
grid_search = GridSearchCV(estimator=rf, param_grid=param_grid, cv=3, n_jobs=-1, scoring='r2')
grid_search.fit(X_train, y_train, sample_weight=w_train)

model = grid_search.best_estimator_
print(f"Best Parameters: {grid_search.best_params_}")

# Evaluate model
score = model.score(X_test, y_test, sample_weight=w_test)
print(f"Robust Real AI R^2 Score: {score:.4f}")

# Log Feature Importances (The Real Proof of Independence)
importances = model.feature_importances_
print("\n--- Feature Importances (Source Significance) ---")
for feat, imp in zip(FEATURES, importances):
    print(f"{feat:12}: {imp*100:6.2f}%")
print("------------------------------------------------\n")

# Create models folder if not exists
os.makedirs("models", exist_ok=True)

# Save model
MODEL_PATH = "models/ipv6_adoption_model.pkl"
joblib.dump(model, MODEL_PATH)
print(f"Real AI Model saved -> {MODEL_PATH}")