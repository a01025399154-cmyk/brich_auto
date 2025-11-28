# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- 사용자 설정 ---
# 비플로우 로그인 정보
BFLOW_ID = "a01025399154@brich.co.kr"
BFLOW_PW = "2rlqmadl@!"

# 구글 시트 설정
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1bnPfUjWhqNMxAosG7qktbWGl-UpJ6lzXcGEYouYx4RM/edit?gid=1366209122#gid=1366209122"
SHEET_NAME = "2.0 마스터상품"
CREDENTIALS_PATH = r"C:\Users\a0102\OneDrive\Desktop\cursor\credentials\inner-sale-979c1e8ed412.json"

def setup_driver():
    """Chrome 웹 드라이버를 설정하고 반환합니다."""
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--remote-debugging-port=9222")
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # 페이지 로드 타임아웃 설정
    driver.set_page_load_timeout(60)
    driver.implicitly_wait(10)
    
    return driver

def authenticate_google_sheets():
    """구글 시트에 인증하고 클라이언트를 반환합니다."""
    try:
        # 서비스 계정 인증
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        credentials = Credentials.from_service_account_file(
            CREDENTIALS_PATH, 
            scopes=scope
        )
        
        client = gspread.authorize(credentials)
        
        # 스프레드시트 열기
        spreadsheet = client.open_by_url(GOOGLE_SHEET_URL)
        worksheet = spreadsheet.worksheet(SHEET_NAME)
        
        print(f"✅ 구글 시트 연결 성공: {SHEET_NAME}")
        return worksheet
        
    except Exception as e:
        print(f"❌ 구글 시트 연결 실패: {e}")
        return None

def update_google_sheet_with_results(worksheet, creation_results):
    """상품 생성 결과를 구글 시트에 업데이트합니다."""
    try:
        if not creation_results:
            print("⚠️ 업데이트할 결과가 없습니다.")
            return
        
        # 현재 시트의 데이터 가져오기
        existing_data = worksheet.get_all_values()
        
        # 헤더가 있는지 확인하고, 없으면 추가
        if not existing_data or len(existing_data) == 0:
            # 헤더 추가
            worksheet.update('A1:C1', [['마스터상품번호', '입점사', '상품수']])
            print("✅ 헤더 추가 완료")
        
        # 기존 데이터에서 마지막 행 찾기
        last_row = len(existing_data) if existing_data else 1
        
        # 새 데이터 추가
        update_data = []
        for result in creation_results:
            row_data = [
                result['master_product_id'],
                result['product_name'], 
                result['created_count']
            ]
            update_data.append(row_data)
        
        # 데이터 업데이트 (A열부터 C열까지)
        start_row = last_row + 1
        end_row = start_row + len(update_data) - 1
        
        worksheet.update(f'A{start_row}:C{end_row}', update_data)
        
        print(f"✅ 구글 시트 업데이트 완료: {len(update_data)}개 행 추가")
        print(f"   업데이트 범위: A{start_row}:C{end_row}")
        
        # 업데이트된 데이터 출력
        print("\n📊 업데이트된 데이터:")
        print("-" * 50)
        for i, data in enumerate(update_data, 1):
            print(f"{i:2d}. {data[0]} | {data[1]} | {data[2]}개")
        
    except Exception as e:
        print(f"❌ 구글 시트 업데이트 중 오류 발생: {e}")

