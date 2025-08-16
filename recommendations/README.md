# Recommendations App Integration

This document describes the integration of the AI-powered recommendation system into the Jadeed Gadgets website.

## Overview

The recommendation system provides personalized product suggestions to users based on their browsing history, purchase behavior, and interactions with products. It uses collaborative filtering and content-based filtering to deliver relevant recommendations.

## Features

### Core Functionality
- **Personalized Recommendations**: AI-powered suggestions based on user behavior
- **Popular Products**: Trending products for new users or fallback recommendations
- **Category-based Recommendations**: Products within specific categories
- **Interaction Tracking**: Automatic recording of user interactions (views, purchases, wishlist, cart)
- **Real-time Updates**: Recommendations update as users interact with products

### User Interface
- **For You Page**: Dedicated page for personalized recommendations
- **Navigation Integration**: Easy access via main navigation
- **Activity History**: User can view their interaction history
- **Responsive Design**: Works seamlessly on all devices

## Technical Implementation

### Models
- `UserInteraction`: Tracks user interactions with products
- `RecommendationCache`: Caches recommendations for performance

### Views
- `recommendations_view`: Main recommendations page
- `popular_products`: Popular products page
- `similar_products`: Products similar to a specific item
- `category_recommendations`: Recommendations within a category
- `interaction_history`: User's activity history
- `record_interaction`: API endpoint for tracking interactions

### Recommendation Engine
- **Collaborative Filtering**: Uses LightFM library for advanced recommendations
- **Content-based Filtering**: Recommendations based on product categories and attributes
- **Fallback System**: Popular products for new users or when personalized data is insufficient
- **Caching**: Redis-based caching for improved performance

## Installation and Setup

### Prerequisites
- Django 5.2+
- Python 3.8+
- Required packages: `lightfm`, `numpy`, `scikit-learn`

### Steps
1. The `recommendations` app is already integrated into the project
2. Run migrations: `python manage.py migrate`
3. Install required packages: `pip install lightfm numpy scikit-learn`
4. Train the initial model: `python manage.py train_recommendation`

## Usage

### For Users
1. **Access Recommendations**: Click "For You" in the main navigation
2. **Browse Popular Products**: Visit the popular products page
3. **View Activity**: Check your interaction history
4. **Automatic Tracking**: Interactions are tracked automatically as you browse

### For Developers
1. **Record Interactions**: Use the API endpoint or `record_user_interaction()` function
2. **Get Recommendations**: Use `get_recommendations_for_user()` function
3. **Train Model**: Run `python manage.py train_recommendation` periodically

## API Endpoints

### Record Interaction
```
POST /recommendations/api/record-interaction/
Content-Type: application/json

{
    "product_id": 123,
    "interaction_type": "view"
}
```

### Available Interaction Types
- `view`: User viewed a product
- `purchase`: User purchased a product
- `add_to_cart`: User added product to cart
- `wishlist`: User added product to wishlist

## URL Structure

```
/recommendations/                    # Main recommendations page
/recommendations/popular/            # Popular products
/recommendations/similar/<id>/       # Similar products
/recommendations/category/<cat>/     # Category recommendations
/recommendations/history/            # User's interaction history
/recommendations/api/record-interaction/  # API endpoint
```

## Performance Considerations

### Caching
- Recommendations are cached for 30 minutes
- Popular products are cached for 1 hour
- Cache is invalidated when user interactions change

### Model Training
- Train the recommendation model periodically (weekly or monthly)
- Use `python manage.py train_recommendation` command
- Training requires sufficient user interaction data

## Integration Points

### Navigation
- Added "For You" link in main navigation for authenticated buyers
- Visible only to users with buyer role

### Templates
- Follows existing design patterns and styling
- Uses Bootstrap 5 and custom CSS variables
- Responsive design with mobile-first approach

### Context Processors
- `recommendations_context`: Adds sidebar recommendations to all pages
- Provides 4 recommended products in template context

### JavaScript Integration
- Automatic interaction tracking via `recommendations.js`
- CSRF token handling for API calls
- Real-time interaction recording

## Testing

Run tests with:
```bash
python manage.py test recommendations
```

Test coverage includes:
- Model functionality
- View responses
- API endpoints
- Recommendation engine
- User interaction tracking

## Monitoring and Analytics

### Admin Interface
- View user interactions in Django admin
- Monitor recommendation cache performance
- Track system usage statistics

### Logging
- All recommendation engine operations are logged
- Error tracking for failed recommendations
- Performance metrics for optimization

## Future Enhancements

### Planned Features
- **A/B Testing**: Test different recommendation algorithms
- **Real-time Recommendations**: WebSocket-based live updates
- **Advanced Filtering**: Price range, brand preferences, etc.
- **Cross-selling**: Complement product recommendations
- **Email Recommendations**: Personalized email campaigns

### Scalability
- Move to dedicated recommendation service
- Implement Apache Kafka for real-time data streaming
- Use machine learning pipelines for continuous model improvement

## Troubleshooting

### Common Issues
1. **No Recommendations**: User needs more interactions or model needs training
2. **Slow Performance**: Check caching configuration and database queries
3. **Training Errors**: Ensure sufficient user interaction data exists

### Debug Mode
- Enable Django debug mode for detailed error messages
- Check Django logs for recommendation engine errors
- Use Django admin to inspect user interactions

## Support

For technical support or questions about the recommendation system:
1. Check the Django admin interface for user interactions
2. Review the recommendation engine logs
3. Verify that the model has been trained with sufficient data
4. Ensure all required packages are installed

---

*This recommendation system was integrated from the NEW1 folder and adapted to work seamlessly with the existing Jadeed Gadgets website architecture.*
