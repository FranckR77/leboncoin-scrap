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
import json
from datetime import datetime

def train_model(gold_file: str, model_dir="./datalake/models"):
    """
    Step 11 & 14: Modélisation avec Pipeline automatisé
    Entraîne un modèle Random Forest et préprocesse les catégories avec OneHotEncoder.
    """
    os.makedirs(model_dir, exist_ok=True)
    
    print(f"[MODEL] Loading Gold data from {gold_file}...")
    df = pd.read_parquet(gold_file)
    
    # 1. Nettoyage Drastique & Filtrage
    df = df[df['suspicious'] == 0].copy()
    
    # EXTRACTION DU DEPARTEMENT
    df['dept'] = df['zipcode'].astype(str).str.strip().str[:2]
    df['pm2'] = df['price'] / df['surface']
    
    # Filtrage Drastique (Price/m2)
    df = df[(df['pm2'] >= 600) & (df['pm2'] <= 11000)]
    df = df[(df['price'] >= 50000) & (df['price'] <= 1100000)]
    df = df[(df['surface'] >= 10) & (df['surface'] <= 350)]

    # --- NOUVEAU : CLUSTERING K-MEANS --- 
    # Objectif : Créer 12 Segments de Marché basés sur le PM2 médian par zone
    # On groupe par (Dept, City) pour plus de précision
    from sklearn.cluster import KMeans
    
    # Calcul des PM2 médians
    geo_stats = df.groupby(['dept', 'city'])['pm2'].median().reset_index()
    
    # K-Means (12 clusters comme demandé)
    kmeans = KMeans(n_clusters=12, random_state=42)
    geo_stats['market_cluster'] = kmeans.fit_predict(geo_stats[['pm2']])
    
    # On réintègre les clusters dans le dataframe principal
    df = df.merge(geo_stats[['dept', 'city', 'market_cluster']], on=['dept', 'city'], how='left')
    
    # Sauvegarde du Cluster Mapping pour la prédiction
    mapping_path = f"{model_dir}/market_clusters_v1.json"
    with open(mapping_path, "w") as f:
        clean_map = {f"{row.dept}_{row.city}": int(row.market_cluster) for _, row in geo_stats.iterrows()}
        json.dump({"map": clean_map, "global_median_cluster": int(geo_stats['market_cluster'].median())}, f)

    # 2. Sélection des colonnes
    # 'market_cluster' remplace ici la ville brute (moins de bruit, plus de sens)
    categorical_cols = ['dept', 'region', 'type', 'category'] 
    numeric_cols = ['surface', 'market_cluster', 'score', 'has_image']
    
    cat_features = [c for c in categorical_cols if c in df.columns]
    num_features = [c for c in numeric_cols if c in df.columns]
    
    # 3. Préparation des données X, y
    y = np.log1p(df['price']) 
    X = df[cat_features + num_features].copy()
    
    # Remplissage simple des valeurs manquantes
    X[num_features] = X[num_features].fillna(0)
    X[cat_features] = X[cat_features].fillna('Unknown').astype(str)
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
    
    # 4. Création du Pipeline (Optimisé pour Clustering)
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', 'passthrough', num_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), cat_features)
        ])
        
    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(n_estimators=600, max_depth=25, min_samples_split=4, random_state=42))
    ])
    
    # 5. Entraînement
    print(f"[MODEL] Training with Target Encoding (City PM2)...")
    model.fit(X_train, y_train)
    
    # 6. Évaluation
    y_pred_log = model.predict(X_test)
    y_pred = np.expm1(y_pred_log)
    y_test_orig = np.expm1(y_test)
    
    mae = mean_absolute_error(y_test_orig, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test_orig, y_pred))
    r2 = r2_score(y_test_orig, y_pred)

    # 7. Importance des Features (poids)
    importance = model.named_steps['regressor'].feature_importances_
    # On affiche juste les principaux numeric
    print("Feature importance (Numeric):")
    for name, imp in zip(num_features, importance[:len(num_features)]):
        print(f" - {name}: {imp:.4f}")
    
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

    # 7. Sauvegarde des métriques pour consultation ultérieure
    metrics = {
        "timestamp": timestamp,
        "model_type": "RandomForestRegressor",
        "n_samples_train": len(X_train),
        "n_samples_test": len(X_test),
        "mae": float(mae),
        "rmse": float(rmse),
        "r2": float(r2),
        "features": {
            "categorical": cat_features,
            "numeric": num_features
        }
    }
    metrics_path = f"{model_dir}/metrics_latest.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=4)
    
    # Save a historical version too
    with open(f"{model_dir}/metrics_{timestamp}.json", "w") as f:
        json.dump(metrics, f, indent=4)

    print(f"[MODEL] Metrics saved to {metrics_path}")
    
    return model_path

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        train_model(sys.argv[1])
    else:
        print("Veuillez spécifier le chemin du fichier Gold (.parquet) en paramètre.")
