# CJ 할인 데이터 분할 프로그램

CJ 할인 엑셀 데이터를 읽어서 지정된 크기로 분할하여 여러 개의 엑셀 파일로 저장하는 Python 스크립트입니다.

## 📋 주요 기능

- 대용량 엑셀 파일을 지정된 행 개수로 자동 분할
- 템플릿 파일의 서식을 유지하면서 데이터 삽입
- 환경변수 또는 설정 파일을 통한 유연한 경로 설정
- 날짜별 파일명 자동 생성 (YYYY-MM-DD_번호.xlsx)
- 상세한 진행 상황 및 오류 메시지 제공

## 🔧 필수 요구사항

### Python 버전
- Python 3.7 이상

### 필수 라이브러리
```bash
pip install pandas openpyxl
```

### 선택 라이브러리 (환경변수 사용 시)
```bash
pip install python-dotenv
```

또는 `requirements.txt`를 사용하여 한 번에 설치:
```bash
pip install -r requirements.txt
```

## 📁 파일 구조

```
project/
├── cjsales_git.py          # 메인 실행 파일
├── config_example.py        # 설정 예제 파일
├── .env.example            # 환경변수 예제 파일
├── requirements.txt        # Python 라이브러리 목록
├── data/                   # 데이터 폴더 (직접 생성)
│   ├── CJ할인원본.xlsx     # 원본 데이터 파일
│   └── CJ 할인 시트_0.xlsx # 템플릿 파일
└── output/                 # 출력 폴더 (자동 생성)
    └── cj_discount/        # 분할된 파일 저장 위치
```

## 🚀 사용 방법

### 1단계: 프로젝트 준비

1. 이 저장소를 클론하거나 다운로드합니다
2. 필요한 라이브러리를 설치합니다
   ```bash
   pip install -r requirements.txt
   ```

### 2단계: 데이터 파일 준비

1. 프로젝트 폴더에 `data` 폴더를 생성합니다
2. 다음 파일들을 `data` 폴더에 넣습니다:
   - `CJ할인원본.xlsx`: 분할할 원본 데이터 파일
   - `CJ 할인 시트_0.xlsx`: 서식이 적용된 템플릿 파일

### 3단계: 설정 (3가지 방법 중 선택)

#### 방법 1: 환경변수 사용 (.env 파일) - 권장
```bash
# .env.example을 복사하여 .env 파일 생성
cp .env.example .env

# .env 파일을 편집하여 경로 설정
# 예: CJ_SOURCE_FILE=data/CJ할인원본.xlsx
```

#### 방법 2: 설정 파일 사용
```bash
# config_example.py를 복사하여 config.py 생성
cp config_example.py config.py

# config.py 파일을 편집하여 경로 설정
```

#### 방법 3: 스크립트 직접 수정
`cjsales_git.py` 파일을 열어서 다음 변수들을 직접 수정:
- `source_file`: 원본 데이터 파일 경로
- `template_file`: 템플릿 파일 경로
- `output_dir`: 출력 폴더 경로
- `chunk_size`: 파일당 행 개수

### 4단계: 실행

```bash
python cjsales_git.py
```

## ⚙️ 설정 옵션

### 환경변수 목록

| 환경변수 | 설명 | 기본값 |
|---------|------|--------|
| `CJ_SOURCE_FILE` | 원본 데이터 파일 경로 | `data/CJ할인원본.xlsx` |
| `CJ_TEMPLATE_FILE` | 템플릿 파일 경로 | `data/CJ 할인 시트_0.xlsx` |
| `CJ_OUTPUT_DIR` | 출력 폴더 경로 | `output/cj_discount` |
| `CJ_CHUNK_SIZE` | 파일당 행 개수 | `500` |

### 경로 설정 방법

- **상대 경로**: 프로젝트 폴더 기준 (예: `data/file.xlsx`)
- **절대 경로**: 전체 경로 (예: `/Users/username/Desktop/file.xlsx`)

## 📊 원본 데이터 형식

원본 엑셀 파일은 다음 구조를 따라야 합니다:

- **A2행**: 헤더 (열 이름)
- **A3행 이후**: 실제 데이터
- **필수 열**:
  - B열: 판매가K
  - C열: CJ상품코드
  - E열: 업로드용마진

## 🎯 출력 결과

실행 후 다음과 같은 파일들이 생성됩니다:

```
output/cj_discount/
├── 2025-11-28_1.xlsx
├── 2025-11-28_2.xlsx
├── 2025-11-28_3.xlsx
└── ...
```

각 파일은:
- 템플릿 파일의 서식을 유지
- A5행부터 데이터가 삽입됨
- 최대 `chunk_size`개의 행 포함

## 🔍 문제 해결

### 파일을 찾을 수 없다는 오류
```
❌ 오류: 원본 데이터 파일을 찾을 수 없습니다.
```
**해결 방법**:
1. 파일 경로가 올바른지 확인
2. 파일이 실제로 해당 위치에 있는지 확인
3. 상대 경로를 사용하는 경우 프로젝트 루트에서 실행하는지 확인

### 라이브러리 import 오류
```
ModuleNotFoundError: No module named 'pandas'
```
**해결 방법**:
```bash
pip install pandas openpyxl
```

### 데이터 가공 오류
```
❌ 오류: 데이터 가공 중 문제가 발생했습니다.
```
**해결 방법**:
1. 원본 파일의 열 구조가 예상과 일치하는지 확인
2. 오류 메시지에 표시된 열 정보를 확인
3. 필요시 스크립트의 열 매핑 부분 수정

### 엑셀 파일이 열려있음
```
PermissionError: [Errno 13] Permission denied
```
**해결 방법**:
- 템플릿 파일이나 출력 파일이 다른 프로그램에서 열려있지 않은지 확인

## 📝 원본 파일과의 차이점

`cjsales_git.py`는 `cjsales.py`의 개선 버전으로 다음 기능이 추가되었습니다:

- ✅ 환경변수 지원 (.env 파일)
- ✅ 상대 경로 지원
- ✅ 더 상세한 오류 메시지 및 해결 방법 안내
- ✅ 진행 상황 표시 개선
- ✅ 예외 처리 강화
- ✅ 사용자 친화적인 출력 메시지

## 📄 라이선스

이 프로젝트는 개인 또는 상업적 용도로 자유롭게 사용할 수 있습니다.

## 🤝 기여

버그 리포트나 기능 제안은 GitHub Issues를 통해 제출해주세요.

## 📧 문의

문제가 발생하거나 질문이 있으시면 GitHub Issues에 등록해주세요.
