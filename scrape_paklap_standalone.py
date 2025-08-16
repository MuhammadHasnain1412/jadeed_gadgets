import datetime
import time
import re
from decimal import Decimal
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup


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


def scrape_paklap_laptops():
    """Scrape laptops from PakLap.pk with pagination handling and improved functionality"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Add user agent to avoid detection
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    base_url = "https://www.paklap.pk/laptops-prices.html"
    driver.get(base_url)

    all_products = []
    page_count = 1
    max_pages = 20  # Increased limit to handle more pages

    try:
        while page_count <= max_pages:
            print(f"📄 Scraping page {page_count}...")
            
            # Wait for products to load
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".product-item-details"))
            )
            
            # Scroll to load all products with limited attempts
            last_height = driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            max_scroll_attempts = 3  # Limited scroll attempts for efficiency
            
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
                    
                    # Only add products with valid titles and prices
                    if title != "N/A" and title.strip() and numeric_value > 0:
                        all_products.append({
                            'Title': title,
                            'Raw_Title': raw_title,  # Keep original for reference
                            'Price (PKR)': clean_price,  # Now includes 'Rs.' and no decimals
                            'Price_Numeric': numeric_value,  # Numeric value for calculations
                            'URL': url,
                            'Image': image,
                            'Timestamp': datetime.datetime.now()
                        })
                        
                except Exception as e:
                    print(f"⚠️ Error processing product: {e}")
                    continue

            print(f"📦 Found {len(products)} products on page {page_count}")

            # Check for next page - improved next button detection
            try:
                # Try the primary selector first
                next_button = driver.find_element(By.CSS_SELECTOR, 'a.action.next')
                
                # Check if next button is disabled
                if 'disabled' in next_button.get_attribute('class'):
                    print("✅ Reached last page (next button disabled)")
                    break

                print("➡️ Moving to next page...")
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
                        print("➡️ Moving to next page (alternative selector)...")
                        driver.execute_script("arguments[0].click();", next_button)
                        page_count += 1
                        
                        # Wait for page to load
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".product-item-details"))
                        )
                        time.sleep(2)
                    else:
                        print("⛔ Next button not clickable")
                        break
                except NoSuchElementException:
                    print("⛔ No more pages found")
                    break
            except Exception as e:
                print(f"⛔ Error navigating to next page: {e}")
                break

    except Exception as e:
        print(f"⛔ Error during scraping: {e}")
    finally:
        driver.quit()

    # Remove duplicates based on title and price
    unique_products = []
    seen_combinations = set()
    
    for product in all_products:
        # Create a unique key based on normalized title and price
        unique_key = (product['Title'].lower(), product['Price_Numeric'])
        
        if unique_key not in seen_combinations:
            seen_combinations.add(unique_key)
            unique_products.append(product)

    print(f"✅ Scraped {len(unique_products)} unique products from paklap.pk (removed {len(all_products) - len(unique_products)} duplicates)")
    return unique_products


# Test the function with some debug output
if __name__ == "__main__":
    products = scrape_paklap_laptops()
    
    # Show some examples of title normalization
    print("\n📋 Sample products:")
    for i, product in enumerate(products[:10]):
        print(f"{i+1}. Title: {product['Title']}")
        print(f"   Price: {product['Price (PKR)']} (Numeric: PKR {product['Price_Numeric']:,})")
        print(f"   URL: {product['URL']}")
        print()
    
    # Save to CSV for analysis
    try:
        import pandas as pd
        df = pd.DataFrame(products)
        filename = f"paklap_laptops_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        print(f"💾 Data saved to {filename}")
    except ImportError:
        print("⚠️ pandas not installed, skipping CSV export")