def automate_bflow_product_creation():
    """비플로우에서 상품 생성 작업을 자동화합니다."""
    driver = setup_driver()
    wait = WebDriverWait(driver, 10)
    
    # 생성 결과 수집을 위한 리스트
    creation_results = []
    
    try:
        print("1. 비플로우 로그인 페이지로 이동...")
        driver.get('https://b-flow.co.kr/login?prevUrl=products-v2%23%2F')

        print("2. 비플로우 사이트에 로그인합니다...")
        
        # 로그인 버튼 클릭
        login_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[3]/div[1]/div[2]/button[2]"))
        )
        login_button.click()
        
        # 로그인 정보 입력
        username_input = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.XPATH, "/html/body/div[1]/div[14]/div/div[2]/div/div[2]/div/input[1]"))
        )
        username_input.send_keys("a01025399154@brich.co.kr")
        
        password_input = driver.find_element(By.XPATH, "/html/body/div[1]/div[14]/div/div[2]/div/div[2]/div/input[2]")
        password_input.send_keys("2rlqmadl@!")
        
        submit_button = driver.find_element(By.XPATH, "/html/body/div[1]/div[14]/div/div[2]/div/div[3]/button[1]")
        submit_button.click()
        
        # 상품 관리 페이지 로딩 대기
        wait.until(EC.url_to_be("https://b-flow.co.kr/products-v2#/"))
        print("3. 상품 관리 페이지로 이동 완료.")

        # --- Y/N 확인 절차 추가 ---
        user_confirmation = input("자동화 작업을 시작하시겠습니까? (Y/N): ").strip().lower()
        print(f"입력된 값: '{user_confirmation}' (길이: {len(user_confirmation)})")
        if user_confirmation not in ['y', 'yes']:
            print("사용자 요청에 따라 작업을 종료합니다.")
            return # 함수 종료
        print("자동화 작업을 시작합니다...")
        # --- Y/N 확인 절차 추가 끝 ---
        
        # 4. 판매상태 필터 설정
        print("4. 판매상태 필터 설정...")
        try:
            # 판매상태 드롭다운 클릭
            status_dropdown_xpath = '//*[@id="main-page"]/div/div/section/div/div[2]/div[2]/div/div[2]/div/div/div/div[1]/div[2]/input'
            status_dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, status_dropdown_xpath)))
            status_dropdown.click()
            print("  -> 판매상태 드롭다운 클릭 완료")
            
            # "판매중" 옵션 선택
            time.sleep(1)  # 드롭다운이 열릴 때까지 대기
            selling_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(@class, 'multiselect__option') and .//span[text()='판매중']]")))
            selling_option.click()
            print("  -> '판매중' 선택 완료")
            
            # 드롭다운이 닫힐 때까지 대기
            time.sleep(1)
            
        except Exception as e:
            print(f"  -> 판매상태 필터 설정 실패: {e}")
            print("  -> 기본 상태로 검색을 계속 진행합니다.")
        
        # 5. 검색 버튼 클릭
        print("5. 검색 버튼 클릭...")
        search_button_xpath = '//*[@id="main-page"]/div/div/section/div/div[2]/div[6]/button[2]'
        wait.until(EC.element_to_be_clickable((By.XPATH, search_button_xpath))).click()
        
        # 6. 검색 결과 로딩 대기 (유동적 대기)
        print("검색 결과 로딩 중... 잠시만 기다려주세요.")
        
        # 테이블이 로딩될 때까지 대기 (최대 30초)
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".data-table > tbody:nth-child(2)")))
            print("검색 결과 테이블 로딩 완료.")
            
            # 테이블에 실제 데이터가 로딩될 때까지 추가 대기
            print("테이블 데이터 로딩 확인 중...")
            max_wait = 20  # 최대 20초 대기
            wait_count = 0
            
            while wait_count < max_wait:
                try:
                    table_body = driver.find_element(By.CSS_SELECTOR, ".data-table > tbody:nth-child(2)")
                    rows = table_body.find_elements(By.TAG_NAME, "tr")
                    
                    # 테이블에 실제 데이터가 있는지 확인
                    if rows and len(rows) > 0:
                        # 첫 번째 행에 데이터가 있는지 확인
                        first_row_tds = rows[0].find_elements(By.TAG_NAME, "td")
                        if len(first_row_tds) >= 10:  # 최소 10개 컬럼이 있는지 확인 (입점사명은 12번째)
                            print("테이블 데이터 로딩 완료.")
                            break
                    
                    print(f"데이터 로딩 대기 중... ({wait_count + 1}/{max_wait})")
                    time.sleep(1)
                    wait_count += 1
                    
                except:
                    print(f"테이블 확인 중... ({wait_count + 1}/{max_wait})")
                    time.sleep(1)
                    wait_count += 1
            
            if wait_count >= max_wait:
                print("테이블 로딩 시간 초과. 계속 진행합니다.")
                
        except Exception as e:
            print(f"테이블 로딩 중 오류 발생: {e}")
            print("추가 대기 후 계속 진행...")
            time.sleep(5)
        
        # 알림 처리 (상품을 선택해주세요 알림이 있을 경우)
        try:
            alert = driver.switch_to.alert
            print(f"알림 발견: {alert.text}")
            alert.accept()
            time.sleep(1)
        except:
            pass  # 알림이 없으면 계속 진행
        
        excluded_sellers = ["애경생활", "애경뷰티통합", "애경티슬로", "롯데웰푸드", "아이허브(iHerb)"]
        
        while True:
            # 7. 현재 페이지의 테이블 행 순회
            print("\n- 현재 페이지 상품 확인 및 처리...")
            
            # 테이블이 완전히 로딩될 때까지 대기
            try:
                table_body = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".data-table > tbody:nth-child(2)")))
                
                # 테이블 데이터가 완전히 로딩될 때까지 대기
                print("페이지 데이터 로딩 확인 중...")
                max_page_wait = 20  # 최대 20초 대기 (시간 증가)
                page_wait_count = 0
                
                while page_wait_count < max_page_wait:
                    rows = table_body.find_elements(By.TAG_NAME, "tr")
                    
                    if rows and len(rows) > 0:
                        # 첫 번째 행에 충분한 데이터가 있는지 확인
                        first_row_tds = rows[0].find_elements(By.TAG_NAME, "td")
                        if len(first_row_tds) >= 10:  # 최소 10개 컬럼이 있는지 확인
                            print("페이지 데이터 로딩 완료.")
                            # 추가 안정화 대기
                            time.sleep(2)
                            break
                    
                    print(f"페이지 데이터 로딩 대기 중... ({page_wait_count + 1}/{max_page_wait})")
                    time.sleep(1)
                    page_wait_count += 1
                
                if page_wait_count >= max_page_wait:
                    print("페이지 로딩 시간 초과. 현재 상태로 계속 진행...")
                
                rows = table_body.find_elements(By.TAG_NAME, "tr")
                if not rows:
                    print("테이블에 데이터가 없습니다. 잠시 대기 후 다시 시도...")
                    time.sleep(3)
                    continue
                    
            except Exception as e:
                print(f"테이블 로딩 중 오류 발생: {e}")
                time.sleep(3)
                continue
            
            print(f"총 {len(rows)}개 상품 발견. 순차적으로 처리합니다.")
            
            for i, row in enumerate(rows):
                try:
                    # 입점사명 가져오기 - 10개 컬럼 기준으로 수정
                    tds = row.find_elements(By.TAG_NAME, "td")
                    seller_name = None
                    
                    print(f"\n--- 상품 {i+1}/{len(rows)} 처리 시작 ---")
                    print(f"컬럼 수 = {len(tds)}")
                    
                    # 모든 컬럼 내용 출력 (디버깅용)
                    for j, td in enumerate(tds):
                        td_text = td.text.strip()
                        if td_text:  # 빈 텍스트가 아닌 경우만 출력
                            print(f"  컬럼 {j+1}: '{td_text}'")
                    
                    if len(tds) == 10:
                        # 10개 컬럼인 경우: 입점사는 8번째 컬럼 (0-based index 7)
                        try:
                            seller_name = tds[7].text.strip()
                            print(f"  -> 10개 컬럼에서 8번째 컬럼 사용: '{seller_name}'")
                        except:
                            print(f"  -> 8번째 컬럼 접근 실패")
                    elif len(tds) >= 12:
                        # 12개 이상 컬럼인 경우: 12번째 컬럼 (0-based index 11)
                        try:
                            seller_name = tds[11].text.strip()
                            print(f"  -> 12개 이상 컬럼에서 12번째 컬럼 사용: '{seller_name}'")
                        except:
                            print(f"  -> 12번째 컬럼 접근 실패")
                    else:
                        # 다른 컬럼 수인 경우: 키워드로 찾기
                        print(f"  -> 예상과 다른 컬럼 수 ({len(tds)}). 키워드로 입점사 찾기...")
                        for j, td in enumerate(tds):
                            td_text = td.text.strip()
                            if any(keyword in td_text for keyword in ["애경", "롯데", "아이허브", "입점사", "로아림"]):
                                seller_name = td_text
                                print(f"  -> {j+1}번째 컬럼에서 발견: '{seller_name}'")
                                break
                    
                    if not seller_name:
                        print(f"상품 {i+1}: 입점사명을 찾을 수 없습니다. 건너뜁니다.")
                        continue
                    
                    print(f"상품 {i+1}: 입점사 - {seller_name}")
                    
                    # 제외 입점사인지 확인
                    if seller_name not in excluded_sellers:
                        print("  -> '마켓 상품 생성' 대상입니다. 처리 시작.")
                        
                        # 체크박스 클릭 (같은 행에 있는)
                        try:
                            checkbox = row.find_element(By.CSS_SELECTOR, "td:nth-child(1) input")
                            driver.execute_script("arguments[0].click();", checkbox)
                            print("  -> 체크박스 클릭 완료")
                        except Exception as e:
                            print(f"  -> 체크박스 클릭 실패: {e}")
                            continue
                        
                        # 1단계: 마켓상품생성 버튼 클릭
                        print("  -> 1단계: 마켓상품생성 버튼 클릭...")
                        create_button_xpath = '//*[@id="app"]/div[1]/div/div/section/div/div[3]/div[2]/div[1]/button[2]'
                        
                        try:
                            # 버튼이 클릭 가능할 때까지 대기
                            create_button = wait.until(EC.element_to_be_clickable((By.XPATH, create_button_xpath)))
                            
                            # 버튼이 화면에 보이도록 스크롤
                            driver.execute_script("arguments[0].scrollIntoView(true);", create_button)
                            time.sleep(1)
                            
                            # JavaScript로 클릭 (더 안전함)
                            driver.execute_script("arguments[0].click();", create_button)
                            print("  -> 마켓상품생성 버튼 클릭 완료.")
                            
                        except Exception as e:
                            print(f"  -> 마켓상품생성 버튼 클릭 실패: {e}")
                            continue
                        
                        # 마켓상품생성 창이 나타날 때까지 대기
                        print("  -> 마켓상품생성 창 로딩 대기 중...")
                        time.sleep(3)  # 창이 완전히 로딩될 때까지 대기
                        
                        # 2단계: 마켓상품생성 창에서 '생성하기' 버튼 클릭
                        print("  -> 2단계: 생성하기 버튼 클릭...")
                        try:
                            # 마켓상품생성 모달 창 확인
                            modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".v--modal-box")))
                            print("  -> 마켓상품생성 창 확인됨.")
                            
                            # 생성하기 버튼 클릭
                            create_in_modal_button = modal.find_element(By.XPATH, './/button[text()="생성하기"]')
                            create_in_modal_button.click()
                            print("  -> 생성하기 버튼 클릭 완료.")
                            
                        except Exception as e:
                            print(f"  -> 생성하기 버튼 클릭 실패: {e}")
                            continue
                        
                        # 3단계: 상품 생성 처리 대기 (상품마다 로딩 시간이 다름)
                        print("  -> 3단계: 상품 생성 처리 중... (로딩 시간에 따라 최대 60초 대기)")
                        
                        # 생성 결과 모달이 나타날 때까지 충분히 대기
                        try:
                            # 최대 60초까지 대기 (상품에 따라 로딩 시간이 다름)
                            max_wait = 60
                            wait_count = 0
                            
                            while wait_count < max_wait:
                                try:
                                    result_modal = driver.find_element(By.CSS_SELECTOR, ".v--modal-box .btn-box")
                                    if result_modal.is_displayed():
                                        print("  -> 생성 결과 모달 나타남.")
                                        break
                                except:
                                    pass
                                
                                print(f"  -> 상품 생성 처리 대기 중... ({wait_count + 1}/{max_wait})")
                                time.sleep(1)
                                wait_count += 1
                            
                            if wait_count >= max_wait:
                                print("  -> 상품 생성 처리 시간 초과. 계속 진행...")
                                continue
                            
                            # 결과 모달이 완전히 로딩될 때까지 추가 대기
                            time.sleep(2)
                            
                            # 생성 결과 수집
                            try:
                                # 생성된 상품 수 추출
                                confirm_list = driver.find_element(By.CSS_SELECTOR, ".confirm-list")
                                confirm_text = confirm_list.text
                                print(f"  -> 생성 결과: {confirm_text}")
                                
                                # "X개 마켓상품이 신규 생성되었습니다"에서 숫자 추출
                                import re
                                match = re.search(r'(\d+)개 마켓상품이 신규 생성되었습니다', confirm_text)
                                if match:
                                    created_count = int(match.group(1))
                                    print(f"  -> 생성된 상품 수: {created_count}개")
                                    
                                    # 마스터상품번호 수집 (현재 처리 중인 상품의 번호)
                                    master_product_id = "수집실패"
                                    try:
                                        # 여러 셀렉터로 마스터상품번호 찾기
                                        selectors = [
                                            "td:nth-child(7)",  # 기본 셀렉터
                                            "td:nth-child(8)",  # 대안 1
                                            "td:nth-child(6)",  # 대안 2
                                            "td:nth-child(9)"   # 대안 3
                                        ]
                                        
                                        for selector in selectors:
                                            try:
                                                master_product_id = row.find_element(By.CSS_SELECTOR, selector).text.strip()
                                                if master_product_id and master_product_id.isdigit():
                                                    print(f"  -> 마스터상품번호: {master_product_id} (셀렉터: {selector})")
                                                    break
                                            except:
                                                continue
                                        
                                        if not master_product_id or not master_product_id.isdigit():
                                            print(f"  -> 마스터상품번호 수집 실패 - 모든 셀렉터 시도 완료")
                                            master_product_id = "수집실패"
                                            
                                    except Exception as e:
                                        print(f"  -> 마스터상품번호 수집 중 오류: {e}")
                                        master_product_id = "수집실패"
                                    
                                    # 생성된 상품 수와 관계없이 모든 처리한 상품 수집
                                    creation_results.append({
                                        'master_product_id': master_product_id,
                                        'created_count': created_count,
                                        'product_name': seller_name
                                    })
                                    print(f"  -> 결과 저장 완료: {master_product_id} - {created_count}개 생성")
                                else:
                                    # 생성 상품 수를 파싱할 수 없는 경우에도 수집
                                    print("  -> 생성 상품 수를 파싱할 수 없음. 기본값으로 수집")
                                    creation_results.append({
                                        'master_product_id': master_product_id,
                                        'created_count': 0,  # 파싱 실패 시 0으로 설정
                                        'product_name': seller_name
                                    })
                                    print(f"  -> 결과 저장 완료: {master_product_id} - 0개 생성 (파싱 실패)")
                                    
                            except Exception as e:
                                print(f"  -> 생성 결과 수집 중 오류: {e}")
                                # 오류가 발생해도 상품 정보는 수집
                                creation_results.append({
                                    'master_product_id': master_product_id,
                                    'created_count': 0,  # 오류 발생 시 0으로 설정
                                    'product_name': seller_name
                                })
                                print(f"  -> 오류 발생으로 기본값으로 수집: {master_product_id} - 0개 생성")
                            
                            # 4단계: 취소 버튼 클릭
                            print("  -> 4단계: 취소 버튼 클릭...")
                            cancel_button = result_modal.find_element(By.XPATH, './/button[text()="취소"]')
                            cancel_button.click()
                            print("  -> 취소 버튼 클릭 완료.")
                            
                            # 취소 후 모달이 닫힐 때까지 대기
                            time.sleep(2)
                            
                        except Exception as e:
                            print(f"  -> 생성 결과 모달 처리 중 오류: {e}")
                            print("  -> 상품 생성이 완료되지 않았을 수 있습니다.")
                            # 오류가 발생해도 다음 상품으로 진행
                        
                        # 5단계: 다음 상품 처리를 위한 대기
                        print("  -> 5단계: 상품 생성 처리 완료. 다음 상품 처리를 위한 대기...")
                        time.sleep(3)  # 안정적인 처리를 위한 충분한 대기
                    else:
                        print(f"  -> 제외 입점사({seller_name})입니다. 건너뜁니다.")
                        
                except Exception as e:
                    print(f"상품 처리 중 오류 발생: {e}")
                    # 오류 발생 시 다음 상품으로 넘어가기
                    continue
            
            # 8. 다음 페이지로 이동
            try:
                print("\n- 다음 페이지 버튼 확인...")
                
                # 페이지 로딩 상태 확인
                print("  -> 페이지 로딩 상태 확인 중...")
                max_page_check_wait = 10
                page_check_count = 0
                
                while page_check_count < max_page_check_wait:
                    try:
                        # 페이지가 완전히 로딩되었는지 확인
                        table_body = driver.find_element(By.CSS_SELECTOR, ".data-table > tbody:nth-child(2)")
                        rows = table_body.find_elements(By.TAG_NAME, "tr")
                        
                        if rows and len(rows) > 0:
                            first_row_tds = rows[0].find_elements(By.TAG_NAME, "td")
                            if len(first_row_tds) >= 10:
                                print("  -> 페이지 로딩 완료. 다음 페이지 버튼 확인 시작.")
                                break
                        
                        print(f"  -> 페이지 로딩 확인 중... ({page_check_count + 1}/{max_page_check_wait})")
                        time.sleep(1)
                        page_check_count += 1
                        
                    except:
                        print(f"  -> 페이지 상태 확인 중... ({page_check_count + 1}/{max_page_check_wait})")
                        time.sleep(1)
                        page_check_count += 1
                
                if page_check_count >= max_page_check_wait:
                    print("  -> 페이지 로딩 확인 시간 초과. 계속 진행...")
                
                # 여러 방법으로 다음 페이지 버튼 찾기
                next_page_link = None
                try:
                    # 방법 1: CSS 선택자로 찾기
                    next_page_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".pagination-next-nav a")))
                    print("  -> CSS 선택자로 다음 페이지 버튼 발견")
                except:
                    try:
                        # 방법 2: XPath로 찾기
                        next_page_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//li[@class='page-item pagination-next-nav']//a")))
                        print("  -> XPath로 다음 페이지 버튼 발견")
                    except:
                        try:
                            # 방법 3: aria-label로 찾기
                            next_page_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@aria-label='Next']")))
                            print("  -> aria-label로 다음 페이지 버튼 발견")
                        except:
                            print("  -> 다음 페이지 버튼을 찾을 수 없습니다.")
                            break
                
                if next_page_link is None:
                    print("마지막 페이지입니다. 자동화 종료.")
                    break
                
                # '다음' 버튼이 비활성화되었는지 확인
                parent_li = next_page_link.find_element(By.XPATH, "..")
                if "disabled" in parent_li.get_attribute("class") or "active" in parent_li.get_attribute("class"):
                    print("마지막 페이지입니다. 자동화 종료.")
                    break
                
                # JavaScript로 클릭 (더 안전함)
                driver.execute_script("arguments[0].click();", next_page_link)
                print("  -> 다음 페이지로 이동...")
                
                # 페이지 이동 후 충분한 로딩 대기
                print("  -> 페이지 로딩 대기 중...")
                time.sleep(5)  # 기본 대기 시간 증가
                
                # 테이블이 완전히 로딩될 때까지 대기
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".data-table > tbody:nth-child(2)")))
                    print("  -> 새 페이지 테이블 로딩 완료.")
                    
                    # 테이블 데이터가 완전히 로딩될 때까지 추가 대기
                    print("  -> 새 페이지 데이터 로딩 확인 중...")
                    max_page_wait = 15
                    page_wait_count = 0
                    
                    while page_wait_count < max_page_wait:
                        try:
                            table_body = driver.find_element(By.CSS_SELECTOR, ".data-table > tbody:nth-child(2)")
                            rows = table_body.find_elements(By.TAG_NAME, "tr")
                            
                            if rows and len(rows) > 0:
                                first_row_tds = rows[0].find_elements(By.TAG_NAME, "td")
                                if len(first_row_tds) >= 10:
                                    print("  -> 새 페이지 데이터 로딩 완료.")
                                    break
                            
                            print(f"  -> 새 페이지 데이터 로딩 대기 중... ({page_wait_count + 1}/{max_page_wait})")
                            time.sleep(1)
                            page_wait_count += 1
                            
                        except:
                            print(f"  -> 새 페이지 테이블 확인 중... ({page_wait_count + 1}/{max_page_wait})")
                            time.sleep(1)
                            page_wait_count += 1
                    
                    if page_wait_count >= max_page_wait:
                        print("  -> 새 페이지 로딩 시간 초과. 현재 상태로 계속 진행...")
                        
                except Exception as e:
                    print(f"  -> 새 페이지 로딩 중 오류 발생: {e}")
                    print("  -> 추가 대기 후 계속 진행...")
                    time.sleep(5)
            except Exception:
                print("다음 페이지 버튼을 찾을 수 없습니다. 마지막 페이지이거나 오류 발생.")
                break

    except Exception as e:
        print(f"자동화 작업 중 오류 발생: {e}")
    finally:
        # 수집된 생성 결과 출력
        print("\n" + "="*60)
        print("📊 상품 생성 결과 요약")
        print("="*60)
        
        if creation_results:
            total_created = sum(result['created_count'] for result in creation_results)
            print(f"총 {len(creation_results)}개 상품에서 {total_created}개 마켓상품이 생성되었습니다.")
            print("\n상세 결과:")
            print("-" * 60)
            
            for i, result in enumerate(creation_results, 1):
                print(f"{i:2d}. 마스터상품번호: {result['master_product_id']}")
                print(f"    입점사: {result['product_name']}")
                print(f"    생성된 마켓상품: {result['created_count']}개")
                print("-" * 60)
        else:
            print("생성된 상품이 없습니다.")
        
        # 구글 시트 업데이트
        print("\n" + "="*60)
        print("📊 구글 시트 업데이트")
        print("="*60)
        
        if creation_results:
            worksheet = authenticate_google_sheets()
            if worksheet:
                update_google_sheet_with_results(worksheet, creation_results)
            else:
                print("❌ 구글 시트 연결 실패로 업데이트를 건너뜁니다.")
        else:
            print("⚠️ 생성된 상품이 없어 구글 시트 업데이트를 건너뜁니다.")
        
        print("\n* 모든 작업이 완료되었습니다. 웹 드라이버를 종료합니다.")
        driver.quit()

if __name__ == '__main__':
    automate_bflow_product_creation()