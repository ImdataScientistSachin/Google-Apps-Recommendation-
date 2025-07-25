import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
import pickle
import os
from typing import Optional

def load_data(data_path: Optional[str] = None):
    """Loads data from a CSV file and performs initial cleaning. If no path is provided, uses default from config."""
    if data_path is None:
        try:
            from app.config import Config
            data_path = Config.DATA_PATH
        except ImportError:
            raise FileNotFoundError("No data path provided and Config could not be imported.")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found at: {data_path}")
    df = pd.read_csv(data_path)
    return df

def preprocess_data(df):
    """Preprocesses the data for the model, imputing missing values instead of dropping them."""
    # Impute missing values
    for col in df.select_dtypes(include=['float64', 'int64']).columns:
        median = df[col].median()
        df[col] = df[col].fillna(median)
    for col in df.select_dtypes(include=['object']).columns:
        mode = df[col].mode()
        if not mode.empty:
            df[col] = df[col].fillna(mode[0])
        else:
            df[col] = df[col].fillna('Unknown')
    df = df.drop_duplicates()

    # Example: Convert categorical features to numerical using Label Encoding
    label_encoder = LabelEncoder()
    for cat_col in ['Category', 'Content Rating', 'Type']:
        if cat_col in df.columns:
            df[cat_col] = label_encoder.fit_transform(df[cat_col].astype(str))

    # Clean Installs feature and convert to numeric
    if 'Installs' in df.columns:
        df['Installs'] = df['Installs'].astype(str).str.replace(r'[+,]', '', regex=True).astype(int)

    # Convert Reviews to numeric
    if 'Reviews' in df.columns:
        df['Reviews'] = pd.to_numeric(df['Reviews'], errors='coerce').fillna(0)

    # Select relevant features (adjust based on your model)
    features = ['Category', 'Rating', 'Reviews', 'Installs', 'Type']  # Example
    X = df[features]
    y = (df['Rating'] > 4).astype(int)  # Example: predict if rating > 4

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    return X_train, X_test, y_train, y_test

def train_model(X_train, y_train):
    """Trains a logistic regression model."""
    model = LogisticRegression()
    model.fit(X_train, y_train)
    return model

def save_model(model, model_path):
    """Saves the trained model to a file."""
    with open(model_path, 'wb') as file:
        pickle.dump(model, file)
    print(f"Model saved to: {model_path}")

def load_apps_data(data_path: Optional[str] = None):
    if data_path is None:
        try:
            from app.config import Config
            data_path = Config.DATA_PATH
        except ImportError:
            raise FileNotFoundError("No data path provided and Config could not be imported.")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found at: {data_path}")
    return pd.read_csv(data_path)

def process_app_data(df):
    if 'Reviews' in df.columns:
        df['Reviews'] = pd.to_numeric(df['Reviews'], errors='coerce').fillna(0)
    return df

# Example usage (for training and saving the model):
if __name__ == '__main__':
    try:
        from config import DATA_PATH, MODEL_PATH  # Import DATA_PATH from config.py
        data = load_data(DATA_PATH)
        X_train, X_test, y_train, y_test = preprocess_data(data)
        model = train_model(X_train, y_train)
        save_model(model, MODEL_PATH)
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

