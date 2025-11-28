"""
CJ 할인 데이터 분할 프로그램 - 설정 예제 파일

이 파일을 복사하여 config.py로 저장하고 자신의 환경에 맞게 수정하세요.
또는 .env 파일을 사용할 수도 있습니다.
"""

# 원본 데이터 파일 경로
# 예: "/Users/username/Desktop/CJ할인설정/원본/CJ할인원본.xlsx"
CJ_SOURCE_FILE = "data/CJ할인원본.xlsx"

# 양식(템플릿) 파일 경로
# 예: "/Users/username/Desktop/CJ할인설정/원본/CJ 할인 시트_0.xlsx"
CJ_TEMPLATE_FILE = "data/CJ 할인 시트_0.xlsx"

# 분할된 파일들을 저장할 폴더 경로
# 예: "/Users/username/Desktop/CJ할인설정/output"
CJ_OUTPUT_DIR = "output/cj_discount"

# 한 파일에 들어갈 데이터 행의 개수
CJ_CHUNK_SIZE = 500
