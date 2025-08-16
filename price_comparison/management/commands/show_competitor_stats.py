from django.core.management.base import BaseCommand
from price_comparison.models import CompetitorProduct, ScrapingLog
from django.db.models import Count, Min, Max, Avg


class Command(BaseCommand):
    help = 'Show statistics for competitor products'

    def add_arguments(self, parser):
        parser.add_argument(
            '--competitor',
            type=str,
            help='Show stats for specific competitor (paklap/priceoye)',
            choices=['paklap', 'priceoye']
        )
        parser.add_argument(
            '--sample',
            type=int,
            default=10,
            help='Number of sample products to show'
        )

    def handle(self, *args, **options):
        competitor = options.get('competitor')
        sample_count = options.get('sample', 10)
        
        # Filter by competitor if specified
        if competitor:
            products = CompetitorProduct.objects.filter(competitor=competitor)
            logs = ScrapingLog.objects.filter(competitor=competitor)
            title = f"{competitor.upper()} COMPETITOR PRODUCTS"
        else:
            products = CompetitorProduct.objects.all()
            logs = ScrapingLog.objects.all()
            title = "ALL COMPETITOR PRODUCTS"
        
        # Get statistics
        total_count = products.count()
        
        if total_count == 0:
            self.stdout.write(
                self.style.WARNING(f"No products found for {competitor or 'any competitor'}.")
            )
            return
        
        stats = products.aggregate(
            min_price=Min('price'),
            max_price=Max('price'),
            avg_price=Avg('price')
        )
        
        # Get competitor breakdown
        competitor_breakdown = products.values('competitor').annotate(
            count=Count('id')
        ).order_by('competitor')
        
        # Get recent scraping logs
        recent_logs = logs.order_by('-started_at')[:5]
        
        # Display results
        self.stdout.write("\n" + "="*60)
        self.stdout.write(f"📊 {title} STATISTICS")
        self.stdout.write("="*60)
        
        # Overall stats
        self.stdout.write(f"📦 Total Products: {total_count:,}")
        self.stdout.write(f"💰 Price Range: PKR {stats['min_price']:,.0f} - PKR {stats['max_price']:,.0f}")
        self.stdout.write(f"📈 Average Price: PKR {stats['avg_price']:,.0f}")
        
        # Competitor breakdown
        if not competitor:
            self.stdout.write("\n🏪 COMPETITOR BREAKDOWN:")
            for comp in competitor_breakdown:
                self.stdout.write(f"   • {comp['competitor'].upper()}: {comp['count']:,} products")
        
        # Recent scraping logs
        self.stdout.write(f"\n📋 RECENT SCRAPING LOGS:")
        for log in recent_logs:
            status_emoji = "✅" if log.status == 'completed' else "❌" if log.status == 'failed' else "⏳"
            self.stdout.write(
                f"   {status_emoji} {log.competitor.upper()} - {log.started_at.strftime('%Y-%m-%d %H:%M')} "
                f"({log.products_scraped} products)"
            )
        
        # Sample products
        self.stdout.write(f"\n📦 SAMPLE PRODUCTS (Latest {sample_count}):")
        sample_products = products.order_by('-timestamp')[:sample_count]
        
        for i, product in enumerate(sample_products, 1):
            self.stdout.write(
                f"   {i:2d}. {product.title[:50]}{'...' if len(product.title) > 50 else ''}"
            )
            self.stdout.write(f"       💰 PKR {product.price:,.0f} | 🏪 {product.competitor.upper()}")
            self.stdout.write(f"       ⏰ {product.timestamp.strftime('%Y-%m-%d %H:%M')}")
            self.stdout.write("")
        
        self.stdout.write("="*60)
        self.stdout.write("✅ Statistics display completed!")
        self.stdout.write("="*60)
