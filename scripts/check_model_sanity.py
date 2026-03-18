import joblib
import os

def check_model():
    model_path = os.path.join(os.getcwd(), 'models', 'ipv6_adoption_model.pkl')
    if os.path.exists(model_path):
        model = joblib.load(model_path)
        print(f"Model type: {type(model)}")
        if hasattr(model, 'feature_names_in_'):
            print(f"Feature names: {model.feature_names_in_}")
        else:
            print("Model has no feature_names_in_ attribute.")
        
        # Test a prediction
        import numpy as np
        # [APNIC, Google, Cloudflare]
        # X = df[["APNIC", "Google", "Cloudflare"]]
        test_in = [[67.2, 62.1, 71.5]]
        pred = model.predict(test_in)[0]
        print(f"Prediction for IN [67.2, 62.1, 71.5]: {pred}")

if __name__ == "__main__":
    check_model()
