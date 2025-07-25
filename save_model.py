import pickle
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestRegressor
from scipy.sparse import hstack, csr_matrix
import logging
import csv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_dataset():
    """Load and properly parse the dataset"""
    try:
        # Try to use the fixed dataset first
        try:
            df = pd.read_csv('data/googleplaystore_fixed.csv', encoding='utf-8-sig')
            logger.info(f"Successfully loaded fixed dataset with shape: {df.shape}")
        except FileNotFoundError:
            # If fixed file not found, try to parse the original with special handling
            df = pd.read_csv('data/googleplaystore.csv', 
                             encoding='utf-8-sig',
                             quoting=csv.QUOTE_MINIMAL,
                             escapechar='\\',
                             on_bad_lines='warn')  # For newer pandas versions
            logger.info(f"Successfully loaded original dataset with shape: {df.shape}")
        
        logger.info(f"Columns found: {df.columns.tolist()}")
        
        # Verify required columns
        required_columns = ['App', 'Category', 'Rating', 'Reviews', 'Size', 
                          'Installs', 'Type', 'Price', 'Content Rating', 'Genres']
        
        # Fix for BOM character in column name
        if '\ufeffApp' in df.columns and 'App' not in df.columns:
            df.rename(columns={'\ufeffApp': 'App'}, inplace=True)
            logger.info("Renamed '\ufeffApp' column to 'App'")
            
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
            
        return df
    
    except Exception as e:
        logger.error(f"Error loading dataset: {str(e)}")
        raise

def preprocess_data(df):
    """Preprocess the dataset"""
    try:
        # Make a copy to avoid modifying original data
        df = df.copy()
        
        # Clean Installs column
        df['Installs'] = df['Installs'].astype(str)
        df['Installs'] = df['Installs'].str.replace('[+,]', '', regex=True)
        df['Installs'] = pd.to_numeric(df['Installs'], errors='coerce')

        # Clean Price column
        df['Price'] = df['Price'].astype(str)
        df['Price'] = df['Price'].str.replace('$', '', regex=False)
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce')

        # Clean Size column
        def convert_size(size):
            try:
                if pd.isna(size) or size == 'Varies with device':
                    return np.nan
                size = str(size).upper()
                if 'M' in size:
                    return float(size.replace('M', ''))
                elif 'K' in size:
                    return float(size.replace('K', '')) / 1024
                return float(size)
            except:
                return np.nan

        df['Size'] = df['Size'].apply(convert_size)

        # Create Features column
        df['Features'] = df['Category'].fillna('') + ' ' + \
                        df['Genres'].fillna('') + ' ' + \
                        df['App'].fillna('')

        # Convert Rating to numeric first, then drop NaN values
        df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')
        
        # Remove rows with missing ratings - do this AFTER converting to numeric
        df = df.dropna(subset=['Rating'])
        
        # Fill missing values for other columns
        df['Size'].fillna(df['Size'].median(), inplace=True)
        df['Price'].fillna(0, inplace=True)
        df['Reviews'] = pd.to_numeric(df['Reviews'], errors='coerce')
        df['Reviews'].fillna(0, inplace=True)
        df['Installs'].fillna(df['Installs'].median(), inplace=True)

        # Verify no NaN values in Rating column
        if df['Rating'].isna().any():
            logger.warning(f"Found {df['Rating'].isna().sum()} NaN values in Rating after preprocessing")
            # Additional safety: remove any remaining NaN values
            df = df.dropna(subset=['Rating'])

        logger.info(f"Preprocessed data shape: {df.shape}")
        return df

    except Exception as e:
        logger.error(f"Error in preprocessing: {str(e)}")
        raise

def train_model(df):
    """Train the recommendation model"""
    try:
        # Prepare features
        numerical_features = ['Reviews', 'Size', 'Installs', 'Price']
        categorical_features = ['Type', 'Content Rating']

        # Verify no NaN values in Rating column before splitting
        if df['Rating'].isna().any():
            logger.warning(f"Found {df['Rating'].isna().sum()} NaN values in Rating before splitting")
            df = df.dropna(subset=['Rating'])
            logger.info(f"Removed rows with NaN ratings, new shape: {df.shape}")

        # Split data
        X = df.drop('Rating', axis=1)
        y = df['Rating']
        
        # Additional check for NaN values in y
        if y.isna().any():
            logger.error(f"Found {y.isna().sum()} NaN values in target variable y")
            raise ValueError("Target variable contains NaN values after preprocessing")
            
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Initialize components
        scaler = MinMaxScaler()
        encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)  # Changed sparse to sparse_output
        tfidf_vectorizer = TfidfVectorizer(stop_words='english')

        # Transform numerical features
        numerical_scaled = scaler.fit_transform(X_train[numerical_features])
        
        # Transform categorical features
        categorical_encoded = encoder.fit_transform(X_train[categorical_features])
        
        # Transform text features
        text_features = tfidf_vectorizer.fit_transform(X_train['Features'])

        # Combine features
        combined_features = hstack([
            text_features,
            csr_matrix(numerical_scaled),
            csr_matrix(categorical_encoded)
        ])

        # Final check for NaN values in y_train
        if np.isnan(y_train.values).any():
            logger.error("NaN values found in y_train after splitting")
            # Remove samples with NaN target values
            valid_indices = ~np.isnan(y_train.values)
            y_train = y_train[valid_indices]
            combined_features = combined_features[valid_indices]
            logger.info(f"Removed {(~valid_indices).sum()} samples with NaN target values")

        # Train model
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(combined_features, y_train)

        logger.info("Model training completed successfully")
        return model, scaler, encoder, tfidf_vectorizer, combined_features

    except Exception as e:
        logger.error(f"Error in model training: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        # Load and preprocess data
        dataset = load_dataset()
        dataset = preprocess_data(dataset)
        logger.info("Data preprocessing completed")

        # Train model
        model, scaler, encoder, tfidf_vectorizer, combined_features = train_model(dataset)
        logger.info("Model training completed")

        # Save components
        model_dir = os.path.join(os.path.dirname(__file__), 'models')
        os.makedirs(model_dir, exist_ok=True)

        components = {
            'random_forest_model.pkl': model,
            'minmax_scaler.pkl': scaler,      # Changed from 'scaler.pkl'
            'onehot_encoder.pkl': encoder,    # Changed from 'encoder.pkl'
            'tfidf_vectorizer.pkl': tfidf_vectorizer,  # Changed from 'tfidf.pkl'
            'combined_features_train.pkl': combined_features
        }

        for filename, component in components.items():
            filepath = os.path.join(model_dir, filename)
            with open(filepath, 'wb') as f:
                pickle.dump(component, f)
            logger.info(f"Saved: {filename}")

        logger.info("Model components saved successfully!")

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise