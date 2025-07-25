from flask import Blueprint, jsonify, request, current_app, render_template
from werkzeug.exceptions import HTTPException, BadRequest
import logging
import traceback
from datetime import datetime
import os
from app.models import App, Review, db

bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

@bp.route('/api/recommend', methods=['GET', 'POST'])
def recommend():
    try:
        # Get the recommender from the app
        recommender = current_app.recommender
        
        if recommender is None or not hasattr(recommender, 'data') or not hasattr(recommender, 'similarity_matrix'):
            logger.error("Recommender not properly initialized")
            return jsonify({
                'status': 'error',
                'message': 'Recommender service is currently unavailable',
                'code': 'RECOMMENDER_UNAVAILABLE'
            }), 503
            
        # Handle both GET and POST requests
        if request.method == 'POST':
            # For POST requests, get data from JSON body
            data = request.get_json()
            app_name = data.get('app_name', '').strip() if data else ''
        else:
            # For GET requests, get data from query parameters
            app_name = request.args.get('app_name', '').strip()
            
        if not app_name:
            raise BadRequest('Please provide a valid app name')

        recommendations = recommender.get_recommendations(app_name)
        
        if recommendations.get('status') == 'error':
            logger.warning(f"Recommendation error for {app_name}: {recommendations['message']}")
            return jsonify({
                'status': 'error',
                'message': recommendations['message'],
                'suggestions': recommendations.get('suggestions', []),
                'popular': recommendations.get('popular', [])
            }), 404

        return jsonify({
            'status': 'success',
            'app_name': app_name,
            'recommendations': recommendations.get('recommendations', [])
        })
    except BadRequest as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        error_details = {
            'error_type': type(e).__name__,
            'error_message': str(e),
            'traceback': traceback.format_exc()
        }
        logger.error(f"Detailed error in recommend endpoint: {error_details}")
        return jsonify({
            'status': 'error',
            'message': f'An unexpected error occurred: {type(e).__name__}',
            'details': str(e) if current_app.debug else None
        }), 500

@bp.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@bp.route('/api/health', methods=['GET'])
def health_check():
    """Check the health of the application and its components."""
    from app.config import Config
    
    # Check if recommender is initialized
    recommender_status = {
        'initialized': current_app.recommender is not None,
        'has_data': False,
        'has_similarity_matrix': False,
        'has_models': False
    }
    
    if current_app.recommender is not None:
        recommender_status['has_data'] = hasattr(current_app.recommender, 'data') and current_app.recommender.data is not None
        recommender_status['has_similarity_matrix'] = hasattr(current_app.recommender, 'similarity_matrix') and current_app.recommender.similarity_matrix is not None
        recommender_status['has_models'] = all([
            hasattr(current_app.recommender, 'tfidf_vectorizer') and current_app.recommender.tfidf_vectorizer is not None,
            hasattr(current_app.recommender, 'encoder') and current_app.recommender.encoder is not None,
            hasattr(current_app.recommender, 'scaler') and current_app.recommender.scaler is not None,
            hasattr(current_app.recommender, 'model') and current_app.recommender.model is not None
        ])
    
    # Check model files
    model_files = {
        'tfidf': os.path.exists(Config.TFIDF_PATH),
        'encoder': os.path.exists(Config.ENCODER_PATH),
        'scaler': os.path.exists(Config.SCALER_PATH),
        'model': os.path.exists(Config.MODEL_PATH)
    }
    
    # Check data files
    data_files = {
        'original': os.path.exists(Config.DATA_PATH),
        'fixed': os.path.exists(Config.FIXED_DATA_PATH),
        'sample': os.path.exists(Config.SAMPLE_DATA_PATH)
    }
    
    return jsonify({
        'status': 'healthy' if all(recommender_status.values()) else 'unhealthy',
        'recommender': recommender_status,
        'model_files': model_files,
        'data_files': data_files,
        'config': {
            'tfidf_path': Config.TFIDF_PATH,
            'encoder_path': Config.ENCODER_PATH,
            'scaler_path': Config.SCALER_PATH,
            'model_path': Config.MODEL_PATH
        }
    })

