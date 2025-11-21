# -*- coding: utf-8 -*-

# 1. Google Cloud Platform (GCP) 서비스 계정 키 파일 경로
GSPREAD_CREDENTIALS_PATH = "/Users/a11/Desktop/cursor/credentials/inner-sale-979c1e8ed412.json"

# 2. 접근할 구글 스프레드시트 이름
SPREADSHEET_NAME = '딜 세팅(지마켓, 옥션)'

# 3. 데이터를 가져올 탭(시트) 이름
SOURCE_SHEET_NAME = '251122 아이미마인1.0_서브딜'

# 4. 상품번호가 있는 열 (A=1, B=2, C=3, ...)
PRODUCT_ID_COLUMN = 2  # B열

# 5. 작업 상태를 기록할 열
STATUS_COLUMN = 3  # C열

# 6. 작업 완료 시간을 기록할 열
TIMESTAMP_COLUMN = 4  # D열

# 7. 데이터 헤더가 있는 행 번호
HEADER_ROW = 4

# 8. 데이터 시작 행 번호
START_ROW = 5

# 9. b-flow 로그인 및 검색 URL
SEARCH_SITE_URL = 'https://b-flow.co.kr/login?'
BFLOW_ID = "a01025399154@brich.co.kr"
BFLOW_PW = "2rlqmadl@!"

# 10. 다운로드 파일이 저장될 폴더 경로
DOWNLOAD_FOLDER = "/Users/a11/Desktop/1.0딜"

# 11. 오류 발생 시 재시도 횟수
RETRY_COUNT = 3

# 12. 병렬 처리를 위한 워커 수 (이미지 추출 시 사용)
MAX_WORKERS = 4
