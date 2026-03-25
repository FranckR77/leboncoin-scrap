import pickle
import pandas as pd

with open("ml/model.pkl", "rb") as f:
    model = pickle.load(f)

def predict_price(data: dict) -> float:
    with open("ml/model.pkl", "rb") as f:
        model = pickle.load(f)  # <--- rechargé à CHAQUE appel
    df = pd.DataFrame([data])
    return float(model.predict(df)[0])