import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import hstack, csr_matrix
from sklearn.metrics.pairwise import cosine_similarity
import pickle
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class App(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    rating = db.Column(db.Float)
    reviews = db.Column(db.Integer)
    size = db.Column(db.String(20))
    installs = db.Column(db.String(20))
    content_rating = db.Column(db.String(20))
    genres = db.Column(db.String(100))
    # Add relationship to reviews
    app_reviews = db.relationship('Review', backref='app', lazy=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Add relationship to reviews
    user_reviews = db.relationship('Review', backref='user', lazy=True)

# Add to existing models.py
from datetime import datetime

# Keep existing App model

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    app_id = db.Column(db.Integer, db.ForeignKey('app.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 star rating
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Add relationship to App model
    app = db.relationship('App', backref=db.backref('reviews', lazy=True))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Nullable for imported reviews
    rating = db.Column(db.Integer, nullable=False)  # 1-5 star rating
    title = db.Column(db.String(100))
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    helpful_count = db.Column(db.Integer, default=0)
    source = db.Column(db.String(20), default='user')  # 'user', 'import', 'api'

# Keep existing functions
def load_models(model_path='AppRecom/models/random_forest_model.pkl',
                scaler_path='AppRecom/models/minmax_scaler.pkl',
                encoder_path='AppRecom/models/onehot_encoder.pkl',
                tfidf_path='AppRecom/models/tfidf_vectorizer.pkl'):
    """Loads the pre-trained models and components."""
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
    with open(encoder_path, 'rb') as f:
        encoder = pickle.load(f)
    with open(tfidf_path, 'rb') as f:
        tfidf_vectorizer = pickle.load(f)

    return model, scaler, encoder, tfidf_vectorizer

def preprocess_new_app(app_name, dataset, numerical_features, categorical_features, scaler, encoder, tfidf_vectorizer, X_train):
    """Preprocesses a new app for recommendation."""
    try:
        app_data = dataset[dataset['App'] == app_name].iloc[0].to_frame().T  # Get app data
        app_data = app_data.drop('Rating', axis=1)  # Remove rating

        # Ensure 'Features' column exists
        if 'Features' not in app_data.columns:
            app_data['Features'] = app_data['Category'].astype(str) + ' ' + app_data['Genres'].astype(str) + ' ' + app_data['App'].astype(str)

        # Impute, scale, and encode
        for col in numerical_features:
            app_data[col] = app_data[col].fillna(X_train[col].median())
        numerical_scaled_app = scaler.transform(app_data[numerical_features])
        encoded_data_app = encoder.transform(app_data[categorical_features])
        tfidf_matrix_app = tfidf_vectorizer.transform(app_data['Features'])

        # Convert to sparse matrices
        numerical_scaled_app_sparse = csr_matrix(numerical_scaled_app)
        encoded_data_app_sparse = csr_matrix(encoded_data_app)
        tfidf_matrix_app = csr_matrix(tfidf_matrix_app)

        # Combine features
        combined_features_app = hstack([tfidf_matrix_app, numerical_scaled_app_sparse, encoded_data_app_sparse])
        return combined_features_app
    except Exception as e:
        raise ValueError(f"Error preprocessing app data: {str(e)}")

def recommend_apps(app_name, dataset, model, scaler, encoder, tfidf_vectorizer, numerical_features, categorical_features, X_train, combined_features_train, num_recommendations=5):
    """Recommends similar apps based on feature similarity."""
    try:
        combined_features_app = preprocess_new_app(app_name, dataset, numerical_features, categorical_features, scaler, encoder, tfidf_vectorizer, X_train)
        
        # Add dimension check before proceeding
        if combined_features_app.shape[1] != combined_features_train.shape[1]:
            logger.error(f"Feature mismatch: App features shape {combined_features_app.shape} vs Train features shape {combined_features_train.shape}")
            raise ValueError("Feature dimension mismatch")

        # Make Prediction
        predicted_rating = model.predict(combined_features_app)[0]

        #Compute Similarity
        similarity_scores = cosine_similarity(combined_features_app, combined_features_train)
        similar_app_indices = similarity_scores.argsort()[0][-(num_recommendations + 1):-1][::-1]

        # Print Results
        recommended_apps = X_train.iloc[similar_app_indices]['App'].values
        return {
            'predicted_rating': float(predicted_rating),
            'recommended_apps': recommended_apps.tolist()
        }
    except IndexError:
        return {'error': f"App '{app_name}' not found in the dataset."}
    except Exception as e:
        return {'error': f"An error occurred: {str(e)}"}

    def predict(self, features):
        if not hasattr(self, 'model'):
            raise RuntimeError("Model not loaded - verify model files in /models directory")
        try:
            return self.model.predict(features)
        except Exception as e:
            self.logger.error(f"Prediction error: {str(e)}")
