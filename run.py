import logging
import os

if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # Ensure necessary directories exist
    os.makedirs('data', exist_ok=True)
    os.makedirs('models', exist_ok=True)

    # Dynamically import create_app after setting up the environment
    from app import create_app

    # Create and run the Flask app
    app = create_app()
    app.run(debug=True)