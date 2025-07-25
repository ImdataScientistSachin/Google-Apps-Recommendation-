# Google Play App Recommender

A Flask web application that recommends similar Google Play Store apps based on machine learning. The application uses the Google Play Store dataset (valid until 2018) to provide recommendations for similar apps based on app features, category, ratings, and more.

## Features

- Find similar apps based on app features using machine learning
- View popular apps from the Google Play Store
- Get recommendations based on app characteristics
- View dataset statistics and information
- Responsive web interface
- RESTful API for integration with other applications

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/ImdataScientistSachin/Google-Apps-Recommendation-.git
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows:
     ```
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Place the `googleplaystore.csv` file in the `data` directory:
   ```
   mkdir -p data
   cp path/to/googleplaystore.csv data/
   ```

## Usage

### Running the Application

1. Start the Flask app:
   ```
   python run.py
   ```

2. Open a web browser and navigate to:
   ```
   http://localhost:5000
   ```

3. Enter an app name to get recommendations for similar apps.

### API Endpoints

- `GET /api/info`: Get information about the API
- `POST /api/recommend`: Get app recommendations
  ```json
  {
    "app_name": "Facebook",
    "num_recommendations": 5
  }
  ```
- `GET /api/popular?count=10`: Get popular apps

## Model Details

The recommendation system uses:
- TF-IDF vectorization for text features
- One-hot encoding for categorical features
- MinMax scaling for numerical features
- Cosine similarity to find similar apps

## Dataset

The application uses the Google Play Store Apps dataset from Kaggle, which includes:
- App name, category, and genre
- Rating, reviews, and installs
- Size, type, price, and content rating

**Note:** The dataset contains information valid until 2018. Newer apps or updates after this period are not included in the recommendations.

## Project Structure

```
GoogleAppsRecom/
├── app/                      # Flask application
│   ├── __init__.py           # App initialization
│   ├── config.py             # Configuration
│   ├── models.py             # Data models
│   ├── recommender.py        # Recommendation logic
│   ├── routes.py             # API routes
│   ├── utils.py              # Utility functions
│   ├── static/               # Static files (CSS, JS)
│   └── templates/            # HTML templates
├── data/                     # Data files
├── models/                   # Saved ML models
├── notebooks/                # Jupyter notebooks
├── run.py                    # App entry point
├── requirements.txt          # Dependencies
└── README.md                 # This file
```

## License

MIT

## Acknowledgments

- The dataset is from Kaggle: [Google Play Store Apps](https://www.kaggle.com/lava18/google-play-store-apps)
