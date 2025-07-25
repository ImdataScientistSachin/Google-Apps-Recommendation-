import pandas as pd
import numpy as np
import pickle
import os
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity
import logging
from app.config import Config

logger = logging.getLogger(__name__)

class AppRecommender:
    """
    A class to handle app recommendations based on similarity metrics.
    """
    
    def __init__(self):
        """Initialize the recommender with pre-trained models and data."""
        try:
            # Load data
            logger.info("Attempting to load data...")
            self.data = self._load_data()
            if self.data is None:
                logger.error("Failed to load data")
                raise Exception("Failed to load data")
            
            # Load models
            logger.info("Attempting to load models...")
            self.tfidf_vectorizer = self._load_model(Config.TFIDF_PATH)
            self.encoder = self._load_model(Config.ENCODER_PATH)
            self.scaler = self._load_model(Config.SCALER_PATH)
            self.model = self._load_model(Config.MODEL_PATH)
            
            if not all([self.tfidf_vectorizer, self.encoder, self.scaler, self.model]):
                missing = []
                if not self.tfidf_vectorizer: missing.append("TF-IDF vectorizer")
                if not self.encoder: missing.append("encoder")
                if not self.scaler: missing.append("scaler")
                if not self.model: missing.append("model")
                logger.error(f"Failed to load models: {', '.join(missing)}")
                raise Exception(f"Failed to load models: {', '.join(missing)}")
            
            # Create similarity matrix if data is available
            logger.info("Attempting to create similarity matrix...")
            if self.data is not None and len(self.data) > 0:
                self.similarity_matrix = self._create_similarity_matrix()
                if self.similarity_matrix is None:
                    logger.error("Failed to create similarity matrix")
                    raise Exception("Failed to create similarity matrix")
            else:
                self.similarity_matrix = None
                logger.error("No data available for similarity matrix creation")
                raise Exception("No data available for similarity matrix creation")
                
            logger.info("AppRecommender initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing AppRecommender: {str(e)}")
            self.data = None
            self.similarity_matrix = None
            raise
    
    def _load_data(self):
        """Load the app data from CSV file."""
        try:
            # Try different data paths in order of preference
            for data_path in [Config.FIXED_DATA_PATH, Config.DATA_PATH, Config.SAMPLE_DATA_PATH]:
                if os.path.exists(data_path):
                    # Add encoding and error handling parameters
                    # After loading the data, add this validation
                    df = pd.read_csv(data_path, encoding='utf-8-sig', on_bad_lines='skip')
                    logger.info(f"Loaded data from {data_path} with shape {df.shape}")
                    
                    # Fix for BOM character in column name
                    if '\ufeffApp' in df.columns and 'App' not in df.columns:
                        df.rename(columns={'\ufeffApp': 'App'}, inplace=True)
                        logger.info("Renamed '\ufeffApp' column to 'App'")
                    
                    # Validate and log column names
                    logger.info(f"Columns in loaded data: {list(df.columns)}")
                    
                    # Ensure numeric columns are properly converted
                    numeric_columns = ['Reviews', 'Size', 'Installs', 'Price']
                    for col in numeric_columns:
                        if col in df.columns:
                            # Convert to string first to handle any formatting issues
                            df[col] = df[col].astype(str)
                            # Remove any non-numeric characters
                            if col == 'Installs':
                                df[col] = df[col].str.replace('[+,]', '', regex=True)
                            elif col == 'Price':
                                df[col] = df[col].str.replace('$', '', regex=False)
                            # Convert to numeric
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                            # Fill NaN values
                            if col in ['Reviews', 'Price']:
                                df[col].fillna(0, inplace=True)
                            else:
                                df[col].fillna(df[col].median(), inplace=True)
                    
                    return df
            
            logger.error("No data file found")
            return None
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            return None
    
    def _load_model(self, model_path):
        """Load a model from a pickle file with robust error handling."""
        try:
            if not os.path.exists(model_path):
                logger.error(f"Model file not found: {model_path}")
                # Check if there are similar files that might be a match
                dir_path = os.path.dirname(model_path)
                file_name = os.path.basename(model_path)
                similar_files = [f for f in os.listdir(dir_path) if f.endswith('.pkl')]
                if similar_files:
                    logger.warning(f"Found similar model files: {similar_files}")
                return None
                
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            logger.info(f"Successfully loaded model: {os.path.basename(model_path)}")
            return model
        except Exception as e:
            logger.error(f"Error loading model {os.path.basename(model_path)}: {str(e)}")
            return None
    
    def _create_similarity_matrix(self):
        """Create the similarity matrix for recommendations."""
        # Define features first
        numerical_features = ['Reviews', 'Size', 'Installs', 'Price']
        categorical_features = ['Type', 'Content Rating']
        
        # Add this at the beginning of the _create_similarity_matrix method
        try:
            # Validate numerical features before processing
            for col in numerical_features:
                if col in self.data.columns:
                    # Check if column contains non-numeric values
                    if not pd.api.types.is_numeric_dtype(self.data[col]):
                        logger.warning(f"Column {col} is not numeric. Converting to numeric.")
                        self.data[col] = pd.to_numeric(self.data[col], errors='coerce')
                        self.data[col].fillna(self.data[col].median() if not self.data[col].isna().all() else 0, inplace=True)
            
            # Log some stats to help diagnose issues
            logger.info(f"Column {col} - min: {self.data[col].min()}, max: {self.data[col].max()}, mean: {self.data[col].mean()}, null count: {self.data[col].isna().sum()}")
            
            # Check for missing numerical features and create them if needed
            for col in numerical_features:
                if col not in self.data.columns:
                    logger.warning(f"{col} not found in data. Creating with default values.")
                    self.data[col] = 0  # Default value for numerical features
                else:
                    # Handle missing values in existing columns
                    self.data[col] = self.data[col].fillna(self.data[col].median())
            
            # Check for missing categorical features and create them if needed
            for col in categorical_features:
                if col not in self.data.columns:
                    logger.warning(f"{col} not found in data. Creating with default values.")
                    self.data[col] = 'Unknown'  # Default value for categorical features
                else:
                    # Handle missing values in existing columns
                    self.data[col] = self.data[col].fillna('Unknown')
            
            # Create Features column if it doesn't exist
            if 'Features' not in self.data.columns:
                logger.info("Creating 'Features' column from existing data")
                try:
                    # Check if required columns exist
                    required_columns = ['Category', 'App']
                    missing_columns = [col for col in required_columns if col not in self.data.columns]
                    
                    if missing_columns:
                        logger.error(f"Missing required columns: {missing_columns}")
                        # Create missing columns with default values
                        for col in missing_columns:
                            logger.warning(f"Creating missing column '{col}' with default values")
                            self.data[col] = 'Unknown'
                    
                    # Create Features column safely
                    self.data['Features'] = self.data['Category'].fillna('') + ' ' + \
                                    self.data['App'].fillna('')
                    
                    if 'Genres' in self.data.columns:
                        self.data['Features'] += ' ' + self.data['Genres'].fillna('')
                    
                except Exception as e:
                        logger.error(f"Error creating Features column: {str(e)}")
                        # Create a basic Features column as fallback
                        self.data['Features'] = 'default_feature'
                
            # Create feature matrices
            if self.tfidf_vectorizer and 'Features' in self.data.columns:
                text_features = self.tfidf_vectorizer.transform(self.data['Features'])
            else:
                logger.error("TF-IDF vectorizer not loaded or 'Features' column missing")
                return None
                
            # Now we can safely use numerical_features since we've created any missing ones
            if self.scaler:
                numerical_scaled = self.scaler.transform(self.data[numerical_features])
                numerical_scaled_sparse = csr_matrix(numerical_scaled)
            else:
                logger.error("Scaler not loaded")
                return None
                
            # Now we can safely use categorical_features since we've created any missing ones
            if self.encoder:
                categorical_encoded = self.encoder.transform(self.data[categorical_features])
                categorical_encoded_sparse = csr_matrix(categorical_encoded)
            else:
                logger.error("Encoder not loaded")
                return None
            
            # Combine features
            from scipy.sparse import hstack
            combined_features = hstack([
                text_features,
                numerical_scaled_sparse,
                categorical_encoded_sparse
            ])
            
            # Create similarity matrix
            similarity_matrix = cosine_similarity(combined_features)
            logger.info(f"Created similarity matrix with shape {similarity_matrix.shape}")
            return similarity_matrix
                
        except Exception as e:
            logger.error(f"Error creating similarity matrix: {str(e)}")
            return None
    
    def get_recommendations(self, app_name, num_recommendations=5):
        """Get recommendations for an app based on similarity."""
        # Inside get_recommendations method
        try:
            if self.data is None or self.similarity_matrix is None:
                return {
                    'status': 'error',
                    'message': 'Recommender not properly initialized',
                    'recommendations': []
                }
            
            # Find the app in the dataset - try exact match first
            app_indices = self.data.index[self.data['App'] == app_name].tolist()
            
            # If exact match fails, try case-insensitive match
            if not app_indices and 'App' in self.data.columns:
                app_indices = self.data.index[self.data['App'].str.lower() == app_name.lower()].tolist()
            
            # If still no match, try partial match
            if not app_indices and 'App' in self.data.columns:
                # Look for apps that contain the search term
                partial_matches = self.data.index[self.data['App'].str.lower().str.contains(app_name.lower(), na=False)].tolist()
                if partial_matches:
                    # Use the first partial match if available
                    app_indices = [partial_matches[0]]
                    logger.info(f"Using partial match: {self.data.loc[partial_matches[0], 'App']} for query '{app_name}'")
            
            if not app_indices:
                # App not found, return similar app names as suggestions
                if 'App' in self.data.columns:
                    app_name_lower = app_name.lower()
                    
                    # Get suggestions based on partial matches
                    suggestions = [
                        app for app in self.data['App'].tolist()
                        if app_name_lower in app.lower() or any(
                            word in app.lower() for word in app_name_lower.split()
                        )
                    ][:5]
                    
                    # If no suggestions found, try finding apps in the same category
                    if not suggestions and 'Category' in self.data.columns:
                        # Try to guess the category from the app name
                        possible_categories = self.data['Category'].unique()
                        for category in possible_categories:
                            if category.lower() in app_name_lower:
                                category_apps = self.data[self.data['Category'] == category]['App'].tolist()[:5]
                                if category_apps:
                                    suggestions = category_apps
                                    break
                    
                    return {
                        'status': 'error',
                        'message': f"App '{app_name}' not found in the dataset",
                        'suggestions': suggestions
                    }
                else:
                    return {
                        'status': 'error',
                        'message': f"App '{app_name}' not found in the dataset",
                        'suggestions': []
                    }
            
            # Get the app index
            app_idx = app_indices[0]
            
            # Get similarity scores
            similarity_scores = self.similarity_matrix[app_idx]
            
            # Get indices of most similar apps (excluding the app itself)
            similar_indices = similarity_scores.argsort()[::-1][1:]
            
            # Filter out duplicate app names
            unique_app_recommendations = []
            seen_apps = set()
            
            # Add the input app to seen_apps to avoid recommending the same app
            input_app_name = self.data.iloc[app_idx]['App']
            seen_apps.add(input_app_name.lower())
            
            # Get unique recommendations
            for idx in similar_indices:
                app_name = self.data.iloc[idx]['App']
                if app_name.lower() not in seen_apps:
                    seen_apps.add(app_name.lower())
                    unique_app_recommendations.append(idx)
                    if len(unique_app_recommendations) >= num_recommendations:
                        break
            
            # Get the recommended apps
            recommended_apps = self.data.iloc[unique_app_recommendations][['App', 'Category', 'Rating']].to_dict('records')
            
            logger.info(f"Successfully found {len(recommended_apps)} recommendations for {app_name}")
            
            return {
                'status': 'success',
                'recommendations': recommended_apps
            }
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            logger.error(f"Error details: {traceback.format_exc()}")
            return {
                'status': 'error',
                'message': str(e),
                'recommendations': []
            }