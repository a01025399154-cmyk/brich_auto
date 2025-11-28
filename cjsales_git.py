"""
CJ 할인 데이터 분할 프로그램 (GitHub 버전)

원본 엑셀 파일을 읽어서 지정된 크기로 분할하여 여러 개의 엑셀 파일로 저장합니다.
환경변수 또는 직접 설정을 통해 경로를 지정할 수 있습니다.
"""

import pandas as pd
import openpyxl
import os
import shutil
import math
from datetime import datetime
from pathlib import Path

# --- 환경변수 로드 (선택사항) ---
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✓ .env 파일을 찾았습니다.")
except ImportError:
    print("ℹ python-dotenv가 설치되지 않았습니다. 환경변수 대신 직접 설정을 사용합니다.")
except:
    print("ℹ .env 파일이 없습니다. 직접 설정을 사용합니다.")

# --- 사용자 설정 부분 ---

# 프로젝트 루트 디렉토리 (이 스크립트가 있는 위치)
PROJECT_ROOT = Path(__file__).parent

# 1. 원본 데이터 파일 경로
# 환경변수 CJ_SOURCE_FILE이 있으면 사용, 없으면 기본값 사용
source_file = os.getenv(
    "CJ_SOURCE_FILE",
    str(PROJECT_ROOT / "data" / "CJ할인원본.xlsx")
)

# 2. 양식(템플릿) 파일 경로
# 환경변수 CJ_TEMPLATE_FILE이 있으면 사용, 없으면 기본값 사용
template_file = os.getenv(
    "CJ_TEMPLATE_FILE",
    str(PROJECT_ROOT / "data" / "CJ 할인 시트_0.xlsx")
)

# 3. 분할된 파일들을 저장할 폴더 경로
# 환경변수 CJ_OUTPUT_DIR이 있으면 사용, 없으면 기본값 사용
output_dir = os.getenv(
    "CJ_OUTPUT_DIR",
    str(PROJECT_ROOT / "output" / "cj_discount")
)

# 4. 생성될 파일의 기본 이름 (사용되지 않음 - 날짜_번호.xlsx 형식으로 자동 생성)
base_filename = "CJ 할인 시트_0"

# 5. 한 파일에 들어갈 데이터 행의 개수
# 환경변수 CJ_CHUNK_SIZE가 있으면 사용, 없으면 기본값 500 사용
try:
    chunk_size = int(os.getenv("CJ_CHUNK_SIZE", "500"))
except ValueError:
    print("⚠️  CJ_CHUNK_SIZE 환경변수가 올바른 숫자가 아닙니다. 기본값 500을 사용합니다.")
    chunk_size = 500

# --- 설정 정보 출력 ---
print("\n" + "="*60)
print("CJ 할인 데이터 분할 프로그램")
print("="*60)
print(f"📁 원본 파일: {source_file}")
print(f"📋 템플릿 파일: {template_file}")
print(f"📂 출력 폴더: {output_dir}")
print(f"📊 분할 크기: {chunk_size}개 행/파일")
print("="*60 + "\n")

# --- 코드 실행 부분 ---

