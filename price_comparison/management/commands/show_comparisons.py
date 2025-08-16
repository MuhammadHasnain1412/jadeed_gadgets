from django.core.management.base import BaseCommand
from price_comparison.models import ProductComparison, CompetitorProduct
from products.models import Product
from accounts.models import User


class Command(BaseCommand):
    help = 'Show detailed price comparison results'

    def add_arguments(self, parser):
        parser.add_argument(
            '--seller-id',
            type=int,
            help='Show comparisons for specific seller only'
        )
        parser.add_argument(
            '--show-details',
            action='store_true',
            help='Show detailed matching information'
        )
        parser.add_argument(
            '--competitor',
            type=str,
            choices=['paklap', 'priceoye', 'both'],
            default='both',
            help='Show matches for specific competitor'
        )

    def handle(self, *args, **options):
        seller_id = options.get('seller_id')
        show_details = options.get('show_details')
        competitor = options.get('competitor')
        
        # Get comparisons
        comparisons = ProductComparison.objects.select_related(
            'seller_product', 'best_paklap_match', 'best_priceoye_match'
        ).filter(seller_product__is_active=True)
        
        if seller_id:
            comparisons = comparisons.filter(seller_product__seller_id=seller_id)
        
        total_comparisons = comparisons.count()
        
        if total_comparisons == 0:
            self.stdout.write(self.style.WARNING("❌ No comparisons found."))
            return
        
        self.stdout.write("\n" + "="*80)
        self.stdout.write("📊 PRODUCT PRICE COMPARISON RESULTS")
        self.stdout.write("="*80)
        
        # Summary statistics
        paklap_matches = comparisons.filter(best_paklap_match__isnull=False).count()
        priceoye_matches = comparisons.filter(best_priceoye_match__isnull=False).count()
        both_matches = comparisons.filter(
            best_paklap_match__isnull=False,
            best_priceoye_match__isnull=False
        ).count()
        no_matches = comparisons.filter(
            best_paklap_match__isnull=True,
            best_priceoye_match__isnull=True
        ).count()
        
        self.stdout.write(f"📦 Total Products: {total_comparisons}")
        self.stdout.write(f"🔵 PakLap Matches: {paklap_matches} ({paklap_matches/total_comparisons*100:.1f}%)")
        self.stdout.write(f"🟡 PriceOye Matches: {priceoye_matches} ({priceoye_matches/total_comparisons*100:.1f}%)")
        self.stdout.write(f"✅ Both Matched: {both_matches} ({both_matches/total_comparisons*100:.1f}%)")
        self.stdout.write(f"❌ No Matches: {no_matches} ({no_matches/total_comparisons*100:.1f}%)")
        
        self.stdout.write("\n" + "-"*80)
        self.stdout.write("📋 DETAILED COMPARISON RESULTS")
        self.stdout.write("-"*80)
        
        for i, comparison in enumerate(comparisons.order_by('seller_product__name'), 1):
            product = comparison.seller_product
            
            self.stdout.write(f"\n{i:2d}. 📱 {product.name}")
            self.stdout.write(f"    💰 Your Price: PKR {product.price:,.0f}")
            self.stdout.write(f"    🏪 Seller: {product.seller.business_name if product.seller.business_name else product.seller.username}")
            
            # PakLap comparison
            if competitor in ['paklap', 'both'] and comparison.best_paklap_match:
                match = comparison.best_paklap_match
                confidence = comparison.match_confidence_paklap
                price_diff = comparison.paklap_price_difference
                
                self.stdout.write(f"    🔵 PakLap Match: {match.title[:50]}{'...' if len(match.title) > 50 else ''}")
                self.stdout.write(f"       💵 PakLap Price: PKR {match.price:,.0f}")
                self.stdout.write(f"       🎯 Confidence: {confidence:.2f}")
                
                if price_diff > 0:
                    self.stdout.write(f"       📈 Your price is PKR {price_diff:,.0f} HIGHER")
                elif price_diff < 0:
                    self.stdout.write(f"       📉 Your price is PKR {abs(price_diff):,.0f} LOWER")
                else:
                    self.stdout.write(f"       ⚖️ Same price")
                
                if show_details:
                    self.stdout.write(f"       🔗 PakLap URL: {match.url}")
            elif competitor in ['paklap', 'both']:
                self.stdout.write(f"    🔵 PakLap: ❌ No match found")
            
            # PriceOye comparison
            if competitor in ['priceoye', 'both'] and comparison.best_priceoye_match:
                match = comparison.best_priceoye_match
                confidence = comparison.match_confidence_priceoye
                price_diff = comparison.priceoye_price_difference
                
                self.stdout.write(f"    🟡 PriceOye Match: {match.title[:50]}{'...' if len(match.title) > 50 else ''}")
                self.stdout.write(f"       💵 PriceOye Price: PKR {match.price:,.0f}")
                self.stdout.write(f"       🎯 Confidence: {confidence:.2f}")
                
                if price_diff > 0:
                    self.stdout.write(f"       📈 Your price is PKR {price_diff:,.0f} HIGHER")
                elif price_diff < 0:
                    self.stdout.write(f"       📉 Your price is PKR {abs(price_diff):,.0f} LOWER")
                else:
                    self.stdout.write(f"       ⚖️ Same price")
                
                if show_details:
                    self.stdout.write(f"       🔗 PriceOye URL: {match.url}")
            elif competitor in ['priceoye', 'both']:
                self.stdout.write(f"    🟡 PriceOye: ❌ No match found")
            
            # Competitive analysis
            if comparison.best_paklap_match or comparison.best_priceoye_match:
                best_competitor_price = None
                best_competitor_name = None
                
                if comparison.best_paklap_match and comparison.best_priceoye_match:
                    if comparison.best_paklap_match.price < comparison.best_priceoye_match.price:
                        best_competitor_price = comparison.best_paklap_match.price
                        best_competitor_name = "PakLap"
                    else:
                        best_competitor_price = comparison.best_priceoye_match.price
                        best_competitor_name = "PriceOye"
                elif comparison.best_paklap_match:
                    best_competitor_price = comparison.best_paklap_match.price
                    best_competitor_name = "PakLap"
                elif comparison.best_priceoye_match:
                    best_competitor_price = comparison.best_priceoye_match.price
                    best_competitor_name = "PriceOye"
                
                if best_competitor_price:
                    difference = product.price - best_competitor_price
                    if difference > 100:
                        self.stdout.write(f"    ⚠️  OVERPRICED by PKR {difference:,.0f} (vs {best_competitor_name})")
                    elif difference < -100:
                        self.stdout.write(f"    💡 UNDERPRICED by PKR {abs(difference):,.0f} (vs {best_competitor_name})")
                    else:
                        self.stdout.write(f"    ✅ COMPETITIVE pricing (vs {best_competitor_name})")
        
        # Price insights
        self.stdout.write("\n" + "="*80)
        self.stdout.write("💡 PRICING INSIGHTS")
        self.stdout.write("="*80)
        
        overpriced = 0
        underpriced = 0
        competitive = 0
        
        for comparison in comparisons:
            best_price = None
            if comparison.best_paklap_match and comparison.best_priceoye_match:
                best_price = min(comparison.best_paklap_match.price, comparison.best_priceoye_match.price)
            elif comparison.best_paklap_match:
                best_price = comparison.best_paklap_match.price
            elif comparison.best_priceoye_match:
                best_price = comparison.best_priceoye_match.price
            
            if best_price:
                difference = comparison.seller_product.price - best_price
                if difference > 100:
                    overpriced += 1
                elif difference < -100:
                    underpriced += 1
                else:
                    competitive += 1
        
        self.stdout.write(f"📈 Overpriced Products: {overpriced} ({overpriced/total_comparisons*100:.1f}%)")
        self.stdout.write(f"📉 Underpriced Products: {underpriced} ({underpriced/total_comparisons*100:.1f}%)")
        self.stdout.write(f"✅ Competitively Priced: {competitive} ({competitive/total_comparisons*100:.1f}%)")
        self.stdout.write(f"❓ No Competitor Data: {no_matches} ({no_matches/total_comparisons*100:.1f}%)")
        
        self.stdout.write("\n🎯 Recommendation: Focus on repricing overpriced items and maintaining competitive pricing.")
        self.stdout.write("="*80)
