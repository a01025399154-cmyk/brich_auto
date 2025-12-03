"""
Hypercape 크롤러 설정 파일
"""

# 기본 URL
BASE_URL = "https://biz.hypercape.com"

# HTTP 헤더
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}

# 요청 간 딜레이 (초)
DELAY_MIN = 1.0
DELAY_MAX = 2.0

# 최대 재시도 횟수
MAX_RETRIES = 3

# 요청 타임아웃 (초)
TIMEOUT = 30

# 출력 디렉토리
OUTPUT_DIR = "output"

# 이미지 저장 디렉토리
IMAGE_DIR = "images"
