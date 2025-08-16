from django.core.management.base import BaseCommand
from price_comparison.models import CompetitorProduct, ScrapingLog, PriceHistory
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import time
from bs4 import BeautifulSoup
from decimal import Decimal
import traceback
import re
import datetime


class Command(BaseCommand):
    help = 'Scrapes laptop products from PriceOye'

    def handle(self, *args, **options):
        # Create scraping log
        log = ScrapingLog.objects.create(
            competitor='priceoye',
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
            chrome_options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

            # Initialize WebDriver
            self.stdout.write("🚀 Starting WebDriver...")
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.stdout.write("✅ WebDriver initialized")

            try:
                # Navigate to PriceOye laptops page
                url = "https://priceoye.pk/laptops/"
                self.stdout.write(f"🌐 Navigating to {url}")
                driver.get(url)
                
                # Wait for initial products to load
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.productBox.b-productBox")))
                    self.stdout.write("✅ Initial products loaded")
                except TimeoutException:
                    self.stdout.write("⚠️ Initial products didn't load within timeout")
                
                # Scroll to load all products (infinite scroll)
                last_count = 0
                same_count_repeats = 0
                max_repeats = 5
                max_scroll_attempts = 50
                scroll_attempts = 0

                self.stdout.write("📜 Scrolling to load all products...")
                
                while same_count_repeats < max_repeats and scroll_attempts < max_scroll_attempts:
                    scroll_attempts += 1
                    
                    # Scroll to last visible product
                    products = driver.find_elements(By.CSS_SELECTOR, "div.productBox.b-productBox")
                    if products:
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'end'});", products[-1])
                    
                    # Wait for new content to potentially load
                    time.sleep(2)
                    
                    # Check if new products loaded
                    new_products = driver.find_elements(By.CSS_SELECTOR, "div.productBox.b-productBox")
                    current_count = len(new_products)
                    self.stdout.write(f"📦 Loaded {current_count} products so far...")
                    
                    if current_count == last_count:
                        same_count_repeats += 1
                    else:
                        same_count_repeats = 0
                        last_count = current_count
                
                self.stdout.write(f"🔍 Final product count: {last_count}")

                # Parse final page with BeautifulSoup
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                product_divs = soup.select("div.productBox.b-productBox")
                
                self.stdout.write(f"📦 Found {len(product_divs)} products to process")
                
                new_count = 0
                updated_count = 0
                
                for div in product_divs:
                    try:
                        a_tag = div.find("a", class_="ga-dataset")
                        if not a_tag:
                            continue
                            
                        # Extract title
                        title_div = a_tag.find("div", class_="p-title")
                        if not title_div:
                            continue
                        title = title_div.get_text(strip=True)
                        
                        # Extract link
                        link = a_tag['href']
                        if not link.startswith('http'):
                            link = f"https://priceoye.pk{link}"
                        
                        # Extract price
                        price_box = a_tag.find("div", class_="price-box")
                        if not price_box:
                            continue
                        price_text = price_box.get_text(strip=True)
                        price_clean = re.sub(r"[^\d]", "", price_text) or "0"
                        
                        if not price_clean.isdigit() or int(price_clean) == 0:
                            continue
                        
                        # Extract image
                        img_tag = a_tag.find("img")
                        image = img_tag['src'] if img_tag and 'src' in img_tag.attrs else ""
                        
                        try:
                            price = Decimal(price_clean)
                        except:
                            self.stdout.write(f"⚠️ Could not parse price: {price_text}")
                            continue
                        
                        # Create or update product
                        competitor_product, created = CompetitorProduct.objects.update_or_create(
                            title=title,
                            competitor='priceoye',
                            defaults={
                                'price': price,
                                'url': link,
                                'is_active': True
                            }
                        )
                        
                        if created:
                            new_count += 1
                        else:
                            # Check if price changed
                            if competitor_product.price != price:
                                updated_count += 1
                        
                        log.products_scraped += 1
                        
                    except Exception as e:
                        self.stdout.write(f"⚠️ Error processing product: {str(e)}")
                        continue
                
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
