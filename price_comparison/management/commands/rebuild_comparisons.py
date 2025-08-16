from django.core.management.base import BaseCommand
from price_comparison.services import PriceComparisonService
from price_comparison.models import ProductComparison, CompetitorProduct
from products.models import Product
from django.db import transaction


class Command(BaseCommand):
    help = 'Rebuild all product comparisons with fresh competitor data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--seller-id',
            type=int,
            help='Rebuild comparisons for specific seller only'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing comparisons before rebuilding'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )

    def handle(self, *args, **options):
        seller_id = options.get('seller_id')
        clear_existing = options.get('clear_existing')
        dry_run = options.get('dry_run')
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write("🔄 REBUILDING PRODUCT COMPARISONS")
        self.stdout.write("="*60)
        
        # Initialize comparison service
        comparison_service = PriceComparisonService()
        
        # Get products to compare
        products = Product.objects.filter(is_active=True, category='laptop')
        if seller_id:
            products = products.filter(seller_id=seller_id)
            
        total_products = products.count()
        
        if total_products == 0:
            self.stdout.write(self.style.WARNING("❌ No laptop products found to compare."))
            return
        
        # Check competitor data availability
        paklap_count = CompetitorProduct.objects.filter(competitor='paklap', is_active=True).count()
        priceoye_count = CompetitorProduct.objects.filter(competitor='priceoye', is_active=True).count()
        
        self.stdout.write(f"📦 Products to compare: {total_products}")
        self.stdout.write(f"🏪 PakLap competitors: {paklap_count}")
        self.stdout.write(f"🏪 PriceOye competitors: {priceoye_count}")
        
        if paklap_count == 0 and priceoye_count == 0:
            self.stdout.write(self.style.WARNING("⚠️ No competitor data found. Please run scrapers first."))
            return
        
        # Clear existing comparisons if requested
        if clear_existing:
            existing_count = ProductComparison.objects.count()
            if not dry_run:
                ProductComparison.objects.all().delete()
                self.stdout.write(f"🧹 Cleared {existing_count} existing comparisons")
            else:
                self.stdout.write(f"🧹 Would clear {existing_count} existing comparisons")
        
        if dry_run:
            self.stdout.write("\n🔍 DRY RUN MODE - No changes will be made")
            self.stdout.write(f"Would process {total_products} products...")
            return
        
        self.stdout.write(f"\n🚀 Starting comparison process...")
        
        # Process products
        processed = 0
        matched_paklap = 0
        matched_priceoye = 0
        matched_both = 0
        no_matches = 0
        
        try:
            with transaction.atomic():
                for i, product in enumerate(products, 1):
                    self.stdout.write(f"📱 [{i:3d}/{total_products}] Processing: {product.name[:40]}...")
                    
                    # Run comparison
                    comparison = comparison_service.compare_single_product(product)
                    
                    if comparison:
                        processed += 1
                        
                        # Count matches
                        has_paklap = comparison.best_paklap_match is not None
                        has_priceoye = comparison.best_priceoye_match is not None
                        
                        if has_paklap and has_priceoye:
                            matched_both += 1
                            self.stdout.write(f"   ✅ Matched both (PakLap: {comparison.match_confidence_paklap:.2f}, PriceOye: {comparison.match_confidence_priceoye:.2f})")
                        elif has_paklap:
                            matched_paklap += 1
                            self.stdout.write(f"   🔵 Matched PakLap only (confidence: {comparison.match_confidence_paklap:.2f})")
                        elif has_priceoye:
                            matched_priceoye += 1
                            self.stdout.write(f"   🟡 Matched PriceOye only (confidence: {comparison.match_confidence_priceoye:.2f})")
                        else:
                            no_matches += 1
                            self.stdout.write("   ❌ No matches found")
                        
                        # Show price differences if available
                        if has_paklap:
                            diff = comparison.paklap_price_difference
                            if diff > 0:
                                self.stdout.write(f"      💰 PakLap: Your price PKR {diff:,.0f} higher")
                            elif diff < 0:
                                self.stdout.write(f"      💰 PakLap: Your price PKR {abs(diff):,.0f} lower")
                            else:
                                self.stdout.write(f"      💰 PakLap: Same price")
                        
                        if has_priceoye:
                            diff = comparison.priceoye_price_difference
                            if diff > 0:
                                self.stdout.write(f"      💰 PriceOye: Your price PKR {diff:,.0f} higher")
                            elif diff < 0:
                                self.stdout.write(f"      💰 PriceOye: Your price PKR {abs(diff):,.0f} lower")
                            else:
                                self.stdout.write(f"      💰 PriceOye: Same price")
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error during processing: {str(e)}"))
            raise
        
        # Display final results
        self.stdout.write("\n" + "="*60)
        self.stdout.write("✅ COMPARISON REBUILD COMPLETED!")
        self.stdout.write("="*60)
        self.stdout.write(f"📊 SUMMARY:")
        self.stdout.write(f"   • Total Products Processed: {processed}")
        self.stdout.write(f"   • Matched Both Competitors: {matched_both}")
        self.stdout.write(f"   • Matched PakLap Only: {matched_paklap}")
        self.stdout.write(f"   • Matched PriceOye Only: {matched_priceoye}")
        self.stdout.write(f"   • No Matches Found: {no_matches}")
        
        # Calculate percentages
        if processed > 0:
            both_pct = (matched_both / processed) * 100
            paklap_pct = ((matched_paklap + matched_both) / processed) * 100
            priceoye_pct = ((matched_priceoye + matched_both) / processed) * 100
            no_match_pct = (no_matches / processed) * 100
            
            self.stdout.write(f"\n📈 MATCH RATES:")
            self.stdout.write(f"   • Both Competitors: {both_pct:.1f}%")
            self.stdout.write(f"   • PakLap Total: {paklap_pct:.1f}%")
            self.stdout.write(f"   • PriceOye Total: {priceoye_pct:.1f}%")
            self.stdout.write(f"   • No Matches: {no_match_pct:.1f}%")
        
        self.stdout.write("\n🎉 All product comparisons have been rebuilt!")
        self.stdout.write("="*60)