@bp.route('/api/popular', methods=['GET'])
def popular_apps():
    try:
        # Get the recommender from the app
        recommender = current_app.recommender
        
        if recommender is None or not hasattr(recommender, 'data'):
            logger.error("Recommender not properly initialized")
            return jsonify({
                'status': 'error',
                'message': 'Recommender service is currently unavailable',
                'code': 'RECOMMENDER_UNAVAILABLE',
                'popular_apps': []
            }), 503
        
        # Get count parameter, default to 10
        count = request.args.get('count', 10, type=int)
        
        # Get popular apps based on review count
        if recommender.data is not None and len(recommender.data) > 0:
            popular_apps = recommender.data.sort_values('Reviews', ascending=False).head(count)
            return jsonify({
                'success': True,
                'popular_apps': popular_apps[['App', 'Category', 'Rating', 'Reviews']].to_dict('records')
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'No app data available',
                'popular_apps': []
            }), 404
            
    except Exception as e:
        logger.error(f"Popular apps request failed: {str(e)}", extra={
            'traceback': traceback.format_exc()
        })
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'popular_apps': []
        }), 500

@bp.errorhandler(HTTPException)
def handle_http_error(e):
    return jsonify({
        'status': 'error',
        'message': e.description,
        'code': e.code
    }), e.code

@bp.errorhandler(Exception)
def handle_unexpected_error(e):
    logger.critical(f"Unexpected error: {str(e)}", extra={
        'traceback': traceback.format_exc()
    })
    return jsonify({
        'status': 'error',
        'message': 'An unexpected error occurred',
        'code': 500
    }), 500

@bp.route('/api/recommender-status', methods=['GET'])
def recommender_status():
    """Check if the recommender is initialized and working properly."""
    from app.config import Config
    
    recommender = current_app.recommender
    missing_files = Config.verify_paths()
    
    if recommender is None or not hasattr(recommender, 'data') or not hasattr(recommender, 'similarity_matrix'):
        return jsonify({
            'status': 'error',
            'initialized': False,
            'message': 'Recommender not properly initialized',
            'code': 'RECOMMENDER_UNAVAILABLE',
            'missing_files': missing_files
        })
    
    # Check if the recommender has data
    has_data = recommender.data is not None and len(recommender.data) > 0
    
    # Check if the similarity matrix is created
    has_similarity_matrix = recommender.similarity_matrix is not None
    
    return jsonify({
        'status': 'success',
        'initialized': True,
        'has_data': has_data,
        'has_similarity_matrix': has_similarity_matrix,
        'data_shape': recommender.data.shape if has_data else None,
        'similarity_matrix_shape': recommender.similarity_matrix.shape if has_similarity_matrix else None,
        'current_directory': os.getcwd(),
        'base_directory': Config.BASE_DIR
    })

@bp.route('/api/reviews/<app_name>', methods=['GET'])
def get_app_reviews(app_name):
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Find the app
        app = App.query.filter_by(name=app_name).first()
        if not app:
            return jsonify({
                'status': 'error',
                'message': f'App {app_name} not found'
            }), 404
        
        # Get reviews with pagination
        reviews_query = Review.query.filter_by(app_id=app.id)
        total_reviews_count = reviews_query.count()  # Get total review count
        reviews_paginated = reviews_query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Format reviews
        reviews = [{
            'id': review.id,
            'rating': review.rating,
            'content': review.content,
            'author': review.author,
            'created_at': review.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for review in reviews_paginated.items]
        
        return jsonify({
            'status': 'success',
            'app_name': app_name,
            'app_info': {
                'name': app.name,
                'category': app.category,
                'rating': app.rating,
                'reviews': app.reviews,  # This is the Google Play Store review count
                'size': app.size,
                'installs': app.installs,
                'content_rating': app.content_rating,
                'genres': app.genres
            },
            'reviews': reviews,
            'total': reviews_paginated.total,
            'pages': reviews_paginated.pages,
            'current_page': page,
            'review_count': total_reviews_count  # This is the count of reviews in our database
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500