from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from products.models import Product
from .models import UserInteraction
from .recommender import get_recommendations_for_user, record_user_interaction

User = get_user_model()

class RecommendationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='buyer'
        )
        
        # Create test products
        self.product1 = Product.objects.create(
            name='Test Laptop',
            brand='TestBrand',
            price=50000,
            stock=10,
            category='laptop',
            description='Test laptop description',
            is_active=True
        )
        
        self.product2 = Product.objects.create(
            name='Test Mobile',
            brand='TestBrand',
            price=25000,
            stock=15,
            category='mobile',
            description='Test mobile description',
            is_active=True
        )
    
    def test_record_user_interaction(self):
        """Test recording user interactions"""
        record_user_interaction(self.user, self.product1, 'view')
        
        interaction = UserInteraction.objects.filter(
            user=self.user,
            product=self.product1,
            interaction_type='view'
        ).first()
        
        self.assertIsNotNone(interaction)
        self.assertEqual(interaction.user, self.user)
        self.assertEqual(interaction.product, self.product1)
        self.assertEqual(interaction.interaction_type, 'view')
    
    def test_get_recommendations_for_new_user(self):
        """Test getting recommendations for a new user with no interactions"""
        recommendations = get_recommendations_for_user(self.user)
        self.assertIsInstance(recommendations, list)
        # Should return popular products for new users
    
    def test_get_recommendations_with_interactions(self):
        """Test getting recommendations for a user with interactions"""
        # Record some interactions
        record_user_interaction(self.user, self.product1, 'view')
        record_user_interaction(self.user, self.product1, 'add_to_cart')
        
        recommendations = get_recommendations_for_user(self.user)
        self.assertIsInstance(recommendations, list)
    
    def test_recommendations_view_requires_login(self):
        """Test that recommendations view requires login"""
        response = self.client.get(reverse('recommendations:recommendations'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_recommendations_view_with_login(self):
        """Test recommendations view with logged in user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('recommendations:recommendations'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Recommended Products')
    
    def test_popular_products_view(self):
        """Test popular products view"""
        response = self.client.get(reverse('recommendations:popular_products'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Popular Products')
    
    def test_record_interaction_api(self):
        """Test the API endpoint for recording interactions"""
        self.client.login(username='testuser', password='testpass123')
        
        data = {
            'product_id': self.product1.id,
            'interaction_type': 'view'
        }
        
        response = self.client.post(
            reverse('recommendations:record_interaction'),
            data=data,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Check that interaction was recorded
        interaction = UserInteraction.objects.filter(
            user=self.user,
            product=self.product1,
            interaction_type='view'
        ).first()
        
        self.assertIsNotNone(interaction)
    
    def test_record_interaction_api_invalid_data(self):
        """Test API endpoint with invalid data"""
        self.client.login(username='testuser', password='testpass123')
        
        data = {
            'product_id': 999,  # Non-existent product
            'interaction_type': 'view'
        }
        
        response = self.client.post(
            reverse('recommendations:record_interaction'),
            data=data,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)  # Product not found
    
    def test_record_interaction_api_unauthenticated(self):
        """Test API endpoint without authentication"""
        data = {
            'product_id': self.product1.id,
            'interaction_type': 'view'
        }
        
        response = self.client.post(
            reverse('recommendations:record_interaction'),
            data=data,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)  # Unauthorized

class UserInteractionModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='buyer'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            brand='TestBrand',
            price=10000,
            stock=5,
            category='laptop',
            description='Test product description',
            is_active=True
        )
    
    def test_user_interaction_creation(self):
        """Test creating a user interaction"""
        interaction = UserInteraction.objects.create(
            user=self.user,
            product=self.product,
            interaction_type='view'
        )
        
        self.assertEqual(interaction.user, self.user)
        self.assertEqual(interaction.product, self.product)
        self.assertEqual(interaction.interaction_type, 'view')
        self.assertIsNotNone(interaction.timestamp)
    
    def test_user_interaction_str_method(self):
        """Test the string representation of UserInteraction"""
        interaction = UserInteraction.objects.create(
            user=self.user,
            product=self.product,
            interaction_type='view'
        )
        
        expected_str = f"{self.user.username} - View - {self.product.name}"
        self.assertEqual(str(interaction), expected_str)
    
    def test_unique_together_constraint(self):
        """Test that the unique_together constraint works"""
        # Create first interaction
        UserInteraction.objects.create(
            user=self.user,
            product=self.product,
            interaction_type='view'
        )
        
        # Try to create duplicate - should update timestamp instead of creating new
        interaction2 = UserInteraction.objects.create(
            user=self.user,
            product=self.product,
            interaction_type='view'
        )
        
        # Should only have one interaction for this combination
        count = UserInteraction.objects.filter(
            user=self.user,
            product=self.product,
            interaction_type='view'
        ).count()
        
        self.assertEqual(count, 1)
