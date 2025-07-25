// Utility functions
function showLoading() {
    document.querySelector('.loading').style.display = 'flex';
    document.querySelector('.error').style.display = 'none';
}

function hideLoading() {
    document.querySelector('.loading').style.display = 'none';
}

function showError(message) {
    const errorElement = document.querySelector('.error');
    errorElement.innerHTML = `
        <div class="alert alert-danger">
            ${message}<br>
            <small>Please try again or contact support</small>
        </div>
    `;
    errorElement.style.display = 'block';
}

// Search functionality
async function searchApp() {
    const searchInput = document.querySelector('.search-box input');
    const appName = searchInput.value.trim();
    
    if (!appName) {
        showError('Please enter an app name');
        return;
    }
    
    showLoading();
    try {
        // Use the correct API endpoint with consistent approach
        const response = await fetch('/api/recommend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ app_name: appName })
        });
        
        // Add detailed error logging
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('API Response:', data);
        
        if (data.error || data.status === 'error') {
            showError(data.error || data.message || 'An error occurred');
            return;
        }
        
        displayRecommendations(data);
    } catch (error) {
        showError('An error occurred while fetching recommendations');
        console.error('Error:', error);
    } finally {
        hideLoading();
    }
}

// Display recommendations
function displayRecommendations(data) {
    const resultsSection = document.querySelector('.results-section');
    resultsSection.innerHTML = '';
    
    // Adapt to the actual response structure
    // Create a standardized app object from the API response
    const standardizeApp = (app) => {
        return {
            name: app.App || app.name || 'Unknown',
            category: app.Category || app.category || 'Unknown',
            rating: app.Rating || app.rating || 0,
            reviews: app.Reviews || app.reviews || 0,
            size: app.Size || app.size || 'Unknown',
            installs: app.Installs || app.installs || 'Unknown',
            price: app.Price || app.price || 0,
            content_rating: app['Content Rating'] || app.content_rating || 'Unknown',
            genres: app.Genres || app.genres || 'Unknown',
            similarity: app.similarity || 1.0
        };
    };
    
    // Display the input app if we have app_name
    if (data.app_name) {
        // Create a basic input app object
        const inputAppData = {
            App: data.app_name,
            Category: 'Unknown',
            Rating: 0
        };
        
        // Try to find more details in recommendations if available
        if (data.recommendations && data.recommendations.length > 0) {
            const matchingApp = data.recommendations.find(app => 
                app.App === data.app_name || app.name === data.app_name
            );
            
            if (matchingApp) {
                Object.assign(inputAppData, matchingApp);
            }
        }
        
        const inputApp = standardizeApp(inputAppData);
        const inputAppSection = document.createElement('div');
        inputAppSection.className = 'input-app-section';
        inputAppSection.innerHTML = `
            <h3>Selected App</h3>
            <div class="app-grid">
                ${createAppCard(inputApp, true)}
            </div>
        `;
        resultsSection.appendChild(inputAppSection);
    }
    
    // Display recommendations
    if (data.recommendations && data.recommendations.length > 0) {
        const recommendationsSection = document.createElement('div');
        recommendationsSection.className = 'recommendations-section';
        recommendationsSection.innerHTML = `
            <h3>Similar Apps</h3>
            <div class="app-grid">
                ${data.recommendations.map(app => createAppCard(standardizeApp(app))).join('')}
            </div>
        `;
        resultsSection.appendChild(recommendationsSection);
    } else {
        // Show a message when no recommendations are found
        const noRecommendationsSection = document.createElement('div');
        noRecommendationsSection.className = 'no-recommendations';
        noRecommendationsSection.innerHTML = `
            <div class="alert alert-info">
                No similar apps found for "${data.app_name}". Try another app name.
            </div>
        `;
        resultsSection.appendChild(noRecommendationsSection);
    }
}

// Create app card HTML
function createAppCard(app, isInputApp = false) {
    return `
        <div class="app-card ${isInputApp ? 'input-app' : ''}">
            <h3>${app.name}</h3>
            <div class="category">${app.category}</div>
            <div class="rating">
                <span class="stars">${'★'.repeat(Math.floor(app.rating))}${app.rating % 1 !== 0 ? '½' : ''}</span>
                <span class="reviews">(${app.reviews.toLocaleString()} reviews)</span>
            </div>
            <p>Size: ${app.size}</p>
            <p>Installs: ${app.installs}</p>
            <p class="price">${app.price === 0 ? 'Free' : `$${app.price.toFixed(2)}`}</p>
            <p class="content-rating">Content Rating: ${app.content_rating}</p>
            <p class="genres">${app.genres}</p>
            ${!isInputApp ? `
                <div class="similarity">Similarity: ${(app.similarity * 100).toFixed(1)}%</div>
                <button class="find-similar" onclick="searchAppByName('${app.name}')">Find Similar</button>
            ` : ''}
        </div>
    `;
}

// Search by app name
function searchAppByName(appName) {
    const searchInput = document.querySelector('.search-box input');
    searchInput.value = appName;
    searchApp();
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Add event listener for search button
    const searchButton = document.querySelector('.search-box button');
    searchButton.addEventListener('click', searchApp);
    
    // Add event listener for Enter key in search input
    const searchInput = document.querySelector('.search-box input');
    searchInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            searchApp();
        }
    });
});

function loadPopularApps() {
    fetch('/api/popular')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                showError(data.error);
                return;
            }
            // Render logic for popular apps would go here
            console.log('Popular apps loaded:', data);
        })
        .catch(error => {
            console.error('Error loading popular apps:', error);
        });
}