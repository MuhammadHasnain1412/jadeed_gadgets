from django.core.management.base import BaseCommand
from recommendations.models import UserInteraction
from collections import defaultdict
import pickle
from pathlib import Path

class Command(BaseCommand):
    help = 'Train recommendation model using simple collaborative filtering'

    def handle(self, *args, **options):
        # Fetch all interactions
        interactions = UserInteraction.objects.all()
        
        if not interactions.exists():
            self.stdout.write(self.style.WARNING('No interactions found. Cannot train model.'))
            return

        # Build user-item interaction matrix
        user_item_matrix = defaultdict(set)
        
        for interaction in interactions:
            user_id = interaction.user.id
            product_id = interaction.product.id
            
            # Weight different interaction types
            weight = 1
            if interaction.interaction_type == 'purchase':
                weight = 3
            elif interaction.interaction_type == 'add_to_cart':
                weight = 2
            elif interaction.interaction_type == 'wishlist':
                weight = 2
            elif interaction.interaction_type == 'view':
                weight = 1
            
            user_item_matrix[user_id].add((product_id, weight))

        # Calculate item similarities (simple Jaccard similarity)
        item_similarities = {}
        all_items = set()
        for user_items in user_item_matrix.values():
            for item_id, weight in user_items:
                all_items.add(item_id)
        
        all_items = list(all_items)
        for i, item1 in enumerate(all_items):
            item_similarities[item1] = {}
            for j, item2 in enumerate(all_items):
                if i != j:
                    # Users who interacted with both items
                    users_item1 = set(user_id for user_id, items in user_item_matrix.items() 
                                    if any(item_id == item1 for item_id, weight in items))
                    users_item2 = set(user_id for user_id, items in user_item_matrix.items() 
                                    if any(item_id == item2 for item_id, weight in items))
                    
                    if users_item1 and users_item2:
                        intersection = len(users_item1.intersection(users_item2))
                        union = len(users_item1.union(users_item2))
                        similarity = intersection / union if union > 0 else 0
                        item_similarities[item1][item2] = similarity

        # Save the trained model
        model_data = {
            'user_item_matrix': dict(user_item_matrix),
            'item_similarities': item_similarities,
        }
        
        model_path = Path(__file__).parent.parent.parent / 'recommendation_model.pkl'
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)

        user_count = len(set(interaction.user.id for interaction in interactions))
        product_count = len(set(interaction.product.id for interaction in interactions))
        
        self.stdout.write(self.style.SUCCESS(f'✅ Model trained and saved to {model_path}'))
        self.stdout.write(self.style.SUCCESS(f'📊 Trained on {user_count} users and {product_count} products'))
        self.stdout.write(self.style.SUCCESS(f'🔄 Total interactions: {interactions.count()}'))
