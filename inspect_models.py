import pickle
import os
from app.config import Config

def inspect_model(path, name):
    try:
        with open(path, 'rb') as f:
            model = pickle.load(f)
            print(f"Successfully loaded {name}")
            print(f"Type: {type(model)}")
            print(f"Details: {model}\n")
    except Exception as e:
        print(f"Error loading {name}: {str(e)}\n")

# Inspect all models
inspect_model(Config.TFIDF_PATH, "TF-IDF Vectorizer")
inspect_model(Config.ENCODER_PATH, "One-Hot Encoder")
inspect_model(Config.SCALER_PATH, "Min-Max Scaler")
inspect_model(Config.MODEL_PATH, "Random Forest Model")

# Check if data files exist and have the required columns
import pandas as pd

for data_path in [Config.FIXED_DATA_PATH, Config.DATA_PATH, Config.SAMPLE_DATA_PATH]:
    if os.path.exists(data_path):
        try:
            df = pd.read_csv(data_path)
            print(f"Loaded data from {data_path}")
            print(f"Columns: {df.columns.tolist()}")
            print(f"Has 'Features' column: {'Features' in df.columns}\n")
        except Exception as e:
            print(f"Error loading {data_path}: {str(e)}\n")