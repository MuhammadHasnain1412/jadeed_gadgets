from django.core.management.base import BaseCommand
from price_comparison.models import CompetitorProduct, ScrapingLog, PriceHistory
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
import time
from bs4 import BeautifulSoup
from decimal import Decimal
import traceback
import re
import datetime


def normalize_product_title(title):
    """Normalize product title for better matching"""
    if not title:
        return ""
    
    # Remove extra whitespace and normalize
    title = re.sub(r'\s+', ' ', title.strip())
    
    # Remove common prefixes/suffixes that don't help with matching
    title = re.sub(r'\b(price in pakistan|prices pakistan|laptop)\b', '', title, flags=re.IGNORECASE)
    
    # Clean up model numbers (ensure proper spacing)
    title = re.sub(r'([a-zA-Z]+)(\d+)', r'\1 \2', title)
    
    # Remove excessive punctuation
    title = re.sub(r'[^\w\s\-\.\"]', ' ', title)
    
    # Clean up extra spaces again
    title = re.sub(r'\s+', ' ', title.strip())
    
    return title


class Command(BaseCommand):
    help = 'Scrapes laptop products from PakLap'

    def handle(self, *args, **options):
        # Create scraping log
        log = ScrapingLog.objects.create(
            competitor='paklap',
            status='started'
        )
        
        try:
            # Setup Chrome options
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

            # Initialize WebDriver
            self.stdout.write("🚀 Starting WebDriver...")
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.stdout.write("✅ WebDriver initialized")

            try:
                # Use the correct PakLap URL
                base_url = "https://www.paklap.pk/laptops-prices.html"
                self.stdout.write(f"🌐 Navigating to {base_url}")
                driver.get(base_url)

                page_count = 1
                max_pages = 20  # Increased limit to handle more pages
                new_count = 0
                updated_count = 0

                while page_count <= max_pages:
                    self.stdout.write(f"📄 Scraping page {page_count}...")

                    # Wait for products to load
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".product-item-details"))
                    )

                    # Scroll to load all products with limited attempts
                    last_height = driver.execute_script("return document.body.scrollHeight")
                    scroll_attempts = 0
                    max_scroll_attempts = 3  # Reduced for efficiency
                    
                    while scroll_attempts < max_scroll_attempts:
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(1.5)
                        new_height = driver.execute_script("return document.body.scrollHeight")
                        if new_height == last_height:
                            break
                        last_height = new_height
                        scroll_attempts += 1

                    # Parse page with BeautifulSoup
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    products = soup.select('.product-item-details')
                    
                    self.stdout.write(f"📦 Found {len(products)} products on page {page_count}")

                    for product in products:
                        try:
                            title_tag = product.select_one('.product-item-link')
                            raw_title = title_tag.text.strip() if title_tag else "N/A"
                            
                            # Normalize the title for better matching
                            title = normalize_product_title(raw_title)

                            price_tag = product.select_one('.price')
                            price_text = price_tag.text.strip() if price_tag else "N/A"
                            
                            # Process price text to keep currency symbol and remove decimals
                            if price_text != "N/A":
                                # Remove commas and fractional part (e.g., '.00')
                                clean_price = price_text.replace(',', '').replace('.00', '')
                                # Extract numeric digits for validation
                                num_str = ''.join(filter(str.isdigit, clean_price))
                                numeric_value = int(num_str) if num_str else 0
                            else:
                                clean_price = "N/A"
                                numeric_value = 0
                            
                            url_tag = product.select_one('.product-item-link')
                            url = url_tag['href'] if url_tag and 'href' in url_tag.attrs else "N/A"
                            
                            # Make URL absolute if needed
                            if url != "N/A" and not url.startswith('http'):
                                url = f"https://www.paklap.pk{url}" if url.startswith('/') else f"https://www.paklap.pk/{url}"
                            
                            # Find image in the product card
                            product_card = product.find_previous(class_='product-item-info')
                            img_tag = product_card.select_one('img.product-image-photo') if product_card else None
                            image = img_tag['src'] if img_tag and 'src' in img_tag.attrs else ""
                            
                            # Only process products with valid titles and prices
                            if title != "N/A" and title.strip() and numeric_value > 0:
                                try:
                                    # Create or update product
                                    competitor_product, created = CompetitorProduct.objects.update_or_create(
                                        title=title,
                                        competitor='paklap',
                                        defaults={
                                            'price': numeric_value,
                                            'url': url,
                                            'is_active': True
                                        }
                                    )
                                    
                                    if created:
                                        new_count += 1
                                        self.stdout.write(f"➕ New product: {title[:50]}... - PKR {numeric_value:,}")
                                    else:
                                        # Check if price changed
                                        if competitor_product.price != numeric_value:
                                            updated_count += 1
                                            self.stdout.write(f"🔄 Updated price: {title[:50]}... - PKR {competitor_product.price:,} → PKR {numeric_value:,}")
                                    
                                    log.products_scraped += 1
                                    
                                except Exception as e:
                                    self.stdout.write(f"⚠️ Error saving product '{title[:50]}...': {e}")
                                    continue
                                        
                        except Exception as e:
                            self.stdout.write(f"⚠️ Error processing product: {e}")
                            continue

                    # Check for next page - improved next button detection
                    try:
                        # Try the primary selector first
                        next_button = driver.find_element(By.CSS_SELECTOR, 'a.action.next')
                        
                        # Check if next button is disabled
                        if 'disabled' in next_button.get_attribute('class'):
                            self.stdout.write("✅ Reached last page (next button disabled)")
                            break

                        self.stdout.write("➡️ Moving to next page...")
                        driver.execute_script("arguments[0].click();", next_button)  # Use JS click to avoid interception
                        page_count += 1
                        
                        # Wait for page to load
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".product-item-details"))
                        )
                        time.sleep(2)  # Additional stability wait

                    except NoSuchElementException:
                        # Try alternative selector if first fails
                        try:
                            next_button = driver.find_element(By.CSS_SELECTOR, 'li.pages-item-next a')
                            if next_button.get_attribute('aria-label') == 'Next':
                                self.stdout.write("➡️ Moving to next page (alternative selector)...")
                                driver.execute_script("arguments[0].click();", next_button)
                                page_count += 1
                                
                                # Wait for page to load
                                WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, ".product-item-details"))
                                )
                                time.sleep(2)
                            else:
                                self.stdout.write("⛔ Next button not clickable")
                                break
                        except NoSuchElementException:
                            self.stdout.write("⛔ No more pages found")
                            break
                    except Exception as e:
                        self.stdout.write(f"⛔ Error navigating to next page: {e}")
                        break
                
                # Update log
                log.new_products = new_count
                log.updated_products = updated_count
                log.mark_completed()
                
                self.stdout.write(f"✅ Scraping completed!")
                self.stdout.write(f"📊 New products: {new_count}")
                self.stdout.write(f"📊 Updated products: {updated_count}")
                self.stdout.write(f"📊 Total processed: {log.products_scraped}")
                
            finally:
                driver.quit()
                self.stdout.write("✅ WebDriver closed")
                
        except Exception as e:
            error_message = f"Fatal error: {str(e)}\n{traceback.format_exc()}"
            self.stdout.write(f"❌ {error_message}")
            log.mark_failed(error_message)
            raise
