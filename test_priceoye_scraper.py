#!/usr/bin/env python3
"""
Test script to verify PriceOye scraper functionality
Run this to test if the PriceOye scraper is working correctly
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jadeed_gadgets.settings')
django.setup()

from django.core.management import call_command

def test_priceoye_scraper():
    """Test the PriceOye scraper"""
    print("🧪 Testing PriceOye Scraper")
    print("=" * 50)
    
    try:
        # Run the PriceOye scraper
        print("🚀 Running PriceOye scraper...")
        call_command('scrape_priceoye')
        print("✅ PriceOye scraper completed successfully!")
        
        # Check the results
        from price_comparison.models import CompetitorProduct, ScrapingLog
        
        priceoye_products = CompetitorProduct.objects.filter(competitor='priceoye', is_active=True)
        recent_log = ScrapingLog.objects.filter(competitor='priceoye').order_by('-started_at').first()
        
        print(f"\n📊 Results:")
        print(f"   • Total PriceOye products: {priceoye_products.count()}")
        if recent_log:
            print(f"   • Last scraping status: {recent_log.status}")
            print(f"   • Products scraped: {recent_log.products_scraped}")
            print(f"   • New products: {recent_log.new_products}")
            print(f"   • Updated products: {recent_log.updated_products}")
        
        # Show some sample products
        print(f"\n📦 Sample Products:")
        for i, product in enumerate(priceoye_products[:5], 1):
            print(f"   {i}. {product.title[:60]}{'...' if len(product.title) > 60 else ''}")
            print(f"      Price: PKR {product.price:,}")
            print(f"      URL: {product.url}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing PriceOye scraper: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_paklap_scraper():
    """Test the PakLap scraper"""
    print("\n🧪 Testing PakLap Scraper")
    print("=" * 50)
    
    try:
        # Run the PakLap scraper
        print("🚀 Running PakLap scraper...")
        call_command('scrape_paklap')
        print("✅ PakLap scraper completed successfully!")
        
        # Check the results
        from price_comparison.models import CompetitorProduct, ScrapingLog
        
        paklap_products = CompetitorProduct.objects.filter(competitor='paklap', is_active=True)
        recent_log = ScrapingLog.objects.filter(competitor='paklap').order_by('-started_at').first()
        
        print(f"\n📊 Results:")
        print(f"   • Total PakLap products: {paklap_products.count()}")
        if recent_log:
            print(f"   • Last scraping status: {recent_log.status}")
            print(f"   • Products scraped: {recent_log.products_scraped}")
            print(f"   • New products: {recent_log.new_products}")
            print(f"   • Updated products: {recent_log.updated_products}")
        
        # Show some sample products
        print(f"\n📦 Sample Products:")
        for i, product in enumerate(paklap_products[:5], 1):
            print(f"   {i}. {product.title[:60]}{'...' if len(product.title) > 60 else ''}")
            print(f"      Price: PKR {product.price:,}")
            print(f"      URL: {product.url}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing PakLap scraper: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_price_comparison():
    """Test the price comparison functionality"""
    print("\n🧪 Testing Price Comparison Service")
    print("=" * 50)
    
    try:
        from price_comparison.services import PriceComparisonService
        from products.models import Product
        
        service = PriceComparisonService()
        
        # Get a sample product to test with
        product = Product.objects.filter(is_active=True).first()
        if not product:
            print("⚠️ No active products found to test comparison")
            return False
        
        print(f"🔍 Testing comparison for: {product.name}")
        
        # Test the comparison
        comparison = service.compare_single_product(product)
        
        print(f"\n📊 Comparison Results:")
        print(f"   • Product: {product.name}")
        print(f"   • Your Price: PKR {product.price:,}")
        
        if comparison.best_paklap_match:
            print(f"   • PakLap Match: {comparison.best_paklap_match.title}")
            print(f"   • PakLap Price: PKR {comparison.best_paklap_match.price:,}")
            print(f"   • PakLap Confidence: {comparison.match_confidence_paklap:.2f}")
            print(f"   • Price Difference: PKR {comparison.paklap_price_difference:,}")
        else:
            print(f"   • No PakLap match found")
        
        if comparison.best_priceoye_match:
            print(f"   • PriceOye Match: {comparison.best_priceoye_match.title}")
            print(f"   • PriceOye Price: PKR {comparison.best_priceoye_match.price:,}")
            print(f"   • PriceOye Confidence: {comparison.match_confidence_priceoye:.2f}")
            print(f"   • Price Difference: PKR {comparison.priceoye_price_difference:,}")
        else:
            print(f"   • No PriceOye match found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing price comparison: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Scraper Test Suite")
    print("This will test the new PriceOye scraper and updated PakLap scraper")
    print()
    
    # Test scrapers
    priceoye_success = test_priceoye_scraper()
    paklap_success = test_paklap_scraper()
    comparison_success = test_price_comparison()
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 Test Summary:")
    print(f"   • PriceOye Scraper: {'✅ PASS' if priceoye_success else '❌ FAIL'}")
    print(f"   • PakLap Scraper: {'✅ PASS' if paklap_success else '❌ FAIL'}")
    print(f"   • Price Comparison: {'✅ PASS' if comparison_success else '❌ FAIL'}")
    
    if all([priceoye_success, paklap_success, comparison_success]):
        print("\n🎉 All tests passed! Your scrapers are working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please check the error messages above.")
    
    print("\n💡 You can now use these commands:")
    print("   • python manage.py scrape_priceoye")
    print("   • python manage.py scrape_paklap") 
    print("   • python manage.py run_all_scrapers")
