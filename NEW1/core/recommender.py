import numpy as np
from lightfm import LightFM
from lightfm.data import Dataset
from django.db.models import Count
from core.models import UserInteraction, Product  # ADDED Product IMPORT

def train_model():
    # Fetch all interactions
    interactions = UserInteraction.objects.all()
    
    if not interactions.exists():
        return None, None
    
    # Prepare data
    user_ids = [interaction.user_id for interaction in interactions]
    item_ids = [interaction.product_id for interaction in interactions]
    
    # Create dataset
    dataset = Dataset()
    dataset.fit(users=set(user_ids), 
                items=set(item_ids))
    
    # Build interactions matrix
    (interactions_matrix, weights) = dataset.build_interactions(
        [(user_id, item_id) for user_id, item_id in zip(user_ids, item_ids)]
    )
    
    # Train model
    model = LightFM(loss='warp')
    model.fit(interactions_matrix, epochs=30)
    
    return model, dataset

def recommend(user_id, n=5):
    # Get popular items as fallback
    popular_items = list(Product.objects.annotate(  # NOW Product IS DEFINED
        view_count=Count('userview')
    ).order_by('-view_count')[:n].values_list('id', flat=True))
    
    # Train model
    model, dataset = train_model()
    if model is None or dataset is None:
        return popular_items
    
    # Get mappings
    user_id_map, _, item_id_map, _ = dataset.mapping()
    
    # Get all item IDs
    all_item_ids = list(item_id_map.keys())
    
    # Convert user ID to LightFM's internal index
    try:
        user_internal_id = user_id_map[user_id]
    except KeyError:
        # User not in training data
        return popular_items
    
    # Generate predictions for all items
    if not all_item_ids:
        return popular_items
        
    scores = model.predict(
        user_ids=user_internal_id,
        item_ids=np.array(list(item_id_map.values()))
    )
    # Get top N recommendations
    top_indices = np.argsort(-scores)[:n]
    
    # Map back to original item IDs
    reverse_item_map = {v: k for k, v in item_id_map.items()}
    return [reverse_item_map[i] for i in top_indices]