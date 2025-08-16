from django.db.models import Count, Q
from django.core.cache import cache
from products.models import Product
from .models import UserInteraction, RecommendationCache
from django.contrib.auth import get_user_model
from collections import defaultdict, Counter
import pickle
import os
from pathlib import Path

User = get_user_model()

class RecommendationEngine:
    def __init__(self):
        self.model = None
        self.user_item_matrix = {}
        self.item_similarities = {}
        
    def load_model(self):
        """Load trained model from file"""
        model_path = Path(__file__).parent / 'recommendation_model.pkl'
        if model_path.exists():
            try:
                with open(model_path, 'rb') as f:
                    model_data = pickle.load(f)
                    self.user_item_matrix = model_data.get('user_item_matrix', {})
                    self.item_similarities = model_data.get('item_similarities', {})
                return True
            except Exception as e:
                print(f"Error loading model: {e}")
                return False
        return False
    
    def get_popular_products(self, n=10):
        """Get most popular products as fallback"""
        cache_key = f'popular_products_{n}'
        popular = cache.get(cache_key)
        
        if popular is None:
            popular = list(Product.objects.filter(is_active=True)
                         .annotate(interaction_count=Count('userinteraction'))
                         .order_by('-interaction_count', '-rating', '-created_at')[:n]
                         .values_list('id', flat=True))
            cache.set(cache_key, popular, 3600)  # Cache for 1 hour
        
        return popular
    
    def get_category_based_recommendations(self, user, n=10):
        """Get recommendations based on user's interaction history"""
        # Get user's favorite categories
        user_interactions = UserInteraction.objects.filter(user=user)
        if not user_interactions.exists():
            return self.get_popular_products(n)
        
        # Get categories from user's interactions
        interacted_products = user_interactions.values_list('product', flat=True)
        categories = Product.objects.filter(id__in=interacted_products)\
                                  .values_list('category', flat=True)
        
        if not categories:
            return self.get_popular_products(n)
        
        # Get most common categories
        from collections import Counter
        category_counts = Counter(categories)
        top_categories = [cat for cat, count in category_counts.most_common(3)]
        
        # Get products from these categories (excluding already interacted)
        recommendations = list(Product.objects.filter(
            category__in=top_categories,
            is_active=True
        ).exclude(
            id__in=interacted_products
        ).order_by('-rating', '-created_at')[:n].values_list('id', flat=True))
        
        # Fill remaining slots with popular products if needed
        if len(recommendations) < n:
            popular = self.get_popular_products(n - len(recommendations))
            recommendations.extend([p for p in popular if p not in recommendations])
        
        return recommendations[:n]
    
    def get_collaborative_recommendations(self, user, n=10):
        """Get recommendations using simple collaborative filtering"""
        if not self.load_model():
            return self.get_category_based_recommendations(user, n)
        
        try:
            user_id = user.id
            if user_id not in self.user_item_matrix:
                return self.get_category_based_recommendations(user, n)
            
            # Get user's interacted items
            user_items = self.user_item_matrix[user_id]
            
            # Find similar items and calculate scores
            item_scores = defaultdict(float)
            
            for item_id, weight in user_items:
                if item_id in self.item_similarities:
                    for similar_item, similarity in self.item_similarities[item_id].items():
                        # Don't recommend items the user has already interacted with
                        if not any(item[0] == similar_item for item in user_items):
                            item_scores[similar_item] += similarity * weight
            
            # Sort by score and get top N
            sorted_items = sorted(item_scores.items(), key=lambda x: x[1], reverse=True)
            recommendations = []
            
            for item_id, score in sorted_items[:n]:
                if Product.objects.filter(id=item_id, is_active=True).exists():
                    recommendations.append(item_id)
            
            return recommendations[:n]
            
        except Exception as e:
            print(f"Error in collaborative filtering: {e}")
            return self.get_category_based_recommendations(user, n)
    
    def get_recommendations(self, user, n=10, use_cache=True):
        """Main recommendation function"""
        if not user.is_authenticated:
            return self.get_popular_products(n)
        
        # Check cache first
        cache_key = f'recommendations_{user.id}_{n}'
        if use_cache:
            cached_recs = cache.get(cache_key)
            if cached_recs:
                return cached_recs
        
        # Try collaborative filtering first
        recommendations = self.get_collaborative_recommendations(user, n)
        
        # Fallback to category-based if needed
        if not recommendations:
            recommendations = self.get_category_based_recommendations(user, n)
        
        # Final fallback to popular products
        if not recommendations:
            recommendations = self.get_popular_products(n)
        
        # Cache the results
        if use_cache:
            cache.set(cache_key, recommendations, 1800)  # Cache for 30 minutes
        
        return recommendations
    
    def record_interaction(self, user, product, interaction_type):
        """Record user interaction and invalidate cache"""
        if not user.is_authenticated:
            return
        
        # Create or update interaction
        interaction, created = UserInteraction.objects.get_or_create(
            user=user,
            product=product,
            interaction_type=interaction_type,
            defaults={'timestamp': None}
        )
        
        if not created:
            # Update timestamp if interaction already exists
            interaction.save()
        
        # Invalidate user's recommendation cache
        cache_keys = [f'recommendations_{user.id}_{n}' for n in [5, 10, 15, 20]]
        cache.delete_many(cache_keys)

# Global instance
recommendation_engine = RecommendationEngine()

# Convenience functions
def get_recommendations_for_user(user, n=10):
    """Get recommendations for a user"""
    return recommendation_engine.get_recommendations(user, n)

def record_user_interaction(user, product, interaction_type):
    """Record user interaction"""
    recommendation_engine.record_interaction(user, product, interaction_type)

def get_popular_products(n=10):
    """Get popular products"""
    return recommendation_engine.get_popular_products(n)
