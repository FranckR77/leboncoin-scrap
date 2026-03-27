import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import os
from datetime import datetime

def train_model(gold_file: str, model_dir="./datalake/models"):
    """
    Step 11 & 14: Modélisation avec Pipeline automatisé
    Entraîne un modèle Random Forest et préprocesse les catégories avec OneHotEncoder.
    """
    os.makedirs(model_dir, exist_ok=True)
    
    print(f"[MODEL] Loading Gold data from {gold_file}...")
    df = pd.read_parquet(gold_file)
    
    # 1. Sélection des colonnes
    categorical_cols = ['city', 'type', 'category']
    numeric_cols = ['surface', 'suspicious', 'score', 'has_image', 'day_of_week', 'month', 'is_weekend']
    
    cat_features = [c for c in categorical_cols if c in df.columns]
    num_features = [c for c in numeric_cols if c in df.columns]
    
    # 2. Préparation des données X, y
    y = df['price'].fillna(df['price'].median())
    X = df[cat_features + num_features].copy()
    
    # Nettoyage basique
    X[num_features] = X[num_features].fillna(0)
    X[cat_features] = X[cat_features].fillna('Unknown').astype(str)
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 3. Création du Pipeline (scikit-learn)
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', 'passthrough', num_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), cat_features)
        ])
        
    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
    ])
    
    # 4. Entraînement
    print(f"[MODEL] Training Pipeline on {len(X_train)} ads...")
    model.fit(X_train, y_train)
    
    # 5. Évaluation
    print(f"[MODEL] Evaluating model on {len(X_test)} unseen ads...")
    y_pred = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    print()
    print("=" * 30)
    print("       MODEL EVALUATION")
    print("=" * 30)
    print(f"MAE (Erreur Moyenne) : {mae:.2f} €")
    print(f"RMSE (Écart quad)    : {rmse:.2f} €")
    print(f"R² (Précision)       : {r2:.4f}")
    print("=" * 30)
    print()
    
    # 6. Sauvegarde du Pipeline complet (Modèle + Encodage)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    model_path = f"{model_dir}/rf_price_pipeline_{timestamp}.joblib"
    joblib.dump(model, model_path)
    print(f"[MODEL] Pipeline successfully saved to {model_path}")
    
    return model_path

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        train_model(sys.argv[1])
    else:
        print("Veuillez spécifier le chemin du fichier Gold (.parquet) en paramètre.")
