"""
LONDON WHOLESALE SCRAPER v4.0 - FINAL VERSION
==============================================
Fixed Pack Price and Pack Qty extraction
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import re
from datetime import datetime

class LondonWholesaleScraper:
    def __init__(self, headless=False):
        print("="*70)
        print("LONDON WHOLESALE SCRAPER v4.0 - FINAL")
        print("="*70)
        
        self.base_url = "https://www.londonwholesales.com"
        self.all_products = []
        self.headless = headless
        self.driver = None
        
    def setup_driver(self):
        print("\n[1/6] Setting up Chrome browser...")
        
        from selenium.webdriver.chrome.options import Options
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✅ Browser ready!")
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def get_categories(self):
        print("\n[2/6] Fetching categories...")
        
        try:
            self.driver.get(f"{self.base_url}/default.php")
            time.sleep(5)
            
            categories = []
            category_elements = self.driver.find_elements(By.XPATH, 
                "//a[contains(@href, 'MainCategoryID=')]")
            
            for element in category_elements:
                try:
                    category_name = element.text.strip()
                    category_href = element.get_attribute('href')
                    match = re.search(r'MainCategoryID=(\d+)', category_href)
                    
                    if match and category_name:
                        categories.append({
                            'name': category_name,
                            'id': match.group(1),
                            'element': element
                        })
                except:
                    continue
            
            print(f"✅ Found {len(categories)} categories")
            return categories
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return []
    
    def click_category(self, category):
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", category['element'])
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", category['element'])
            time.sleep(8)
            
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "textarea"))
                )
            except:
                pass
            
            return True
        except Exception as e:
            print(f"  ⚠️  Error: {e}")
            return False
    
    def extract_pack_info(self, parent_table):
        """
        Improved Pack Qty and Pack Price extraction
        Uses multiple strategies to find the data
        """
        pack_qty = ''
        pack_price = ''
        
        # STRATEGY 1: Find by text content and get next sibling
        try:
            # Get all table cells
            all_cells = parent_table.find_elements(By.TAG_NAME, "td")
            
            for i, cell in enumerate(all_cells):
                cell_text = cell.text.strip()
                
                # Check for Pack Qty
                if "Pack Qty" in cell_text and not pack_qty:
                    # Look in next few cells
                    for j in range(i+1, min(i+4, len(all_cells))):
                        next_text = all_cells[j].text.strip()
                        # Check if it's a number
                        if next_text and next_text.replace('.', '').isdigit():
                            pack_qty = next_text
                            break
                
                # Check for Pack Price
                if "Pack Price" in cell_text and not pack_price:
                    # Look in next few cells
                    for j in range(i+1, min(i+4, len(all_cells))):
                        next_text = all_cells[j].text.strip()
                        # Check if it contains £ or is a price
                        if '£' in next_text or (next_text and re.match(r'[\d.]+', next_text)):
                            pack_price = next_text
                            # Add £ if missing
                            if '£' not in pack_price:
                                pack_price = f'£{pack_price}'
                            break
        except:
            pass
        
        # STRATEGY 2: Use XPath with class="textBlue"
        if not pack_qty:
            try:
                qty_elements = parent_table.find_elements(By.XPATH,
                    ".//tr[.//td[contains(text(), 'Pack Qty')]]/td[@class='textBlue']")
                if qty_elements:
                    pack_qty = qty_elements[0].text.strip()
            except:
                pass
        
        if not pack_price:
            try:
                price_elements = parent_table.find_elements(By.XPATH,
                    ".//tr[.//td[contains(text(), 'Pack Price')]]/td[@class='textBlue']")
                if price_elements:
                    pack_price = price_elements[0].text.strip()
                    if '£' not in pack_price:
                        pack_price = f'£{pack_price}'
            except:
                pass
        
        # STRATEGY 3: Parse from entire table HTML
        if not pack_qty or not pack_price:
            try:
                table_html = parent_table.get_attribute('innerHTML')
                
                if not pack_qty:
                    qty_match = re.search(r'Pack Qty.*?textBlue["\']>(\d+)<', table_html, re.IGNORECASE | re.DOTALL)
                    if qty_match:
                        pack_qty = qty_match.group(1)
                
                if not pack_price:
                    price_match = re.search(r'Pack Price.*?textBlue["\']>£?\s*([\d.]+)<', table_html, re.IGNORECASE | re.DOTALL)
                    if price_match:
                        pack_price = f'£{price_match.group(1)}'
            except:
                pass
        
        return pack_qty, pack_price
    
    def scrape_products_on_page(self, category_name):
        products = []
        
        try:
            textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
            
            print(f"  Found {len(textareas)} products")
            
            for idx, textarea in enumerate(textareas):
                try:
                    product = {}
                    
                    # Product name
                    product_name = textarea.get_attribute('value').strip()
                    if not product_name:
                        product_name = textarea.text.strip()
                    
                    if not product_name:
                        continue
                    
                    product['Product_Name'] = product_name
                    
                    # Find parent table
                    parent_table = textarea.find_element(By.XPATH, 
                        "./ancestor::table[contains(@width, '100%')]")
                    
                    # Product ID
                    try:
                        product_id_elem = parent_table.find_element(By.XPATH, 
                            ".//font[contains(@style, 'color') and contains(@style, '#1F86DE')]")
                        product['Product_ID'] = product_id_elem.text.strip()
                    except:
                        try:
                            product_id_elem = parent_table.find_element(By.XPATH, 
                                ".//b[contains(text(), 'LW')]")
                            product['Product_ID'] = product_id_elem.text.strip()
                        except:
                            product['Product_ID'] = ''
                    
                    # Pack Qty and Pack Price - IMPROVED EXTRACTION
                    pack_qty, pack_price = self.extract_pack_info(parent_table)
                    product['Pack_Qty'] = pack_qty
                    product['Pack_Price'] = pack_price
                    
                    # Image URL
                    try:
                        img = parent_table.find_element(By.TAG_NAME, "img")
                        src = img.get_attribute('src')
                        if src and 'nopicture' not in src.lower():
                            product['Image_URL'] = src if src.startswith('http') else f"{self.base_url}/{src}"
                        else:
                            product['Image_URL'] = ''
                    except:
                        product['Image_URL'] = ''
                    
                    product['Category'] = category_name
                    
                    # Calculate unit price
                    if product.get('Pack_Price') and product.get('Pack_Qty'):
                        try:
                            price_str = product['Pack_Price'].replace('£', '').replace(',', '').replace('&nbsp;', '').strip()
                            qty_str = product['Pack_Qty'].strip()
                            
                            price = float(price_str)
                            qty = int(float(qty_str))
                            
                            if qty > 0:
                                product['Unit_Price'] = f"£{price/qty:.2f}"
                            else:
                                product['Unit_Price'] = ''
                        except:
                            product['Unit_Price'] = ''
                    else:
                        product['Unit_Price'] = ''
                    
                    products.append(product)
                    
                    # Show first 3 products for verification
                    if idx < 3:
                        print(f"    → {product['Product_ID']}: {product['Product_Name'][:30]}... | Qty: {product['Pack_Qty']} | Price: {product['Pack_Price']}")
                    
                except Exception as e:
                    continue
            
            return products
            
        except Exception as e:
            print(f"  ⚠️  Error: {e}")
            return []
    
    def get_total_pages(self):
        try:
            page_links = self.driver.find_elements(By.XPATH, 
                "//a[contains(@href, 'page=')]")
            
            max_page = 1
            for link in page_links:
                text = link.text.strip()
                if text.isdigit():
                    max_page = max(max_page, int(text))
            
            return max_page
        except:
            return 1
    
    def navigate_to_page(self, page_num):
        try:
            page_link = self.driver.find_element(By.XPATH, f"//a[text()='{page_num}']")
            self.driver.execute_script("arguments[0].click();", page_link)
            time.sleep(8)
            return True
        except:
            return False
    
    def scrape_category(self, category, category_num, total_categories):
        print(f"\n[{category_num}/{total_categories}] {category['name']}")
        
        if not self.click_category(category):
            print("  ❌ Failed to load")
            return
        
        total_pages = self.get_total_pages()
        if total_pages > 1:
            print(f"  📄 {total_pages} pages")
        
        # Page 1
        print(f"  Page 1:")
        products = self.scrape_products_on_page(category['name'])
        print(f"  ✅ {len(products)} products extracted")
        
        self.all_products.extend(products)
        
        # Additional pages (limit to 15 per category)
        for page_num in range(2, min(total_pages + 1, 16)):
            print(f"  Page {page_num}:")
            if self.navigate_to_page(page_num):
                page_products = self.scrape_products_on_page(category['name'])
                print(f"  ✅ {len(page_products)} products")
                self.all_products.extend(page_products)
            else:
                print("  ⚠️  Skipped")
    
    def save_to_excel(self, filename='London_Wholesale_Complete.xlsx'):
        print(f"\n[5/6] Saving to Excel...")
        
        if not self.all_products:
            print("❌ No products!")
            return None
        
        df = pd.DataFrame(self.all_products)
        
        column_order = ['Product_ID', 'Product_Name', 'Category', 'Pack_Qty', 
                       'Pack_Price', 'Unit_Price', 'Image_URL']
        existing_cols = [col for col in column_order if col in df.columns]
        df = df[existing_cols]
        
        df.to_excel(filename, index=False)
        
        print(f"✅ Saved {len(df)} products")
        
        # Show data quality stats
        print(f"\n📊 DATA QUALITY:")
        print(f"   Products with Pack Qty: {df['Pack_Qty'].notna().sum()} ({df['Pack_Qty'].notna().sum()/len(df)*100:.1f}%)")
        print(f"   Products with Pack Price: {df['Pack_Price'].notna().sum()} ({df['Pack_Price'].notna().sum()/len(df)*100:.1f}%)")
        print(f"   Products with Product ID: {df['Product_ID'].notna().sum()} ({df['Product_ID'].notna().sum()/len(df)*100:.1f}%)")
        
        print(f"\n📦 SUMMARY:")
        print(f"   Total products: {len(df)}")
        print(f"   Categories: {df['Category'].nunique()}")
        print(f"\n📈 Top 10 categories:")
        print(df['Category'].value_counts().head(10).to_string())
        
        return filename
    
    def run(self, max_categories=None):
        start_time = datetime.now()
        
        try:
            if not self.setup_driver():
                return
            
            categories = self.get_categories()
            if not categories:
                return
            
            if max_categories:
                categories = categories[:max_categories]
                print(f"\n⚠️  Test mode: {max_categories} categories")
            
            print(f"\n[3/6] Scraping {len(categories)} categories...")
            
            for i, category in enumerate(categories, 1):
                self.scrape_category(category, i, len(categories))
                
                if i % 10 == 0:
                    print(f"\n  📊 Progress: {i}/{len(categories)} | {len(self.all_products)} products so far\n")
            
            filename = self.save_to_excel()
            
            elapsed = datetime.now() - start_time
            print(f"\n[6/6] ✅ SCRAPING COMPLETE!")
            print(f"   Time: {elapsed}")
            if filename:
                print(f"   File: {filename}")
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            if self.all_products:
                print("   Saving progress...")
                self.save_to_excel()
        
        except Exception as e:
            print(f"\n❌ Error: {e}")
            if self.all_products:
                print("   Saving progress...")
                self.save_to_excel()
        
        finally:
            if self.driver:
                print("\n🔒 Closing browser...")
                self.driver.quit()
                print("✅ Done!")


def main():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║     LONDON WHOLESALE SCRAPER v4.0 - FINAL VERSION             ║
║                                                               ║
║  ✅ Product names                                             ║
║  ✅ Product IDs                                               ║
║  ✅ Pack Qty (FIXED!)                                         ║
║  ✅ Pack Price (FIXED!)                                       ║
║  ✅ Unit Price (auto-calculated)                              ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

CHOOSE MODE:
------------
1. Test mode (3 categories) - Recommended first!
2. Full scrape (all categories) - 1-3 hours

Enter choice (1 or 2): """)
    
    choice = input().strip()
    
    scraper = LondonWholesaleScraper(headless=False)
    
    if choice == "1":
        print("\n🔬 Running test mode (3 categories)...\n")
        scraper.run(max_categories=3)
    else:
        print("\n🚀 Running full scrape (all categories)...\n")
        scraper.run(max_categories=None)


if __name__ == "__main__":
    main()
