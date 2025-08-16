from django.core.management.base import BaseCommand
from django.core.management import call_command
from price_comparison.services import PriceComparisonService


class Command(BaseCommand):
    help = 'Run all competitor scrapers and update price comparisons'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-scraping',
            action='store_true',
            help='Skip scraping and only update comparisons',
        )

    def handle(self, *args, **options):
        self.stdout.write("🚀 Starting comprehensive price comparison update...")
        
        if not options['skip_scraping']:
            # Run PakLap scraper
            self.stdout.write("📊 Scraping PakLap...")
            try:
                call_command('scrape_paklap')
                self.stdout.write("✅ PakLap scraping completed")
            except Exception as e:
                self.stdout.write(f"❌ PakLap scraping failed: {e}")
            
            # Run PriceOye scraper
            self.stdout.write("📊 Scraping PriceOye...")
            try:
                call_command('scrape_priceoye')
                self.stdout.write("✅ PriceOye scraping completed")
            except Exception as e:
                self.stdout.write(f"❌ PriceOye scraping failed: {e}")
        
        # Update all price comparisons
        self.stdout.write("🔄 Updating price comparisons...")
        try:
            comparison_service = PriceComparisonService()
            results = comparison_service.compare_all_products()
            self.stdout.write(f"✅ Updated {len(results)} product comparisons")
        except Exception as e:
            self.stdout.write(f"❌ Price comparison update failed: {e}")
        
        self.stdout.write("🎉 All tasks completed!")
