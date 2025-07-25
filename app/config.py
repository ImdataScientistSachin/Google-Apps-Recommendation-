import os

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-for-app-recommender'
    DEBUG = os.environ.get('FLASK_DEBUG') or True
    TESTING = False
    
    # File paths - always use absolute paths based on the current location
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    MODELS_DIR = os.path.join(BASE_DIR, 'models')
    
    # Ensure directories exist
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    # Data paths
    DATA_PATH = os.path.join(DATA_DIR, 'googleplaystore.csv')
    FIXED_DATA_PATH = os.path.join(DATA_DIR, 'googleplaystore_fixed.csv')
    SAMPLE_DATA_PATH = os.path.join(DATA_DIR, 'apps_data.csv')
    
        # Model paths
    # Model paths
    TFIDF_PATH = os.path.join(MODELS_DIR, 'tfidf_vectorizer.pkl')
    ENCODER_PATH = os.path.join(MODELS_DIR, 'onehot_encoder.pkl')
    SCALER_PATH = os.path.join(MODELS_DIR, 'minmax_scaler.pkl')
    MODEL_PATH = os.path.join(MODELS_DIR, 'random_forest_model.pkl')
    
    # API configuration
    MAX_RECOMMENDATIONS = 20
    
    @classmethod
    def verify_paths(cls):
        """Verify that all required paths exist and are accessible."""
        missing_files = []
        
        # Check model files
        model_files = [cls.TFIDF_PATH, cls.ENCODER_PATH, cls.SCALER_PATH, cls.MODEL_PATH]
        for file_path in model_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        # Check at least one data file exists
        data_files = [cls.DATA_PATH, cls.FIXED_DATA_PATH, cls.SAMPLE_DATA_PATH]
        if not any(os.path.exists(path) for path in data_files):
            missing_files.extend(data_files)
        
        return missing_files