from django.core.management.base import BaseCommand
from django.db import connection
from price_comparison.models import CompetitorProduct


class Command(BaseCommand):
    help = 'Verify competitor products table structure and data'

    def handle(self, *args, **options):
        # Check table structure
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='price_comparison_competitorproduct';")
            table_exists = cursor.fetchone()
            
            if table_exists:
                self.stdout.write("✅ Table 'price_comparison_competitorproduct' exists")
                
                # Get table schema
                cursor.execute("PRAGMA table_info(price_comparison_competitorproduct);")
                columns = cursor.fetchall()
                
                self.stdout.write("\n📋 TABLE STRUCTURE:")
                self.stdout.write("-" * 60)
                for col in columns:
                    col_id, name, type_, not_null, default, pk = col
                    pk_indicator = " (PK)" if pk else ""
                    null_indicator = " NOT NULL" if not_null else ""
                    self.stdout.write(f"  {name:<20} {type_:<15}{null_indicator}{pk_indicator}")
                
                # Get sample data
                cursor.execute("SELECT COUNT(*) FROM price_comparison_competitorproduct;")
                total_count = cursor.fetchone()[0]
                
                self.stdout.write(f"\n📊 TOTAL RECORDS: {total_count}")
                
                if total_count > 0:
                    # Sample records
                    cursor.execute("""
                        SELECT id, title, price, competitor, timestamp 
                        FROM price_comparison_competitorproduct 
                        ORDER BY timestamp DESC 
                        LIMIT 5
                    """)
                    sample_records = cursor.fetchall()
                    
                    self.stdout.write("\n📦 SAMPLE RECORDS:")
                    self.stdout.write("-" * 80)
                    for record in sample_records:
                        id_, title, price, competitor, timestamp = record
                        title_short = title[:40] + "..." if len(title) > 40 else title
                        self.stdout.write(f"  ID: {id_:<3} | {title_short:<43} | PKR {price:>10,.0f} | {competitor}")
                
                # Count by competitor
                cursor.execute("""
                    SELECT competitor, COUNT(*) as count 
                    FROM price_comparison_competitorproduct 
                    GROUP BY competitor
                """)
                competitor_counts = cursor.fetchall()
                
                self.stdout.write(f"\n🏪 BY COMPETITOR:")
                self.stdout.write("-" * 30)
                for comp, count in competitor_counts:
                    self.stdout.write(f"  {comp.upper():<10}: {count:>5} products")
                
            else:
                self.stdout.write("❌ Table 'price_comparison_competitorproduct' does not exist!")
                
        self.stdout.write("\n" + "="*60)
        self.stdout.write("✅ Table verification completed!")
        self.stdout.write("="*60)
