# ml/train.py
import pandas as pd
import pymysql
import pickle
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor

from config.settings import DB_HOST, DB_USER, DB_PASS, DB_NAME, DB_PORT

def load_data():
    conn = pymysql.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASS,
        database=DB_NAME, port=DB_PORT
    )

    df = pd.read_sql("SELECT city, zipcode, region, category, type, price FROM ads WHERE price IS NOT NULL", conn)
    conn.close()
    return df

def train_model():
    print("Training model…")

    try:
        df = load_data()
        print(f"Dataset loaded: {len(df)} rows")

        X = df.drop("price", axis=1)
        y = df["price"]

        categorical = ["city", "zipcode", "region", "category", "type"]

        preprocessor = ColumnTransformer(
            transformers=[
                ("cat", OneHotEncoder(handle_unknown="ignore"), categorical)
            ]
        )

        model = Pipeline(
            steps=[
                ("preprocess", preprocessor),
                ("model", RandomForestRegressor(n_estimators=200))
            ]
        )

        model.fit(X, y)

        with open("ml/model.pkl", "wb") as f:
            pickle.dump(model, f)

        print("Model trained and saved.")

    except Exception as e:
        print("🔥 ERROR while training model:", e)

if __name__ == "__main__":
    train_model()