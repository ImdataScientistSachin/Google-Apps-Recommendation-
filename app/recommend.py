from flask import Blueprint, request, jsonify
import pandas as pd
import pickle
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from app.config import Config  # Add this import

recommend_bp = Blueprint('recommend', __name__)

# Load the trained model and components
try:
    with open(Config.MODEL_PATH, 'rb') as file:  # Use Config.MODEL_PATH instead of hardcoded path
        model_data = pickle.load(file)
        
    # Extract components from model_data
    model = model_data['model']
    scaler = model_data['scaler']
    encoder = model_data['encoder']
    tfidf_vectorizer = model_data['tfidf_vectorizer']
    numerical_features = model_data['numerical_features']
    categorical_features = model_data['categorical_features']
    apps_list = model_data['apps_list']
except Exception as e:
    print(f"Error loading model: {str(e)}")

@recommend_bp.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        app_features = data.get('features')
        
        if not app_features:
            return jsonify({"error": "No features provided"}), 400
        
        # Ensure all required features are present
        required_features = numerical_features + categorical_features + ['description']
        missing_features = [feat for feat in required_features if feat not in app_features]
        
        if missing_features:
            return jsonify({"error": f"Missing features: {', '.join(missing_features)}"}), 400
            
        try:
            numerical_data = [[app_features[feat] for feat in numerical_features]]
            categorical_data = [[app_features[feat] for feat in categorical_features]]
            
            numerical_features_scaled = scaler.transform(numerical_data)
            categorical_features_encoded = encoder.transform(categorical_data)
            text_features = tfidf_vectorizer.transform([app_features['description']])
            
            # Combine features
            features = np.hstack([
                numerical_features_scaled,
                categorical_features_encoded.toarray(),
                text_features.toarray()
            ])
            
            # Get prediction
            predicted_rating = model.predict(features)[0]
            
            return jsonify({
                "predicted_rating": float(predicted_rating),
                "recommended_apps": apps_list[:5]
            })
            
        except Exception as e:
            return jsonify({"error": f"Error processing features: {str(e)}"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

