# CJ 할인 데이터 일괄 업로드 도구

CJ 오쇼핑의 엑셀 파일들을 읽어서 API로 가격을 일괄 변경하는 Python 도구입니다.

## 📋 주요 기능

- 여러 엑셀 파일을 한 번에 처리
- CJ API를 통한 자동 가격 변경
- 배치 처리로 안정적인 업로드
- 테스트 모드로 사전 검증 가능
- 상세한 결과 리포트 생성
- 환경변수를 통한 유연한 설정

## 🔧 필수 요구사항

### Python 버전
- Python 3.7 이상

### 필수 라이브러리
```bash
pip install pandas openpyxl requests
```

### 선택 라이브러리 (환경변수 사용 시)
```bash
pip install python-dotenv
```

## 📁 파일 구조

```
project/
├── cj_batch_upload_git.py      # 메인 실행 파일
├── cj_api_client_simple.py     # CJ API 클라이언트
├── .env                         # 환경변수 설정 (직접 생성)
├── .env_cj_batch.example        # 환경변수 예제
├── data/                        # 데이터 폴더 (직접 생성)
│   └── cj_discount_excel/       # 엑셀 파일 저장 위치
│       ├── 2025-11-28_1.xlsx
│       ├── 2025-11-28_2.xlsx
│       └── ...
└── output/                      # 출력 폴더 (자동 생성)
    └── cj_upload_reports/       # 리포트 저장 위치
```

## 🚀 사용 방법

### 1단계: 환경변수 설정

`.env_cj_batch.example` 파일을 복사하여 `.env`로 저장:
```bash
cp .env_cj_batch.example .env
```

`.env` 파일을 편집하여 필수 정보 입력:
```bash
# 필수: CJ API 인증 키
CJ_AUTH_KEY=your_actual_authentication_key

# 선택: 폴더 경로 (기본값 사용 가능)
CJ_EXCEL_FOLDER=data/cj_discount_excel
CJ_REPORT_FOLDER=output/cj_upload_reports
```

### 2단계: 엑셀 파일 준비

1. `data/cj_discount_excel` 폴더 생성
2. CJ 할인 엑셀 파일들을 해당 폴더에 복사

**엑셀 파일 형식:**
- A3행부터 데이터 시작 (A2행은 헤더)
- 필수 열: 상품코드, 판매가, 수수료율

### 3단계: 실행

```bash
python cj_batch_upload_git.py
```

### 4단계: 모드 선택

실행 후 모드를 선택합니다:

**1. 테스트 모드** (권장)
- 실제 API 호출 없이 데이터만 분석
- 가격 분포, 파일별 통계 확인
- 문제가 없는지 사전 검증

**2. 실제 업로드 모드**
- CJ API로 실제 가격 변경
- 배치 처리로 안정적 업로드
- 상세한 결과 리포트 생성

## ⚙️ 환경변수 설명

| 환경변수 | 설명 | 기본값 | 필수 |
|---------|------|--------|------|
| `CJ_VENDOR_CODE` | CJ 벤더 코드 | `456988` | ❌ |
| `CJ_AUTH_KEY` | CJ API 인증 키 | - | ✅ |
| `CJ_API_URL` | CJ API 엔드포인트 | 기본 URL | ❌ |
| `CJ_EXCEL_FOLDER` | 엑셀 파일 폴더 | `data/cj_discount_excel` | ❌ |
| `CJ_REPORT_FOLDER` | 리포트 저장 폴더 | `output/cj_upload_reports` | ❌ |
| `CJ_BATCH_SIZE` | 배치 크기 | `50` | ❌ |
| `HTTP_PROXY` | HTTP 프록시 | - | ❌ |
| `HTTPS_PROXY` | HTTPS 프록시 | - | ❌ |

## 📊 엑셀 파일 형식

### 필수 구조
- **A2행**: 헤더 (상품코드, 판매가, 수수료율, 공급가, 적용일, 적용시간)
- **A3행 이후**: 실제 데이터

### 예시
```
| 상품코드    | 판매가 | 수수료율 | 공급가 | 적용일 | 적용시간 |
|------------|--------|---------|--------|--------|----------|
| 2058944322 | 30000  | 10      | 27000  |        |          |
| 2058944323 | 25000  | 15      | 21250  |        |          |
```

**참고:**
- 공급가가 없으면 자동으로 계산됩니다: `공급가 = 판매가 × (100 - 수수료율) / 100`
- 적용일은 자동으로 설정됩니다 (현재 시간 + 10초)

## 🎯 출력 결과

### 콘솔 출력
- 파일별 처리 진행 상황
- 상품별 성공/실패 여부
- 전체 통계 (성공률, 실패율)
- 실패한 상품 목록

### 엑셀 리포트
`output/cj_upload_reports/` 폴더에 저장됩니다:
- `cj_upload_report_YYYYMMDD_HHMMSS.xlsx` - 실제 업로드 결과
- `cj_products_test_report_YYYYMMDD_HHMMSS.xlsx` - 테스트 모드 결과

리포트 내용:
- 상품코드
- 판매가
- 수수료율
- 파일명
- 성공/실패 여부
- 오류 메시지 (실패 시)

## 🔍 문제 해결

### CJ_AUTH_KEY 오류
```
⚠️  경고: CJ_AUTH_KEY 환경변수가 설정되지 않았습니다.
```
**해결 방법**: `.env` 파일에 `CJ_AUTH_KEY=실제_인증키` 추가

### 폴더를 찾을 수 없음
```
❌ 폴더를 찾을 수 없습니다: data/cj_discount_excel
```
**해결 방법**:
1. `data/cj_discount_excel` 폴더 생성
2. 또는 `.env`에서 `CJ_EXCEL_FOLDER` 경로 수정

### 프록시 연결 오류
```
❌ 프록시 연결 오류
```
**해결 방법**:
1. `.env`에서 프록시 설정 확인
2. 프록시가 필요없다면 `HTTP_PROXY`, `HTTPS_PROXY` 주석 처리

### API 호출 실패
```
❌ 실패: [오류 메시지]
```
**해결 방법**:
1. CJ_AUTH_KEY가 올바른지 확인
2. 상품코드가 유효한지 확인
3. 판매가가 올바른 범위인지 확인

## 📝 원본 파일과의 차이점

`cj_batch_upload_git.py`는 `cj_batch_upload.py`의 개선 버전입니다:

- ✅ 환경변수 지원 (.env 파일)
- ✅ 간소화된 의존성 (api/ 폴더 불필요)
- ✅ 상대 경로 지원
- ✅ 더 상세한 오류 메시지
- ✅ 독립 실행 가능
- ✅ 이식성 향상

## 🤝 기여

버그 리포트나 기능 제안은 GitHub Issues를 통해 제출해주세요.

## 📄 라이선스

이 프로젝트는 개인 또는 상업적 용도로 자유롭게 사용할 수 있습니다.
