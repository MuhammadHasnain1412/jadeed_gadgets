from django.core.management.base import BaseCommand
from django.apps import apps
from lightfm import LightFM
from lightfm.data import Dataset
import pickle
import os

class Command(BaseCommand):
    help = 'Train recommendation model'

    def handle(self, *args, **kwargs):
        # Get models dynamically
        Order = apps.get_model('orders', 'Order')
        User = apps.get_model('accounts', 'CustomUser')  # replace with your actual model name
        Product = apps.get_model('products', 'Product')

        dataset = Dataset()

        # Fetch all unique users and product IDs from orders
        users = Order.objects.values_list("user__id", flat=True).distinct()
        items = Order.objects.values_list("product__id", flat=True).distinct()

        # Map users and items
        dataset.fit((str(u) for u in users), (str(p) for p in items))

        # Build user-item interaction matrix
        interactions, _ = dataset.build_interactions(
            ((str(order.user.id), str(order.product.id)) for order in Order.objects.all())
        )

        # Train the model
        model = LightFM(loss="warp")
        model.fit(interactions, epochs=10, num_threads=2)

        # Prepare data to save
        model_data = {
            "model": model,
            "user_mapping": dataset.mapping()[0],
            "item_mapping": dataset.mapping()[2],
        }

        # Ensure the model directory exists
        model_dir = os.path.join("recommendation", "models")
        os.makedirs(model_dir, exist_ok=True)

        # Save the model
        model_path = os.path.join(model_dir, "recommendation_model.pkl")
        with open(model_path, "wb") as f:
            pickle.dump(model_data, f)

        self.stdout.write(self.style.SUCCESS("✅ Recommendation model trained and saved."))
