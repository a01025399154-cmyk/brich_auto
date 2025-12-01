"""
Hypercape 브랜드 크롤러 (Selenium 버전)
브랜드 페이지 URL을 입력받아 브랜드 정보와 모든 상품 정보를 수집하여 Excel로 저장
JavaScript 렌더링 페이지 지원
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import json
from datetime import datetime
from urllib.parse import urljoin
import hypercape_config as config


class HypercapeSeleniumCrawler:
    """Hypercape 브랜드 크롤러 (Selenium 버전)"""
    
    def __init__(self, headless=True):
        """
        Args:
            headless: True면 브라우저 창을 숨김, False면 브라우저 창 표시
        """
        self.headless = headless
        self.driver = None
        
    def _init_driver(self):
        """Chrome 드라이버 초기화"""
        print("🌐 브라우저 초기화 중...")
        
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(f'user-agent={config.HEADERS["User-Agent"]}')
        
        # 자동으로 ChromeDriver 다운로드 및 설정
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
        print("✅ 브라우저 준비 완료")
        
    def _close_driver(self):
        """브라우저 종료"""
        if self.driver:
            self.driver.quit()
            print("🔚 브라우저 종료")
            
    def _wait_and_get_page_source(self, url, wait_seconds=3):
        """페이지 로드 후 소스 가져오기"""
        self.driver.get(url)
        time.sleep(wait_seconds)  # JavaScript 실행 대기
        return self.driver.page_source
        
    def extract_brand_info(self, brand_url):
        """브랜드 정보 추출"""
        print(f"\n📋 브랜드 정보 수집 중: {brand_url}")
        
        page_source = self._wait_and_get_page_source(brand_url)
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # 브랜드 ID 추출
        brand_id = brand_url.rstrip('/').split('/')[-1]
        
        # 브랜드명은 나중에 상품에서 추출
        brand_name = f"Brand_{brand_id}"
        
        # 브랜드 설명 추출
        description = ""
        for elem in soup.find_all(string=re.compile(r'As a .* brand', re.I)):
            text = elem.strip()
            if len(text) > 20:
                description = text
                break
        
        # 브랜드 이미지 URL 추출
        brand_image_url = ""
        images = soup.find_all('img')
        for img in images:
            src = img.get('src', '')
            if src and ('brand' in src.lower() or 'logo' in src.lower()):
                brand_image_url = src
                if not brand_image_url.startswith('http'):
                    brand_image_url = urljoin(config.BASE_URL, brand_image_url)
                break
        
        if not brand_image_url:
            for img in images:
                src = img.get('src', '')
                if src and 'icon' not in src.lower() and 'favicon' not in src.lower():
                    brand_image_url = src
                    if not brand_image_url.startswith('http'):
                        brand_image_url = urljoin(config.BASE_URL, brand_image_url)
                    break
        
        brand_data = {
            'brand_id': brand_id,
            'brand_name': brand_name,
            'brand_description': description,
            'brand_image_url': brand_image_url,
            'product_list_url': '',  # 상품 목록 URL 추가
            'total_products': 0,
            'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # "show products" 링크 찾기
        try:
            show_products = soup.find('a', href=re.compile(r'goods\?brand=', re.I))
            if show_products:
                href = show_products.get('href')
                if href:
                    brand_data['product_list_url'] = urljoin(config.BASE_URL, href)
                    print(f"  → 상품 목록 URL 발견: {brand_data['product_list_url']}")
        except Exception as e:
            print(f"  ⚠️ 상품 목록 URL 찾기 실패: {str(e)}")
            
        # 못 찾았으면 기본값 (하지만 정확하지 않을 수 있음)
        if not brand_data['product_list_url']:
             # brand_id가 아니라 brand_name을 사용해야 함 (하지만 brand_name을 아직 모를 수 있음)
             # 일단 brand_id로 시도하되 경고 출력
             brand_data['product_list_url'] = f"{config.BASE_URL}/goods?brand={brand_id}"
             print(f"  ⚠️ 상품 목록 URL을 찾지 못해 기본값 사용: {brand_data['product_list_url']}")
        
        print(f"✅ 브랜드 정보 수집 완료 (상품에서 정확한 브랜드명 추출 예정)")
        return brand_data
        
    def get_product_links(self, product_list_url):
        """상품 목록 페이지에서 상품 링크 수집"""
        print(f"\n🔍 상품 목록 수집 중: {product_list_url}")
        
        page_source = self._wait_and_get_page_source(product_list_url, wait_seconds=5)
        soup = BeautifulSoup(page_source, 'html.parser')
        
        product_links = []
        for link in soup.find_all('a', href=re.compile(r'/goods/\d+')):
            href = link.get('href')
            full_url = urljoin(config.BASE_URL, href)
            if full_url not in product_links:
                product_links.append(full_url)
        
        print(f"✅ 상품 {len(product_links)}개 발견")
        return product_links
        
    def extract_product_details(self, product_url):
        """상품 상세 정보 추출"""
        print(f"  📦 상품 정보 수집 중: {product_url}")
        
        page_source = self._wait_and_get_page_source(product_url, wait_seconds=3)
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # 상품 ID
        product_id = product_url.rstrip('/').split('/')[-1]
        
        # 상품명 추출 (수정됨)
        product_name = "Unknown"
        name_elem = soup.select_one('h4#name')
        if not name_elem:
            name_elem = soup.select_one('h4.pro-desc')
        if not name_elem:
            name_elem = soup.select_one('h1')
            
        if name_elem:
            product_name = name_elem.get_text(strip=True)
        
        # 가격 정보 추출 (수정됨)
        price = ""
        original_price = ""
        
        # 현재 가격
        price_elem = soup.select_one('span#price')
        if price_elem:
            price = price_elem.get_text(strip=True)
            
        # 정가 (할인 전 가격)
        org_price_elem = soup.select_one('span#compareAtPrice')
        if org_price_elem:
            original_price = org_price_elem.get_text(strip=True)
            
        # 만약 위 선택자로 못 찾으면 기존 방식 시도
        if not price:
            price_elem = soup.find('span', class_=re.compile(r'price', re.I))
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                prices = re.findall(r'\$[\d.]+', price_text)
                if len(prices) >= 1:
                    price = prices[0]
        
        # 할인율
        discount_rate = ""
        if price and original_price:
            try:
                p = float(price.replace('$', '').replace(',', ''))
                op = float(original_price.replace('$', '').replace(',', ''))
                if op > 0:
                    discount_rate = f"{int((1 - p/op) * 100)}%"
            except:
                pass
        
        # 옵션
        options = []
        option_section = soup.find('div', string=re.compile(r'Option', re.I))
        if option_section:
            option_parent = option_section.find_parent()
            if option_parent:
                option_items = option_parent.find_all(['button', 'div', 'span'])
                for item in option_items:
                    text = item.get_text(strip=True)
                    if text and text != 'Option':
                        options.append(text)
        
        options_str = ", ".join(options) if options else ""
        
        # 상품 설명, 사용법, 성분 분리 추출
        description = ""
        how_to_use = ""
        ingredients = ""
        
        desc_elem = soup.select_one('div#description')
        if desc_elem:
            current_section = "description" # 기본 섹션
            
            # 자식 요소들을 순회하며 처리
            for child in desc_elem.children:
                if child.name in ['h2', 'h4']:
                    header_text = child.get_text(strip=True).lower()
                    if 'ingredients' in header_text:
                        current_section = "ingredients"
                    elif 'how to use' in header_text:
                        current_section = "how_to_use"
                    elif 'details' in header_text:
                        current_section = "description"
                    else:
                        # [important] 같은 기타 헤더는 설명에 포함
                        if current_section == "description":
                            description += f"\n\n[{child.get_text(strip=True)}]"
                            
                elif child.name == 'pre':
                    text = child.get_text(strip=True)
                    if current_section == "ingredients":
                        ingredients += text + "\n"
                    elif current_section == "how_to_use":
                        how_to_use += text + "\n"
                    else:
                        description += text + "\n"
                        
            # 앞뒤 공백 제거
            description = description.strip()
            how_to_use = how_to_use.strip()
            ingredients = ingredients.strip()
        
        # 만약 위 방식으로 추출되지 않았다면 기존 방식 시도 (백업)
        if not description and not how_to_use and not ingredients:
            desc_section = soup.find('div', string=re.compile(r'Description', re.I))
            if desc_section:
                desc_parent = desc_section.find_next_sibling()
                if desc_parent:
                    description = desc_parent.get_text(strip=True)
        
        # 이미지 URL 추출
        main_image_url = ""
        detail_images_urls = []
        
        # 메인 이미지
        main_img = soup.find('img', alt=re.compile(product_name[:20], re.I))
        if not main_img:
            images = soup.find_all('img')
            for img in images:
                src = img.get('src', '')
                if src and 'product' in src.lower():
                    main_img = img
                    break
        
        if main_img:
            main_image_url = main_img.get('src', '')
            if main_image_url and not main_image_url.startswith('http'):
                main_image_url = urljoin(config.BASE_URL, main_image_url)
        
        # 모든 상품 이미지
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src and ('product' in src.lower() or 'goods' in src.lower() or 'image' in src.lower()):
                if not src.startswith('http'):
                    src = urljoin(config.BASE_URL, src)
                if src not in detail_images_urls and src != main_image_url:
                    detail_images_urls.append(src)
        
        product_data = {
            'product_id': product_id,
            'product_name': product_name,
            'price': price,
            'original_price': original_price,
            'discount_rate': discount_rate,
            'options': options_str,
            'description': description,
            'how_to_use': how_to_use,
            'ingredients': ingredients,
            'main_image_url': main_image_url,
            'detail_images_urls': json.dumps(detail_images_urls),
            'product_url': product_url
        }
        
        print(f"  ✅ 상품 정보 수집 완료: {product_name[:50]}")
        return product_data
        
    def save_to_excel(self, brand_data, products_data, output_path):
        """Excel 파일로 저장"""
        print(f"\n💾 Excel 파일 저장 중: {output_path}")
        
        import os
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        brand_df = pd.DataFrame([brand_data])
        products_df = pd.DataFrame(products_data)
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            brand_df.to_excel(writer, sheet_name='Brand', index=False)
            products_df.to_excel(writer, sheet_name='Products', index=False)
        
        print(f"✅ Excel 파일 저장 완료: {output_path}")
        
    def crawl_brand(self, brand_url):
        """브랜드 전체 크롤링"""
        print("="*80)
        print("🚀 Hypercape 브랜드 크롤러 시작 (Selenium)")
        print("="*80)
        
        try:
            # 브라우저 초기화
            self._init_driver()
            
            # 1. 브랜드 정보 추출
            brand_data = self.extract_brand_info(brand_url)
            if not brand_data:
                print("❌ 브랜드 정보를 가져올 수 없습니다.")
                return
            
            brand_name = brand_data['brand_name']
            brand_id = brand_data['brand_id']
            product_list_url = brand_data['product_list_url']
            
            # 2. 상품 링크 수집
            product_links = self.get_product_links(product_list_url)
            if not product_links:
                print("❌ 상품을 찾을 수 없습니다.")
                return
            
            brand_data['total_products'] = len(product_links)
            
            # 3. 각 상품 정보 수집
            products_data = []
            for i, product_url in enumerate(product_links, 1):
                print(f"\n[{i}/{len(product_links)}]")
                product_data = self.extract_product_details(product_url)
                if product_data:
                    # 첫 번째 상품에서 브랜드명 추출
                    if i == 1 and product_data['product_name']:
                        match = re.match(r'\[([^\]]+)\]', product_data['product_name'])
                        if match:
                            actual_brand_name = match.group(1)
                            brand_data['brand_name'] = actual_brand_name
                            brand_name = actual_brand_name
                            print(f"  ✅ 브랜드명 업데이트: {brand_name}")
                    
                    product_data['brand_name'] = brand_name
                    products_data.append(product_data)
            
            # 4. Excel 저장
            output_filename = f"{brand_name}_products.xlsx"
            output_path = f"{config.OUTPUT_DIR}/{output_filename}"
            self.save_to_excel(brand_data, products_data, output_path)
            
            print("\n" + "="*80)
            print("✨ 크롤링 완료!")
            print(f"📊 브랜드: {brand_name}")
            print(f"📦 상품 수: {len(products_data)}")
            print(f"💾 저장 위치: {output_path}")
            print("="*80)
            
            return output_path
            
        finally:
            # 브라우저 종료
            self._close_driver()


def main():
    """메인 함수"""
    import sys
    
    brand_url = ""
    
    # 명령행 인자가 있으면 사용
    if len(sys.argv) >= 2:
        brand_url = sys.argv[1]
    # 없으면 사용자 입력 받기
    else:
        print("크롤링할 브랜드 URL을 입력해주세요.")
        print("예시: https://biz.hypercape.com/brands/149")
        try:
            brand_url = input("URL 입력: ").strip()
        except KeyboardInterrupt:
            print("\n취소되었습니다.")
            sys.exit(0)
            
    if not brand_url:
        print("URL이 입력되지 않았습니다.")
        sys.exit(1)
    
    # headless=False로 설정하면 브라우저 창이 보입니다 (디버깅용)
    crawler = HypercapeSeleniumCrawler(headless=True)
    crawler.crawl_brand(brand_url)


if __name__ == "__main__":
    main()
