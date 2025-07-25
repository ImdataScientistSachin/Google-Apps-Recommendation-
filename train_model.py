import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import hstack, csr_matrix
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os
import logging
from app.recommender import AppRecommender

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def train_and_save_model():
    """Train and save the model components."""
    try:
        # Initialize the recommender to get the data
        recommender = AppRecommender()
        
        # Get the apps data
        apps_data = recommender.apps_data
        
        if apps_data is None or len(apps_data) == 0:
            raise ValueError("No data available for training")
        
        logger.info(f"Training model with {len(apps_data)} apps")
        
        # Create and fit the vectorizer
        vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        text_features = vectorizer.fit_transform(apps_data['Features'])
        logger.info("Created text features")
        
        # Create and fit the scaler
        scaler = MinMaxScaler()
        numerical_features = scaler.fit_transform(
            apps_data[['Rating', 'Reviews', 'Size', 'Installs']].fillna(0)
        )
        logger.info("Created numerical features")
        
        # Create and fit the encoder
        encoder = OneHotEncoder(sparse=False)
        categorical_features = encoder.fit_transform(
            apps_data[['Category', 'Content Rating', 'Type']].fillna('Unknown')
        )
        logger.info("Created categorical features")
        
        # Combine all features
        combined_features = hstack([text_features, numerical_features, categorical_features])
        
        # Create similarity matrix
        similarity_matrix = cosine_similarity(combined_features)
        similarity_matrix = csr_matrix(similarity_matrix)
        logger.info("Created similarity matrix")
        
        # Save the components
        models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
        os.makedirs(models_dir, exist_ok=True)
        
        # Save vectorizer
        with open(os.path.join(models_dir, 'tfidf_vectorizer.pkl'), 'wb') as f:
            pickle.dump(vectorizer, f)
        logger.info("Saved vectorizer")
        
        # Save scaler
        with open(os.path.join(models_dir, 'minmax_scaler.pkl'), 'wb') as f:
            pickle.dump(scaler, f)
        logger.info("Saved scaler")
        
        # Save encoder
        with open(os.path.join(models_dir, 'onehot_encoder.pkl'), 'wb') as f:
            pickle.dump(encoder, f)
        logger.info("Saved encoder")
        
        # Save similarity matrix
        with open(os.path.join(models_dir, 'similarity_matrix.pkl'), 'wb') as f:
            pickle.dump(similarity_matrix, f)
        logger.info("Saved similarity matrix")
        
        logger.info("Model training and saving completed successfully")
        
    except Exception as e:
        logger.error(f"Error training and saving model: {str(e)}")
        raise

if __name__ == "__main__":
    train_and_save_model() 