// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const appNameInput = document.getElementById('appNameInput');
    const searchButton = document.getElementById('searchButton');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const recommendationsContainer = document.getElementById('recommendationsContainer');
    const inputAppName = document.getElementById('inputAppName');
    const recommendationsList = document.getElementById('recommendationsList');
    const errorContainer = document.getElementById('errorContainer');
    const popularAppsList = document.getElementById('popularAppsList');
    
    // Debounce function to limit how often a function can fire
    function debounce(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }
    
    // Cache for previously fetched recommendations
    const recommendationCache = {};
    
    // Cache for popular apps
    let popularAppsCache = null;
    
    // Throttle search requests
    let lastSearchTime = 0;
    const SEARCH_THROTTLE_MS = 300;
    
    // Function to check recommender status
    function checkRecommenderStatus() {
        fetch('/api/recommender-status')
            .then(response => response.json())
            .then(data => {
                if (!data.initialized) {
                    // Show a warning if the recommender is not initialized
                    const warningHtml = `
                        <div class="alert alert-warning">
                            <strong>Note:</strong> The recommendation system is currently initializing. 
                            Some features may be limited.
                        </div>
                    `;
                    document.querySelector('.container').insertAdjacentHTML("afterbegin", warningHtml);
                }
            })
            .catch(error => {
                console.error('Error checking recommender status:', error);
            });
    }
    
    // Call this function on page load
    document.addEventListener('DOMContentLoaded', function() {
        // Existing code...
        
        // Check recommender status
        checkRecommenderStatus();
        
        // Load popular apps and dataset info
        setTimeout(() => {
            loadPopularApps();
            loadDatasetInfo();
        }, 100);
        
        // Rest of the existing code...
    });
    
    // Event listener for the search button
    searchButton.addEventListener('click', getRecommendations);
    
    // Event listener for the enter key in the input field
    appNameInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            getRecommendations();
        }
    });
    
    // Add auto-suggestion behavior with debounce
    appNameInput.addEventListener('input', debounce(function() {
        const query = appNameInput.value.trim();
        if (query.length >= 3) {
            // Here we would normally call an API endpoint for suggestions
            // This is a placeholder for a future implementation
            console.log(`Could search for suggestions: ${query}`);
        }
    }, 300));
    
    // Function to get recommendations from the API
    // Function to get recommendations from the API
    function getRecommendations() {
        const appName = appNameInput.value.trim();
        
        // Validate input
        if (!appName) {
            showError('Please enter an app name');
            return;
        }
        
        // Throttle searches to prevent rapid clicking
        const now = Date.now();
        if (now - lastSearchTime < SEARCH_THROTTLE_MS) {
            console.log('Search throttled');
            return;
        }
        lastSearchTime = now;
        
        // Reset UI
        resetUI();
        
        // Check cache first
        const cacheKey = `${appName}:10`; // 10 is the default num_recommendations
        if (recommendationCache[cacheKey]) {
            console.log('Using cached recommendations');
            handleRecommendationResponse({
                status: 200,
                data: recommendationCache[cacheKey]
            });
            return;
        }
        
        // Show loading indicator
        loadingIndicator.classList.remove('d-none');
        
        // Use fetchWithRetry instead of fetch
        fetchWithRetry('/api/recommend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                app_name: appName,
                num_recommendations: 10
            }),
        }, 3)  // 3 retries
        .then(response => {
            // Cache successful responses
            if (response.data.success) {
                recommendationCache[cacheKey] = response.data;
            }
            
            handleRecommendationResponse(response);
        })
        .catch(error => {
            loadingIndicator.classList.add('d-none');
            let errorMessage = 'Network or server error. Please try again later.';
            
            // Add more specific error messages
            if (error.name === 'TypeError') {
                console.error('Type Error:', error.message);
                errorMessage = 'There was a problem processing the data. Please try again.';
            } else if (error.name === 'SyntaxError') {
                console.error('Syntax Error:', error.message);
                errorMessage = 'The server response was invalid. Please try again later.';
            } else {
                console.error('Error:', error.message, error);
                errorMessage = `An error occurred while fetching recommendations. Please try again. Error: ${error.message} (${error.name})`;
            }
            
            showError(errorMessage);
            console.error('Error details:', error);
            logError('recommendation_fetch', error);  // Add error logging
            
            // Always try to load popular apps as fallback
            loadPopularApps();
        });
    }
    
    // Function to handle API response - separated for reuse with cache
    // Function to handle API response - separated for reuse with cache
    function handleRecommendationResponse(response) {
        // Hide loading indicator
        loadingIndicator.classList.add('d-none');
        
        // Validate response structure
        if (!response || typeof response !== 'object') {
            showError('Invalid response received');
            loadPopularApps();
            return;
        }
        
        const { status, data } = response;
        
        // Validate data structure
        if (!data || typeof data !== 'object') {
            showError('Invalid data format received');
            loadPopularApps();
            return;
        }
        
        console.log('API response data:', data);  // Debug log
        
        // Show request time if available
        if (data.request_time_seconds) {
            console.log(`Request time: ${data.request_time_seconds.toFixed(4)}s`);
        }

        if (data.status === "success") {
            // Show recommendations
            displayRecommendations(data);
        } else {
            // Show error message with more context
            let errorMessage = data.message || data.error || 'An unknown error occurred';
            
            // Add more specific error messages based on error code
            if (data.code === 'RECOMMENDER_UNAVAILABLE') {
                errorMessage = 'The recommendation system is currently initializing. Please try again in a few moments.';
            } else if (status === 500) {
                errorMessage += '. The server encountered an issue processing your request.';
            }
            
            showError(errorMessage);
            
            // Display popular recommendations if available as fallback
            if (data.popular && data.popular.length > 0) {
                console.log('Showing fallback popular recommendations');
                displayPopularRecommendations(data.popular);
            } else if (data.popular_apps && data.popular_apps.length > 0) {
                // Handle popular_apps property as an alternative
                console.log('Showing fallback popular_apps recommendations');
                displayPopularRecommendations(data.popular_apps);
            } else {
                // If no recommendations provided, load popular apps
                console.log('No fallback recommendations, loading popular apps');
                loadPopularApps();
            }
        }
    }
    
    // Load popular apps with a smaller cached version
    function loadPopularApps() {
        console.log('Loading popular apps...');
        
        // Use cache if available
        if (popularAppsCache) {
            console.log('Using cached popular apps');
            displayPopularApps(popularAppsCache);
            return;
        }
        
        // Use fetchWithRetry instead of fetch
        fetchWithRetry('/api/popular?count=10', {}, 3)  // 3 retries
        .then(({ status, data }) => {
            console.log('Popular apps response:', data);  // Debug logging
            
            // Handle 500 status specifically
            if (status === 500) {
                console.warn('Server error when loading popular apps');
                popularAppsList.innerHTML = `<div class="alert alert-warning">
                    <strong>Note:</strong> Using sample popular apps while the recommendation system is being initialized.
                </div>`;
                
                // If the server returns popular_apps even with an error, use them
                if (data.popular_apps && data.popular_apps.length > 0) {
                    popularAppsCache = data.popular_apps;
                    displayPopularApps(data.popular_apps);
                    return;
                }
                
                // Otherwise, create some sample apps 
                const sampleApps = [
                    { App: "Facebook", Category: "Social", Rating: 4.5, Reviews: 1000000, Installs: 1000000000 },
                    { App: "Instagram", Category: "Social", Rating: 4.3, Reviews: 900000, Installs: 500000000 },
                    { App: "WhatsApp", Category: "Communication", Rating: 4.6, Reviews: 950000, Installs: 1000000000 }
                ];
                popularAppsCache = sampleApps;
                displayPopularApps(sampleApps);
                return;
            }
            
            // Normal success case
            if (data.success && data.popular_apps && data.popular_apps.length > 0) {
                popularAppsCache = data.popular_apps;
                displayPopularApps(data.popular_apps);
            } else {
                const errorMessage = data.error || data.message || 'No popular apps available at the moment.';
                popularAppsList.innerHTML = `<div class="alert alert-info">${errorMessage}</div>`;
                console.warn('No popular apps returned:', data);
            }
        })
        .catch(error => {
            console.error('Error loading popular apps:', error);
            logError('popular_apps_fetch', error);  // Add error logging
            popularAppsList.innerHTML = `<div class="alert alert-danger">Failed to load popular apps: ${error.message}</div>`;
            
            // Display some sample apps as fallback
            const sampleApps = [
                { App: "Facebook", Category: "Social", Rating: 4.5, Reviews: 1000000, Installs: 1000000000 },
                { App: "Instagram", Category: "Social", Rating: 4.3, Reviews: 900000, Installs: 500000000 },
                { App: "WhatsApp", Category: "Communication", Rating: 4.6, Reviews: 950000, Installs: 1000000000 }
            ];
            
            popularAppsCache = sampleApps;
            setTimeout(() => {
                popularAppsList.innerHTML += '<div class="mt-3"><h4>Sample Popular Apps</h4></div>';
                displayPopularApps(sampleApps);
            }, 100);  // Short delay for better UI experience
        });
    }
    
    // Function to display recommendations
    function displayRecommendations(data) {
        try {
            recommendationsContainer.classList.remove('d-none');
            inputAppName.textContent = data.input_app;
            
            // Store source app info for similarity reasons
            const sourceApp = data.input_app || '';
            let sourceCategory = data.input_category || '';
            const sourceGenres = data.input_genre || '';
            
            recommendationsList.innerHTML = '';
            
            // Add category and genre info if available
            if (data.input_category || data.input_genre) {
                const categoryInfo = document.createElement('p');
                categoryInfo.classList.add('text-muted', 'mb-3');
                
                let infoText = '';
                if (data.input_category) {
                    infoText += `Category: ${data.input_category}`;
                }
                if (data.input_genre) {
                    infoText += infoText ? ` | Genre: ${data.input_genre}` : `Genre: ${data.input_genre}`;
                }
                
                categoryInfo.textContent = infoText;
                recommendationsContainer.insertBefore(categoryInfo, recommendationsList);
            }
            
            // Sort recommendations by match score first
            const sortedRecommendations = [...data.recommendations].sort((a, b) => {
                return (b.MatchScore || 0) - (a.MatchScore || 0);
            });
            
            // Track apps we've already added to prevent duplicates
            const addedApps = new Set();
            
            // Group recommendations by category to improve clarity
            const recommendationsByCategory = {};
            
            // First, group by category and filter out duplicates
            sortedRecommendations.forEach(app => {
                // Skip if we've already added this app
                if (addedApps.has(app.App)) {
                    return;
                }
                
                // Add to our tracking set
                addedApps.add(app.App);
                
                const category = app.Category || 'Uncategorized';
                if (!recommendationsByCategory[category]) {
                    recommendationsByCategory[category] = [];
                }
                recommendationsByCategory[category].push(app);
            });
            
            // Display recommendations, showing same category first
            const categories = Object.keys(recommendationsByCategory);
            
            // Sort categories to show source category first, then others
            categories.sort((a, b) => {
                if (a === sourceCategory) return -1;
                if (b === sourceCategory) return 1;
                return 0;
            });
            
            // Create category sections
            categories.forEach(category => {
                const apps = recommendationsByCategory[category];
                
                // Add category header if there's more than one category
                if (categories.length > 1) {
                    const categoryHeader = document.createElement('div');
                    categoryHeader.classList.add('category-header', 'my-2');
                    categoryHeader.innerHTML = `<strong>${category}</strong>`;
                    
                    // Highlight if it matches the source category
                    if (category === sourceCategory) {
                        categoryHeader.classList.add('same-category');
                        categoryHeader.innerHTML += ' <span class="badge bg-primary">Same Category</span>';
                    }
                    
                    recommendationsList.appendChild(categoryHeader);
                }
                
                // Add apps in this category
                apps.forEach(app => {
                    const item = createAppListItem(app, true, sourceApp, sourceCategory, sourceGenres);
                    recommendationsList.appendChild(item);
                });
            });
            
            // If no recommendations were found, show a message
            if (sortedRecommendations.length === 0) {
                const noResults = document.createElement('div');
                noResults.classList.add('alert', 'alert-info');
                noResults.textContent = 'No recommended apps found.';
                recommendationsList.appendChild(noResults);
            }
        } catch (error) {
            console.error('Error displaying recommendations:', error);
            showError('Error displaying recommendations. Please try again.');
            // Show popular apps as fallback
            loadPopularApps();
        }
    }
    
    // Function to display popular recommendations (fallback)
    function displayPopularRecommendations(popularApps) {
        if (popularApps && popularApps.length > 0) {
            const fallbackDiv = document.createElement('div');
            fallbackDiv.classList.add('mt-4');
            fallbackDiv.innerHTML = `
                <h4>You might be interested in these popular apps:</h4>
                <div class="list-group" id="fallbackRecommendations"></div>
            `;
            
            recommendationsContainer.parentNode.insertBefore(fallbackDiv, recommendationsContainer.nextSibling);
            
            const fallbackList = document.getElementById('fallbackRecommendations');
            
            popularApps.forEach(app => {
                const item = createAppListItem(app);
                fallbackList.appendChild(item);
            });
        }
    }
    
    // Function to display recommendations
    function displayRecommendations(data) {
        try {
            recommendationsContainer.classList.remove('d-none');
            inputAppName.textContent = data.input_app;
            
            // Store source app info for similarity reasons
            const sourceApp = data.input_app || '';
            let sourceCategory = data.input_category || '';
            const sourceGenres = data.input_genre || '';
            
            recommendationsList.innerHTML = '';
            
            // Add category and genre info if available
            if (data.input_category || data.input_genre) {
                const categoryInfo = document.createElement('p');
                categoryInfo.classList.add('text-muted', 'mb-3');
                
                let infoText = '';
                if (data.input_category) {
                    infoText += `Category: ${data.input_category}`;
                }
                if (data.input_genre) {
                    infoText += infoText ? ` | Genre: ${data.input_genre}` : `Genre: ${data.input_genre}`;
                }
                
                categoryInfo.textContent = infoText;
                recommendationsContainer.insertBefore(categoryInfo, recommendationsList);
            }
            
            // Sort recommendations by match score first
            const sortedRecommendations = [...data.recommendations].sort((a, b) => {
                return (b.MatchScore || 0) - (a.MatchScore || 0);
            });
            
            // Track apps we've already added to prevent duplicates
            const addedApps = new Set();
            
            // Group recommendations by category to improve clarity
            const recommendationsByCategory = {};
            
            // First, group by category and filter out duplicates
            sortedRecommendations.forEach(app => {
                // Skip if we've already added this app
                if (addedApps.has(app.App)) {
                    return;
                }
                
                // Add to our tracking set
                addedApps.add(app.App);
                
                const category = app.Category || 'Uncategorized';
                if (!recommendationsByCategory[category]) {
                    recommendationsByCategory[category] = [];
                }
                recommendationsByCategory[category].push(app);
            });
            
            // Display recommendations, showing same category first
            const categories = Object.keys(recommendationsByCategory);
            
            // Sort categories to show source category first, then others
            categories.sort((a, b) => {
                if (a === sourceCategory) return -1;
                if (b === sourceCategory) return 1;
                return 0;
            });
            
            // Create category sections
            categories.forEach(category => {
                const apps = recommendationsByCategory[category];
                
                // Add category header if there's more than one category
                if (categories.length > 1) {
                    const categoryHeader = document.createElement('div');
                    categoryHeader.classList.add('category-header', 'my-2');
                    categoryHeader.innerHTML = `<strong>${category}</strong>`;
                    
                    // Highlight if it matches the source category
                    if (category === sourceCategory) {
                        categoryHeader.classList.add('same-category');
                        categoryHeader.innerHTML += ' <span class="badge bg-primary">Same Category</span>';
                    }
                    
                    recommendationsList.appendChild(categoryHeader);
                }
                
                // Add apps in this category
                apps.forEach(app => {
                    const item = createAppListItem(app, true, sourceApp, sourceCategory, sourceGenres);
                    recommendationsList.appendChild(item);
                });
            });
            
            // If no recommendations were found, show a message
            if (sortedRecommendations.length === 0) {
                const noResults = document.createElement('div');
                noResults.classList.add('alert', 'alert-info');
                noResults.textContent = 'No recommended apps found.';
                recommendationsList.appendChild(noResults);
            }
        } catch (error) {
            console.error('Error displaying recommendations:', error);
            showError('Error displaying recommendations. Please try again.');
            // Show popular apps as fallback
            loadPopularApps();
        }
    }
    
    // Function to display popular recommendations (fallback)
    function displayPopularRecommendations(popularApps) {
        if (popularApps && popularApps.length > 0) {
            const fallbackDiv = document.createElement('div');
            fallbackDiv.classList.add('mt-4');
            fallbackDiv.innerHTML = `
                <h4>You might be interested in these popular apps:</h4>
                <div class="list-group" id="fallbackRecommendations"></div>
            `;
            
            recommendationsContainer.parentNode.insertBefore(fallbackDiv, recommendationsContainer.nextSibling);
            
            const fallbackList = document.getElementById('fallbackRecommendations');
            
            popularApps.forEach(app => {
                const item = createAppListItem(app);
                fallbackList.appendChild(item);
            });
        }
    }
    
    // Function to display popular apps
    function displayPopularApps(apps) {
        popularAppsList.innerHTML = '';
        
        apps.forEach(app => {
            const item = createAppListItem(app);
            popularAppsList.appendChild(item);
        });
    }
    
    // Function to create an app list item
    // Modify the existing function to add a reviews button
    function createAppListItem(app, showMatchScore = false, sourceApp = '', sourceCategory = '', sourceGenres = '') {
        const item = document.createElement('div');
        item.classList.add('list-group-item');
        
        // Format the installs number
        const installs = typeof app.Installs === 'number' ? 
            app.Installs.toLocaleString() : app.Installs || 'N/A';
        
        // Format the reviews number
        const reviews = typeof app.Reviews === 'number' ? 
            app.Reviews.toLocaleString() : app.Reviews || 'N/A';
        
        // Handle potentially missing or null rating
        const rating = app.Rating !== undefined && app.Rating !== null ? 
            `★ ${parseFloat(app.Rating).toFixed(1)}` : 'No rating';
            
        // Get the match score if available, ensure it's a number
        const matchScore = app.MatchScore !== undefined ? 
            parseInt(app.MatchScore) : null;
        
        // Create match score HTML with improved visualization
        const matchScoreHtml = matchScore !== null ? 
            `<div class="match-score">
                <div class="progress" style="height: 8px; width: 80px;">
                    <div class="progress-bar ${getMatchScoreColorClass(matchScore)}" 
                         role="progressbar" 
                         style="width: ${matchScore}%;" 
                         aria-valuenow="${matchScore}" 
                         aria-valuemin="0" 
                         aria-valuemax="100">
                    </div>
                </div>
                <small>${matchScore}% match</small>
            </div>` : '';
        
        // Get genres if available, format it better for display
        let genres = app.Genres ? app.Genres : null;
        if (genres && genres.includes(';')) {
            // Format multi-genre entries with commas
            genres = genres.split(';').join(', ');
        }
        
        // Remove ScoreBreakdown property as it's only for debugging
        if (app.ScoreBreakdown) {
            delete app.ScoreBreakdown;
        }
        
        // Content rating might be in either format (with space or underscore)
        const contentRating = app.Content_Rating || app['Content Rating'] || null;
        
        // Generate similarity reason
        let similarityReason = '';
        if (showMatchScore && matchScore) {
            // Determine why this app is being recommended
            if (app.Category === sourceCategory) {
                similarityReason = `<div class="similarity-reason same-category">Same category as ${sourceCategory}</div>`;
            } else if (matchScore >= 80) {
                similarityReason = `<div class="similarity-reason">Similar functionality to ${sourceCategory}</div>`;
            } else if (genres && sourceGenres && genres.toLowerCase().includes(sourceGenres.toLowerCase())) {
                similarityReason = `<div class="similarity-reason">Similar genre: ${genres}</div>`;
            } else if (app.App.toLowerCase().includes(sourceCategory.toLowerCase()) || 
                      sourceCategory.toLowerCase().includes(app.App.toLowerCase())) {
                similarityReason = `<div class="similarity-reason">Part of the ${app.App.split(' ')[0]} app family</div>`;
            }
        }
        
        // Add a reviews button
        const reviewsButton = `
            <button class="btn btn-sm btn-outline-primary view-reviews-btn mt-2" 
                    data-app-name="${app.App || 'Unknown App'}">
                View ${reviews} Reviews
            </button>
        `;
        
        item.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <h5 class="mb-1">${app.App || 'Unknown App'}</h5>
                <span class="app-rating">${rating}</span>
            </div>
            <div class="d-flex justify-content-between">
                <span class="app-category">${app.Category || 'Uncategorized'}</span>
                <span class="app-installs">${installs} installs</span>
            </div>
            ${genres ? `<div class="app-genres mb-1">${genres}</div>` : ''}
            ${similarityReason}
            <div class="d-flex justify-content-between align-items-center">
                <small class="app-reviews">${reviews} reviews</small>
                ${showMatchScore ? matchScoreHtml : ''}
            </div>
            ${contentRating ? `<small class="content-rating">Content: ${contentRating}</small>` : ''}
            ${reviewsButton}
        `;
        
        // Add event listener for the reviews button
        setTimeout(() => {
            const button = item.querySelector('.view-reviews-btn');
            if (button) {
                button.addEventListener('click', function() {
                    const appName = this.getAttribute('data-app-name');
                    openReviewsModal(appName);
                });
            }
        }, 0);
        
        return item;
    }
    
    // Function to get CSS class based on match score
    function getMatchScoreColorClass(score) {
        if (score >= 85) return 'bg-success';  // Excellent match
        if (score >= 70) return 'bg-info';     // Good match
        if (score >= 50) return 'bg-warning';  // Fair match
        return 'bg-danger';                    // Poor match
    }
    
    // Function to show error message
    function showError(message) {
        errorContainer.textContent = message;
        errorContainer.classList.remove('d-none');
    }
    
    // Function to reset UI
    function resetUI() {
        errorContainer.classList.add('d-none');
        recommendationsContainer.classList.add('d-none');
        
        // Remove any fallback recommendations
        const fallbackDiv = document.querySelector('[id^="fallbackRecommendations"]');
        if (fallbackDiv && fallbackDiv.parentNode) {
            fallbackDiv.parentNode.remove();
        }
    }
    
    // Function to load dataset information
    function loadDatasetInfo() {
        fetch('/api/dataset')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success && data.dataset_info) {
                    // Add dataset info to the footer
                    const footerDiv = document.querySelector('.card-footer');
                    if (footerDiv) {
                        const info = data.dataset_info;
                        footerDiv.innerHTML = `
                            <div class="mt-2">
                                <p class="mb-1">Based on ${info.name} (valid until ${info.data_valid_until})</p>
                                <p class="mb-1">Dataset includes ${info.num_apps.toLocaleString()} apps across ${info.categories.length} categories</p>
                                <p class="mb-0">Average rating: ${info.average_rating} ★ | Most popular category: ${info.top_category}</p>
                            </div>
                        `;
                    }
                }
            })
            .catch(error => {
                console.error('Error loading dataset info:', error);
            });
    }
});

    // Add this function to implement retry logic
    function fetchWithRetry(url, options, maxRetries = 3) {
        return new Promise((resolve, reject) => {
            const attempt = (retryCount) => {
                fetch(url, options)
                    .then(response => {
                        // First check if the response is ok
                        if (!response.ok) {
                            throw new Error(`HTTP error! Status: ${response.status}`);
                        }
                        
                        // Try to parse JSON, but handle parsing errors gracefully
                        return response.json().then(data => {
                            return { status: response.status, data: data };
                        }).catch(err => {
                            // JSON parsing error
                            throw new Error(`Invalid JSON response: ${err.message}`);
                        });
                    })
                    .then(resolve)
                    .catch(error => {
                        console.error(`Fetch attempt ${retryCount + 1} failed:`, error.message);
                        
                        if (retryCount < maxRetries) {
                            console.log(`Retry attempt ${retryCount + 1} of ${maxRetries}`);
                            // Exponential backoff: wait longer between retries
                            setTimeout(() => attempt(retryCount + 1), 1000 * Math.pow(2, retryCount)); 
                        } else {
                            reject(error);
                        }
                    });
            };
            attempt(0);
        });
    }

    // Add this function for better error logging
    function logError(context, error) {
        const errorInfo = {
            context: context,
            message: error.message,
            stack: error.stack,
            timestamp: new Date().toISOString()
        };
        
        console.error('Application error:', errorInfo);
    }
        // You could also send this to a server endpoint for logging
        // fetch('/api/log-error', {
        //     method: 'POST',
        //     headers: { 'Content-Type': 'application/json' },
        //     body: JSON.stringify(errorInfo)
        // }).catch(e => console.error('Failed to log error:', e));

    // Function to open the reviews modal
    function openReviewsModal(appName) {
        // Set the app name in the modal
        document.getElementById('reviewsModalLabel').textContent = `Reviews for ${appName}`;
        
        // Reset the modal state
        document.getElementById('reviewsContainer').classList.remove('d-none');
        document.getElementById('reviewsError').classList.add('d-none');
        document.getElementById('reviewsList').innerHTML = '';
        
        // Show loading indicator
        document.getElementById('reviewsLoading').classList.remove('d-none');
        
        // Load reviews
        loadAppReviews(appName);
        
        // Open the modal
        const reviewsModal = new bootstrap.Modal(document.getElementById('reviewsModal'));
        reviewsModal.show();
    }

    // Function to load app reviews
    function loadAppReviews(appName, page = 1) {
        fetch(`/api/reviews/${encodeURIComponent(appName)}?page=${page}`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('reviewsLoading').classList.add('d-none');
                
                if (data.status === 'success') {
                    displayReviews(data.reviews);
                    setupPagination(data.current_page, data.pages, appName);
                } else {
                    throw new Error(data.message);
                }
            })
            .catch(error => {
                document.getElementById('reviewsLoading').classList.add('d-none');
                const errorElement = document.getElementById('reviewsError');
                errorElement.textContent = `Error loading reviews: ${error.message}`;
                errorElement.classList.remove('d-none');
            });
    }

    // Function to display reviews
    function displayReviews(reviews) {
        const reviewsList = document.getElementById('reviewsList');
        
        if (reviews.length === 0) {
            reviewsList.innerHTML = '<div class="alert alert-info">No reviews available for this app.</div>';
            return;
        }
        
        reviews.forEach(review => {
            const reviewElement = document.createElement('div');
            reviewElement.classList.add('review-item', 'mb-3', 'p-3', 'border', 'rounded');
            
            // Generate star rating HTML
            let starsHtml = '';
            for (let i = 1; i <= 5; i++) {
                if (i <= review.rating) {
                    starsHtml += '<span class="star filled">★</span>';
                } else {
                    starsHtml += '<span class="star">☆</span>';
                }
            }
            
            reviewElement.innerHTML = `
                <div class="d-flex justify-content-between">
                    <div class="stars-display">${starsHtml}</div>
                    <small class="text-muted">${review.created_at}</small>
                </div>
                <p class="mt-2">${review.content}</p>
                <small class="text-muted">By ${review.author || 'Anonymous'}</small>
            `;
            
            reviewsList.appendChild(reviewElement);
        });
}