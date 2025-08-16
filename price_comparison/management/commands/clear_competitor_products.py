from django.core.management.base import BaseCommand
from price_comparison.models import CompetitorProduct, ScrapingLog, PriceHistory
from django.db import transaction


class Command(BaseCommand):
    help = 'Clear all competitor products data and related records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--competitor',
            type=str,
            help='Clear data for specific competitor (paklap/priceoye)',
            choices=['paklap', 'priceoye']
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion without prompts',
        )

    def handle(self, *args, **options):
        competitor = options.get('competitor')
        confirm = options.get('confirm')
        
        # Get counts before deletion
        if competitor:
            competitor_products = CompetitorProduct.objects.filter(competitor=competitor)
            scraping_logs = ScrapingLog.objects.filter(competitor=competitor)
            price_histories = PriceHistory.objects.filter(competitor_product__competitor=competitor)
        else:
            competitor_products = CompetitorProduct.objects.all()
            scraping_logs = ScrapingLog.objects.all()
            price_histories = PriceHistory.objects.all()
        
        product_count = competitor_products.count()
        log_count = scraping_logs.count()
        history_count = price_histories.count()
        
        if product_count == 0:
            self.stdout.write(
                self.style.WARNING(f"No {'competitor' if not competitor else competitor} products found to delete.")
            )
            return

        # Show what will be deleted
        self.stdout.write("\n" + "="*50)
        self.stdout.write("🗑️  DATA DELETION SUMMARY")
        self.stdout.write("="*50)
        self.stdout.write(f"📦 Competitor Products: {product_count}")
        self.stdout.write(f"📊 Scraping Logs: {log_count}")
        self.stdout.write(f"📈 Price Histories: {history_count}")
        
        if competitor:
            self.stdout.write(f"🎯 Target Competitor: {competitor.upper()}")
        else:
            self.stdout.write("🎯 Target: ALL COMPETITORS")
        
        self.stdout.write("="*50 + "\n")

        # Confirm deletion
        if not confirm:
            confirm_input = input("⚠️  Are you sure you want to delete this data? Type 'yes' to continue: ")
            if confirm_input.lower() != 'yes':
                self.stdout.write(self.style.WARNING("❌ Operation cancelled."))
                return

        # Perform deletion with transaction
        try:
            with transaction.atomic():
                self.stdout.write("🧹 Starting deletion process...")
                
                # Delete in correct order (due to foreign key constraints)
                if history_count > 0:
                    price_histories.delete()
                    self.stdout.write(f"✅ Deleted {history_count} price history records")
                
                if product_count > 0:
                    competitor_products.delete()
                    self.stdout.write(f"✅ Deleted {product_count} competitor products")
                
                if log_count > 0:
                    scraping_logs.delete()
                    self.stdout.write(f"✅ Deleted {log_count} scraping logs")
                
                self.stdout.write("\n" + "="*50)
                self.stdout.write("✅ DELETION COMPLETED SUCCESSFULLY!")
                self.stdout.write("="*50)
                
                if competitor:
                    self.stdout.write(f"🎯 All {competitor} data has been cleared.")
                else:
                    self.stdout.write("🎯 All competitor data has been cleared.")
                
                self.stdout.write("📊 Database is ready for fresh data.")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error during deletion: {str(e)}")
            )
            raise