def process_and_split_files():
    """
    원본 엑셀 데이터를 읽고 가공한 후, 양식 파일에 맞춰
    정해진 개수만큼 나누어 새로운 엑셀 파일들로 저장합니다.
    """
    # 0. 필수 파일 및 폴더 존재 여부 확인
    if not os.path.exists(source_file):
        print(f"❌ 오류: 원본 데이터 파일을 찾을 수 없습니다.")
        print(f"   경로: {source_file}")
        print(f"\n💡 해결 방법:")
        print(f"   1. 파일이 해당 경로에 있는지 확인하세요.")
        print(f"   2. .env 파일에서 CJ_SOURCE_FILE 경로를 확인하세요.")
        print(f"   3. 또는 이 스크립트의 source_file 변수를 직접 수정하세요.")
        return
    
    if not os.path.exists(template_file):
        print(f"❌ 오류: 양식 파일을 찾을 수 없습니다.")
        print(f"   경로: {template_file}")
        print(f"\n💡 해결 방법:")
        print(f"   1. 파일이 해당 경로에 있는지 확인하세요.")
        print(f"   2. .env 파일에서 CJ_TEMPLATE_FILE 경로를 확인하세요.")
        print(f"   3. 또는 이 스크립트의 template_file 변수를 직접 수정하세요.")
        return
    
    # 출력 폴더가 없으면 생성
    os.makedirs(output_dir, exist_ok=True)
    print(f"✓ 출력 폴더 준비 완료: '{output_dir}'\n")

    # 1. 원본 데이터 파일 읽기 (A2행을 헤더로, A3부터 데이터 시작)
    try:
        print("📖 원본 데이터 파일을 읽는 중입니다...")
        source_df = pd.read_excel(source_file, header=1)  # A2행을 헤더로, A3부터 데이터
        # 열 이름이 문자열인 경우에만 공백 제거
        source_df.columns = [str(col).strip() if isinstance(col, str) else str(col) for col in source_df.columns]
        print(f"✓ 파일 읽기 완료 (총 {len(source_df)}개 행)\n")
    except Exception as e:
        print(f"❌ 오류: 원본 데이터 파일을 읽는 중 문제가 발생했습니다.")
        print(f"   상세 오류: {e}")
        print(f"\n💡 해결 방법:")
        print(f"   1. 파일이 손상되지 않았는지 확인하세요.")
        print(f"   2. 엑셀 파일이 다른 프로그램에서 열려있지 않은지 확인하세요.")
        print(f"   3. pandas와 openpyxl 라이브러리가 설치되어 있는지 확인하세요.")
        return

    # 2. 새로운 양식에 맞게 데이터 가공 및 재구성
    print("🔄 데이터를 새로운 양식에 맞게 가공합니다...")
    # 출력될 데이터프레임 생성
    output_df = pd.DataFrame()

    # 열 매핑 및 데이터 할당 (양식 구조에 맞춰 수정)
    try:
        # 원본 데이터를 양식 구조에 맞게 매핑
        # 원본: 0:B.상품코드, 1:판매가K, 2:CJ상품코드, 3:외부할인, 4:할인판매가, 5:공급가, 6:등록할인율, 7:종료일
        output_df['CJ상품코드'] = source_df.iloc[:, 2]      # 원본 C열 → 양식 A5열
        output_df['판매가K'] = source_df.iloc[:, 1]         # 원본 B열 → 양식 B5열  
        output_df['업로드용마진'] = source_df.iloc[:, 4]    # 원본 E열 → 양식 C3열 (10 → 10)
        
        print(f"✓ 데이터 가공 완료 (총 {len(output_df)}개 행)\n")
    except Exception as e:
        print(f"❌ 오류: 데이터 가공 중 문제가 발생했습니다.")
        print(f"   상세 오류: {e}")
        print(f"\n사용 가능한 열 정보:")
        for i, col in enumerate(source_df.columns):
            print(f"  {i}: '{col}'")
        print(f"\n💡 해결 방법:")
        print(f"   원본 파일의 열 구조가 예상과 다를 수 있습니다.")
        print(f"   위의 열 정보를 확인하고 스크립트를 수정해야 할 수 있습니다.")
        return

    total_rows = len(output_df)
    if total_rows == 0:
        print("⚠️  가공할 데이터가 없습니다. 작업을 종료합니다.")
        return

    # 3. 가공된 데이터를 정해진 크기로 나누어 파일로 저장
    num_files = math.ceil(total_rows / chunk_size)
    print(f"📦 총 {total_rows}개의 데이터를 {chunk_size}개씩 나누어 {num_files}개의 파일을 생성합니다.\n")

    # 오늘 날짜를 YYYY-MM-DD 형식으로 가져오기
    today = datetime.now().strftime("%Y-%m-%d")
    
    success_count = 0
    fail_count = 0
    
    for i in range(num_files):
        # 파일 이름에 붙일 번호 계산 (1부터 시작).
        file_num = i + 1
        output_filename = f"{today}_{file_num}.xlsx"
        output_path = os.path.join(output_dir, output_filename)

        print(f"[{file_num}/{num_files}] '{output_filename}' 파일 생성 중...", end=" ")

        # a. 양식 파일을 새 출력 파일로 복사 (서식 유지를 위함)
        try:
            shutil.copy(template_file, output_path)
        except Exception as e:
            print(f"❌ 실패 (템플릿 복사 오류: {e})")
            fail_count += 1
            continue

        # b. 현재 처리할 데이터 조각(chunk) 선택
        start_index = i * chunk_size
        end_index = start_index + chunk_size
        chunk = output_df.iloc[start_index:end_index]

        try:
            # c. 복사된 엑셀 파일을 열고 데이터 추가
            workbook = openpyxl.load_workbook(output_path)
            sheet = workbook.active

            # d. 데이터프레임의 각 행을 엑셀 시트에 추가 (A5부터 시작)
            start_row = 5  # A5부터 시작
            for chunk_idx, (_, row) in enumerate(chunk.iterrows()):
                row_data = list(row)
                for col_idx, value in enumerate(row_data, start=1):  # 열은 1부터 시작 (A=1, B=2, ...)
                    cell = sheet.cell(row=start_row + chunk_idx, column=col_idx)
                    # B열의 셀 형식을 숫자로 변경
                    if col_idx == 2:  # B=2 (판매가K)
                        cell.number_format = '#,##0'  # 천 단위 구분자 포함
                    # C열의 셀 형식을 숫자로 변경
                    elif col_idx == 3:  # C=3 (업로드용마진)
                        cell.number_format = '0'  # 숫자 형식
                    cell.value = value

            # e. 변경사항 저장
            workbook.save(output_path)
            print(f"✓ 완료 ({len(chunk)}개 행)")
            success_count += 1

        except Exception as e:
            print(f"❌ 실패 (데이터 저장 오류: {e})")
            fail_count += 1

    # 최종 결과 출력
    print("\n" + "="*60)
    print("작업 완료!")
    print("="*60)
    print(f"✓ 성공: {success_count}개 파일")
    if fail_count > 0:
        print(f"❌ 실패: {fail_count}개 파일")
    print(f"📂 저장 위치: {output_dir}")
    print("="*60)

# 스크립트 실행
if __name__ == "__main__":
    try:
        process_and_split_files()
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 작업이 중단되었습니다.")
    except Exception as e:
        print(f"\n\n❌ 예상치 못한 오류가 발생했습니다: {e}")
        print("\n💡 이 오류가 계속 발생하면 GitHub Issues에 보고해주세요.")
