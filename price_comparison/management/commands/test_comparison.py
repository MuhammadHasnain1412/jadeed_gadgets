from django.core.management.base import BaseCommand
from price_comparison.services import PriceComparisonService
from price_comparison.models import CompetitorProduct
from products.models import Product
from accounts.models import User


class Command(BaseCommand):
    help = 'Test price comparison functionality with sample data'

    def handle(self, *args, **options):
        self.stdout.write("🧪 Testing Price Comparison System...")
        
        # Create some sample competitor products for testing
        self.create_sample_competitor_products()
        
        # Get a seller's products and run comparison
        self.test_product_comparison()
        
        self.stdout.write("✅ Price comparison test completed!")
    
    def create_sample_competitor_products(self):
        """Create sample competitor products for testing"""
        self.stdout.write("📦 Creating sample competitor products...")
        
        # Sample Asif products
        asif_products = [
            {'title': 'Dell Inspiron 15 3000 Laptop', 'price': 85000, 'url': 'https://asifcomputers.com/dell-inspiron-15'},
            {'title': 'HP Pavilion 14 Core i5 Laptop', 'price': 95000, 'url': 'https://asifcomputers.com/hp-pavilion-14'},
            {'title': 'Lenovo ThinkPad E14 Business Laptop', 'price': 120000, 'url': 'https://asifcomputers.com/lenovo-thinkpad-e14'},
            {'title': 'ASUS VivoBook 15 AMD Ryzen 5', 'price': 78000, 'url': 'https://asifcomputers.com/asus-vivobook-15'},
        ]
        
        # Sample PakLap products
        paklap_products = [
            {'title': 'Dell Inspiron 15 3000 Core i3', 'price': 88000, 'url': 'https://paklap.pk/dell-inspiron-15'},
            {'title': 'HP Pavilion 14 Intel Core i5', 'price': 92000, 'url': 'https://paklap.pk/hp-pavilion-14'},
            {'title': 'Lenovo ThinkPad E14 Gen 3', 'price': 125000, 'url': 'https://paklap.pk/lenovo-thinkpad-e14'},
            {'title': 'ASUS VivoBook 15 Ryzen 5 5500U', 'price': 82000, 'url': 'https://paklap.pk/asus-vivobook-15'},
        ]
        
        # Create Asif products
        for product_data in asif_products:
            CompetitorProduct.objects.get_or_create(
                title=product_data['title'],
                competitor='asif',
                defaults={
                    'price': product_data['price'],
                    'url': product_data['url'],
                    'is_active': True
                }
            )
        
        # Create PakLap products
        for product_data in paklap_products:
            CompetitorProduct.objects.get_or_create(
                title=product_data['title'],
                competitor='paklap',
                defaults={
                    'price': product_data['price'],
                    'url': product_data['url'],
                    'is_active': True
                }
            )
        
        self.stdout.write(f"✅ Created {len(asif_products)} Asif products and {len(paklap_products)} PakLap products")
    
    def test_product_comparison(self):
        """Test the comparison functionality"""
        self.stdout.write("🔍 Testing product comparison matching...")
        
        # Get first seller user
        try:
            seller = User.objects.filter(role='seller').first()
            if not seller:
                self.stdout.write("⚠️ No seller found. Please create a seller user first.")
                return
            
            # Get seller's products
            products = Product.objects.filter(seller=seller, is_active=True)[:5]
            
            if not products:
                self.stdout.write("⚠️ No products found for seller. Please add some products first.")
                return
            
            # Initialize comparison service
            comparison_service = PriceComparisonService()
            
            self.stdout.write(f"🔄 Running comparison for {products.count()} products...")
            
            for product in products:
                self.stdout.write(f"\n📱 Product: {product.name}")
                self.stdout.write(f"💰 Price: Rs. {product.price}")
                
                # Run comparison
                comparison = comparison_service.compare_single_product(product)
                
                # Display results
                if comparison.best_asif_match:
                    self.stdout.write(f"🔍 Asif Match: {comparison.best_asif_match.title}")
                    self.stdout.write(f"💵 Asif Price: Rs. {comparison.best_asif_match.price}")
                    self.stdout.write(f"📊 Price Difference: Rs. {comparison.asif_price_difference}")
                    self.stdout.write(f"🎯 Confidence: {comparison.match_confidence_asif:.2f}")
                else:
                    self.stdout.write("❌ No Asif match found")
                
                if comparison.best_paklap_match:
                    self.stdout.write(f"🔍 PakLap Match: {comparison.best_paklap_match.title}")
                    self.stdout.write(f"💵 PakLap Price: Rs. {comparison.best_paklap_match.price}")
                    self.stdout.write(f"📊 Price Difference: Rs. {comparison.paklap_price_difference}")
                    self.stdout.write(f"🎯 Confidence: {comparison.match_confidence_paklap:.2f}")
                else:
                    self.stdout.write("❌ No PakLap match found")
                
                self.stdout.write("-" * 50)
            
            # Get pricing insights
            insights = comparison_service.get_price_insights(seller)
            self.stdout.write("\n📈 Pricing Insights:")
            self.stdout.write(f"📦 Total Products: {insights['total_products']}")
            self.stdout.write(f"✅ Competitive: {insights['competitive_count']}")
            self.stdout.write(f"📈 Overpriced: {insights['overpriced_count']}")
            self.stdout.write(f"📉 Underpriced: {insights['underpriced_count']}")
            self.stdout.write(f"❓ No Match: {insights['no_match_count']}")
            self.stdout.write(f"🎯 Competitive %: {insights['competitive_percentage']:.1f}%")
            
        except Exception as e:
            self.stdout.write(f"❌ Error during testing: {str(e)}")
            import traceback
            self.stdout.write(traceback.format_exc())
