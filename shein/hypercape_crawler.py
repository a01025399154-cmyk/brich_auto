"""
Hypercape 브랜드 크롤러
브랜드 페이지 URL을 입력받아 브랜드 정보와 모든 상품 정보를 수집하여 Excel로 저장
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time
import random
import re
import json
from datetime import datetime
from urllib.parse import urljoin, urlparse
from pathlib import Path
import hypercape_config as config


class HypercapeCrawler:
    """Hypercape 브랜드 크롤러"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(config.HEADERS)
        
    def _delay(self):
        """요청 간 랜덤 딜레이"""
        time.sleep(random.uniform(config.DELAY_MIN, config.DELAY_MAX))
        
    def _get_page(self, url, retries=0):
        """페이지 가져오기 (재시도 포함)"""
        try:
            self._delay()
            response = self.session.get(url, timeout=config.TIMEOUT)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            if retries < config.MAX_RETRIES:
                print(f"⚠️  요청 실패, 재시도 중... ({retries + 1}/{config.MAX_RETRIES}): {url}")
                time.sleep(2 ** retries)  # 지수 백오프
                return self._get_page(url, retries + 1)
            else:
                print(f"❌ 요청 실패: {url} - {str(e)}")
                return None
                
    def extract_brand_info(self, brand_url):
        """브랜드 정보 추출"""
        print(f"\n📋 브랜드 정보 수집 중: {brand_url}")
        
        response = self._get_page(brand_url)
        if not response:
            return None
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 브랜드 ID 추출 (URL에서)
        brand_id = brand_url.rstrip('/').split('/')[-1]
        
        # 브랜드명은 나중에 상품에서 추출 (일단 임시값)
        brand_name = f"Brand_{brand_id}"
        
        # 브랜드 설명 추출 시도
        description = ""
        for elem in soup.find_all(string=re.compile(r'As a .* brand', re.I)):
            text = elem.strip()
            if len(text) > 20:  # 충분히 긴 설명
                description = text
                break
        
        # 브랜드 이미지 URL 추출
        brand_image_url = ""
        # 큰 이미지 찾기 (브랜드 로고)
        images = soup.find_all('img')
        for img in images:
            src = img.get('src', '')
            if src and ('brand' in src.lower() or 'logo' in src.lower()):
                brand_image_url = src
                if not brand_image_url.startswith('http'):
                    brand_image_url = urljoin(config.BASE_URL, brand_image_url)
                break
        
        # 이미지를 못 찾았으면 첫 번째 큰 이미지
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
            'brand_name': brand_name,  # 나중에 업데이트됨
            'brand_description': description,
            'brand_image_url': brand_image_url,
            'total_products': 0,
            'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f"✅ 브랜드 정보 수집 완료: {brand_name} (상품에서 정확한 이름 추출 예정)")
        return brand_data
        
    def get_product_list_url(self, brand_id):
        """상품 목록 페이지 URL 가져오기"""
        # 브랜드 ID로 직접 상품 목록 URL 구성
        # 패턴: /goods?brand={brand_id}
        product_list_url = f"{config.BASE_URL}/goods?brand={brand_id}"
        print(f"  → 상품 목록 URL: {product_list_url}")
        return product_list_url
        
    def get_product_links(self, product_list_url):
        """상품 목록에서 모든 상품 링크 수집"""
        print(f"\n🔍 상품 목록 수집 중: {product_list_url}")
        
        response = self._get_page(product_list_url)
        if not response:
            return []
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        product_links = []
        
        # 상품 링크 찾기 - 여러 패턴 시도
        # 패턴 1: /goods/{id} 형태의 링크
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
        
        response = self._get_page(product_url)
        if not response:
            return None
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 상품 ID 추출
        product_id = product_url.rstrip('/').split('/')[-1]
        
        # 상품명 추출
        product_name = soup.find('h1')
        if not product_name:
            product_name = soup.find('div', class_=re.compile(r'product.*name', re.I))
        product_name = product_name.get_text(strip=True) if product_name else "Unknown"
        
        # 가격 정보 추출
        price = ""
        original_price = ""
        
        # 가격 찾기
        price_elem = soup.find('span', class_=re.compile(r'price', re.I))
        if not price_elem:
            price_elem = soup.find('div', class_=re.compile(r'price', re.I))
        
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            # $14.00 $28.00 형태에서 추출
            prices = re.findall(r'\$[\d.]+', price_text)
            if len(prices) >= 2:
                price = prices[0]
                original_price = prices[1]
            elif len(prices) == 1:
                price = prices[0]
        
        # 할인율 계산
        discount_rate = ""
        if price and original_price:
            try:
                p = float(price.replace('$', ''))
                op = float(original_price.replace('$', ''))
                if op > 0:
                    discount_rate = f"{int((1 - p/op) * 100)}%"
            except:
                pass
        
        # 옵션 정보 추출
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
        
        # 상품 설명 추출
        description = ""
        desc_section = soup.find('div', string=re.compile(r'Description', re.I))
        if desc_section:
            desc_parent = desc_section.find_next_sibling()
            if desc_parent:
                description = desc_parent.get_text(strip=True)
        
        # Details 섹션도 확인
        if not description:
            details = soup.find('div', class_=re.compile(r'details', re.I))
            if details:
                description = details.get_text(strip=True)
        
        # 사용법 추출
        how_to_use = ""
        how_section = soup.find('div', string=re.compile(r'How to use', re.I))
        if how_section:
            how_parent = how_section.find_next_sibling()
            if how_parent:
                how_to_use = how_parent.get_text(strip=True)
        
        # 성분 정보 추출
        ingredients = ""
        ing_section = soup.find('div', string=re.compile(r'Ingredients', re.I))
        if ing_section:
            ing_parent = ing_section.find_next_sibling()
            if ing_parent:
                ingredients = ing_parent.get_text(strip=True)
        
        # 이미지 URL 추출
        main_image_url = ""
        detail_images_urls = []
        
        # 메인 이미지
        main_img = soup.find('img', alt=re.compile(product_name[:20], re.I))
        if not main_img:
            # 큰 이미지 찾기
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
        
        # 모든 상품 이미지 수집
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
        
        # 디렉토리 생성
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        # DataFrame 생성
        brand_df = pd.DataFrame([brand_data])
        products_df = pd.DataFrame(products_data)
        
        # Excel 저장
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            brand_df.to_excel(writer, sheet_name='Brand', index=False)
            products_df.to_excel(writer, sheet_name='Products', index=False)
        
        print(f"✅ Excel 파일 저장 완료: {output_path}")
        
    def crawl_brand(self, brand_url):
        """브랜드 전체 크롤링"""
        print("="*80)
        print("🚀 Hypercape 브랜드 크롤러 시작")
        print("="*80)
        
        # 1. 브랜드 정보 추출
        brand_data = self.extract_brand_info(brand_url)
        if not brand_data:
            print("❌ 브랜드 정보를 가져올 수 없습니다.")
            return
        
        brand_name = brand_data['brand_name']
        brand_id = brand_data['brand_id']
        
        # 2. 상품 목록 URL 가져오기
        product_list_url = self.get_product_list_url(brand_id)
        if not product_list_url:
            print("❌ 상품 목록 URL을 찾을 수 없습니다.")
            return
        
        # 3. 상품 링크 수집
        product_links = self.get_product_links(product_list_url)
        if not product_links:
            print("❌ 상품을 찾을 수 없습니다.")
            return
        
        brand_data['total_products'] = len(product_links)
        
        # 4. 각 상품 정보 수집
        products_data = []
        for i, product_url in enumerate(product_links, 1):
            print(f"\n[{i}/{len(product_links)}]")
            product_data = self.extract_product_details(product_url)
            if product_data:
                # 첫 번째 상품에서 브랜드명 추출
                if i == 1 and product_data['product_name']:
                    # "[BIOHEAL BOH] Product Name" 형태에서 브랜드명 추출
                    match = re.match(r'\[([^\]]+)\]', product_data['product_name'])
                    if match:
                        actual_brand_name = match.group(1)
                        brand_data['brand_name'] = actual_brand_name
                        brand_name = actual_brand_name
                        print(f"  ✅ 브랜드명 업데이트: {brand_name}")
                
                product_data['brand_name'] = brand_name
                products_data.append(product_data)
        
        # 5. Excel 저장
        output_filename = f"{brand_name}_products.xlsx"
        output_path = os.path.join(config.OUTPUT_DIR, output_filename)
        self.save_to_excel(brand_data, products_data, output_path)
        
        print("\n" + "="*80)
        print("✨ 크롤링 완료!")
        print(f"📊 브랜드: {brand_name}")
        print(f"📦 상품 수: {len(products_data)}")
        print(f"💾 저장 위치: {output_path}")
        print("="*80)
        
        return output_path


def main():
    """메인 함수"""
    import sys
    
    if len(sys.argv) < 2:
        print("사용법: python hypercape_crawler.py <브랜드_URL>")
        print("예시: python hypercape_crawler.py https://biz.hypercape.com/brands/149")
        sys.exit(1)
    
    brand_url = sys.argv[1]
    
    crawler = HypercapeCrawler()
    crawler.crawl_brand(brand_url)


if __name__ == "__main__":
    main()
