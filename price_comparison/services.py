import re
from difflib import SequenceMatcher
from django.db.models import Q
from .models import CompetitorProduct, ProductComparison
from products.models import Product


class PriceComparisonService:
    """Service for handling price comparison logic"""
    
    def __init__(self):
        self.min_confidence = 0.4  # Minimum confidence score for matching (increased for better accuracy)
    
    def clean_product_name(self, name):
        """Clean and normalize product name for better matching"""
        # Convert to lowercase
        name = name.lower()
        
        # Remove common words that don't help with matching
        stop_words = ['laptop', 'computer', 'pc', 'the', 'and', 'with', 'for', 'of', 'in', 'inch', '"', 'prices', 'pakistan']
        
        # Remove special characters and extra spaces
        name = re.sub(r'[^\w\s]', ' ', name)
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Remove stop words
        words = [word for word in name.split() if word not in stop_words]
        
        return ' '.join(words)
    
    def extract_key_features(self, name):
        """Extract key features like model numbers, screen sizes, etc."""
        name_lower = name.lower()
        features = {
            'brand': None,
            'model_number': None,
            'screen_size': None,
            'processor': None,
            'special_features': []
        }
        
        # Extract brand
        brands = ['hp', 'dell', 'lenovo', 'asus', 'acer', 'msi', 'apple', 'samsung']
        for brand in brands:
            if brand in name_lower:
                features['brand'] = brand
                break
        
        # Extract model numbers (like pavilion 15, inspiron 14, victus 15, etc.)
        import re
        model_pattern = r'(pavilion|inspiron|thinkpad|vivobook|aspire|victus|latitude|precision|ideapad|legion|zenbook|tuf|rog)\s*(\d+)'
        model_match = re.search(model_pattern, name_lower)
        if model_match:
            features['model_number'] = f"{model_match.group(1)} {model_match.group(2)}"
        
        # Extract screen size - improved to handle model numbers
        size_pattern = r'(\d+\.?\d*)\s*inch|\b(\d+)\s*"|\b(\d+)\s*in\b|(\d{2})(?=\s|$|[^\d])'
        size_match = re.search(size_pattern, name_lower)
        if size_match:
            # Extract the size, prioritizing specific patterns
            size = size_match.group(1) or size_match.group(2) or size_match.group(3) or size_match.group(4)
            # Only consider as screen size if it's a reasonable laptop screen size (13-17 inches typically)
            if size and 13 <= float(size) <= 17:
                features['screen_size'] = size
            # Also extract from model numbers like "victus 15" or "pavilion 14"
        
        # Additional screen size extraction from model numbers
        if not features['screen_size'] and features['model_number']:
            model_size_match = re.search(r'\s(1[3-7])(?=\s|$)', features['model_number'])
            if model_size_match:
                features['screen_size'] = model_size_match.group(1)
        
        # Extract processor info
        processor_pattern = r'(core\s*i\d+|ryzen\s*\d+|celeron|pentium|m\d+)'
        processor_match = re.search(processor_pattern, name_lower)
        if processor_match:
            features['processor'] = processor_match.group(1)
        
        # Extract special features
        special_features = ['gaming', 'touch', 'convertible', '2in1', 'ultrabook', 'business']
        for feature in special_features:
            if feature in name_lower:
                features['special_features'].append(feature)
        
        return features
    
    def calculate_similarity(self, text1, text2):
        """Calculate similarity between two text strings using feature-based matching"""
        # Extract features from both products
        features1 = self.extract_key_features(text1)
        features2 = self.extract_key_features(text2)
        
        # Clean text for basic comparison
        clean_text1 = self.clean_product_name(text1)
        clean_text2 = self.clean_product_name(text2)
        
        # Use sequence matcher for basic similarity
        basic_similarity = SequenceMatcher(None, clean_text1, clean_text2).ratio()
        
        # Feature-based scoring
        feature_score = 0.0
        feature_weight = 0.0
        
        # Brand matching (very important - 30% weight)
        if features1['brand'] and features2['brand']:
            feature_weight += 0.3
            if features1['brand'] == features2['brand']:
                feature_score += 0.3
            # Penalize different brands heavily
            else:
                feature_score -= 0.2  # Negative score for different brands
        
        # Model number matching (very important - 25% weight)
        if features1['model_number'] and features2['model_number']:
            feature_weight += 0.25
            if features1['model_number'] == features2['model_number']:
                feature_score += 0.25
            # Partial model match (e.g., pavilion 15 vs pavilion 14)
            elif features1['model_number'].split()[0] == features2['model_number'].split()[0]:
                # Same series but different size - much lower score
                feature_score += 0.05
            # Different model series - negative score
            else:
                feature_score -= 0.15
        
        # Screen size matching (important - 15% weight)
        if features1['screen_size'] and features2['screen_size']:
            feature_weight += 0.15
            if features1['screen_size'] == features2['screen_size']:
                feature_score += 0.15
        
        # Processor matching (important - 15% weight)
        if features1['processor'] and features2['processor']:
            feature_weight += 0.15
            if features1['processor'] == features2['processor']:
                feature_score += 0.15
        
        # Special features matching (moderate - 15% weight)
        if features1['special_features'] or features2['special_features']:
            feature_weight += 0.15
            common_features = set(features1['special_features']).intersection(set(features2['special_features']))
            all_features = set(features1['special_features']).union(set(features2['special_features']))
            if all_features:
                feature_similarity = len(common_features) / len(all_features)
                feature_score += 0.15 * feature_similarity
        
        # Word-based similarity for remaining comparison
        words1 = set(clean_text1.split())
        words2 = set(clean_text2.split())
        
        word_similarity = 0.0
        if words1 and words2:
            common_words = words1.intersection(words2)
            word_similarity = len(common_words) / max(len(words1), len(words2))
        
        # Combine scores with weights
        if feature_weight > 0:
            # Normalize feature score
            normalized_feature_score = feature_score / feature_weight if feature_weight > 0 else 0
            # 70% feature-based, 20% word-based, 10% basic similarity
            final_similarity = (normalized_feature_score * 0.7) + (word_similarity * 0.2) + (basic_similarity * 0.1)
        else:
            # Fallback to original method if no features extracted
            final_similarity = (basic_similarity * 0.6) + (word_similarity * 0.4)
        
        return min(final_similarity, 1.0)  # Ensure score doesn't exceed 1.0
    
    def find_best_matches(self, product):
        """Find best matches for a product from competitors"""
        product_name = self.clean_product_name(product.name)
        
        # Get all competitor products
        paklap_products = CompetitorProduct.objects.filter(competitor='paklap', is_active=True)
        priceoye_products = CompetitorProduct.objects.filter(competitor='priceoye', is_active=True)
        
        best_paklap = None
        best_paklap_score = 0
        
        best_priceoye = None
        best_priceoye_score = 0
        
        # Find best PakLap match
        for competitor_product in paklap_products:
            similarity = self.calculate_similarity(product.name, competitor_product.title)
            if similarity > best_paklap_score and similarity >= self.min_confidence:
                best_paklap_score = similarity
                best_paklap = competitor_product
        
        # Find best PriceOye match
        for competitor_product in priceoye_products:
            similarity = self.calculate_similarity(product.name, competitor_product.title)
            if similarity > best_priceoye_score and similarity >= self.min_confidence:
                best_priceoye_score = similarity
                best_priceoye = competitor_product
        
        return {
            'paklap': {'product': best_paklap, 'confidence': best_paklap_score},
            'priceoye': {'product': best_priceoye, 'confidence': best_priceoye_score}
        }
    
    def compare_single_product(self, product):
        """Compare a single product with competitors"""
        # Only compare laptops, not accessories
        if product.category != 'laptop':
            return None
            
        matches = self.find_best_matches(product)
        
        # Get or create comparison object
        comparison, created = ProductComparison.objects.get_or_create(
            seller_product=product,
            defaults={}
        )
        
        # Update PakLap comparison
        if matches['paklap']['product']:
            comparison.best_paklap_match = matches['paklap']['product']
            comparison.match_confidence_paklap = matches['paklap']['confidence']
            comparison.paklap_price_difference = product.price - matches['paklap']['product'].price
        else:
            comparison.best_paklap_match = None
            comparison.match_confidence_paklap = 0.0
            comparison.paklap_price_difference = None
        
        # Update PriceOye comparison
        if matches['priceoye']['product']:
            comparison.best_priceoye_match = matches['priceoye']['product']
            comparison.match_confidence_priceoye = matches['priceoye']['confidence']
            comparison.priceoye_price_difference = product.price - matches['priceoye']['product'].price
        else:
            comparison.best_priceoye_match = None
            comparison.match_confidence_priceoye = 0.0
            comparison.priceoye_price_difference = None
        
        comparison.save()
        return comparison
    
    def compare_all_products(self, seller=None):
        """Compare all products (optionally filtered by seller)"""
        # Only compare laptops, not accessories
        products = Product.objects.filter(is_active=True, category='laptop')
        
        if seller:
            products = products.filter(seller=seller)
        
        results = []
        for product in products:
            comparison = self.compare_single_product(product)
            if comparison:  # Only add if comparison was created (laptop products)
                results.append(comparison)
        
        return results
    
    def get_price_insights(self, seller):
        """Get pricing insights for a seller"""
        comparisons = ProductComparison.objects.filter(
            seller_product__seller=seller,
            seller_product__is_active=True
        )
        
        total_products = comparisons.count()
        if total_products == 0:
            return {
                'total_products': 0,
                'competitive_count': 0,
                'overpriced_count': 0,
                'underpriced_count': 0,
                'no_match_count': 0
            }
        
        competitive_count = 0
        overpriced_count = 0
        underpriced_count = 0
        no_match_count = 0
        
        for comparison in comparisons:
            has_match = False
            
            # Check competitiveness against PakLap
            if comparison.best_paklap_match:
                has_match = True
                if comparison.paklap_price_difference < -100:
                    underpriced_count += 1
                elif comparison.paklap_price_difference > 100:
                    overpriced_count += 1
                else:
                    competitive_count += 1
            
            # Check competitiveness against PriceOye
            elif comparison.best_priceoye_match:
                has_match = True
                if comparison.priceoye_price_difference < -100:  # Seller price is 100+ less
                    underpriced_count += 1
                elif comparison.priceoye_price_difference > 100:  # Seller price is 100+ more
                    overpriced_count += 1
                else:
                    competitive_count += 1
            
            if not has_match:
                no_match_count += 1
        
        return {
            'total_products': total_products,
            'competitive_count': competitive_count,
            'overpriced_count': overpriced_count,
            'underpriced_count': underpriced_count,
            'no_match_count': no_match_count,
            'competitive_percentage': (competitive_count / total_products) * 100 if total_products > 0 else 0
        }
