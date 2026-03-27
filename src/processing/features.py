import pandas as pd
import numpy as np

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Step 6: Feature Engineering.
    Ajoute des variables prédictives à partir des colonnes brutes.
    """
    df = df.copy()

    # 1. Ratio : Prix au mètre carré (optionnel, on garde pour l'analyse)
    if 'price' in df.columns and 'surface' in df.columns:
        df["price_per_m2"] = df["price"] / df["surface"]
        df["price_per_m2"] = df["price_per_m2"].replace([np.inf, -np.inf], np.nan)

    # 2. Variables temporelles
    if 'created_at' in df.columns:
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['day_of_week'] = df['created_at'].dt.dayofweek
        df['month'] = df['created_at'].dt.month
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)

    # 3. Indicateur binaire
    if "image_url" in df.columns:
        df["has_image"] = df["image_url"].notna().astype(int)

    return df
