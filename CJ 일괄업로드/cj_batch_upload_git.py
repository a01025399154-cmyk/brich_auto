#!/usr/bin/env python3
"""
CJ 할인 데이터 일괄 업로드 도구 (GitHub 버전)

엑셀 파일들을 읽어서 CJ API로 가격을 일괄 변경합니다.
환경변수를 통해 설정을 관리하며 이식성을 높였습니다.
"""

import os
import sys
import pandas as pd
import glob
from datetime import datetime
from pathlib import Path

# 환경변수 로드 (선택사항)
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✓ .env 파일을 찾았습니다.")
except ImportError:
    print("ℹ python-dotenv가 설치되지 않았습니다. 환경변수 대신 직접 설정을 사용합니다.")
except:
    print("ℹ .env 파일이 없습니다. 직접 설정을 사용합니다.")

# 간소화된 CJ API 클라이언트 import
from cj_api_client_simple import CJAPIClient

# --- 사용자 설정 부분 ---

# 프로젝트 루트 디렉토리
PROJECT_ROOT = Path(__file__).parent

# 1. 엑셀 파일이 있는 폴더 경로
EXCEL_FOLDER = os.getenv(
    "CJ_EXCEL_FOLDER",
    str(PROJECT_ROOT / "data" / "cj_discount_excel")
)

# 2. 리포트 저장 폴더 경로
REPORT_FOLDER = os.getenv(
    "CJ_REPORT_FOLDER",
    str(PROJECT_ROOT / "output" / "cj_upload_reports")
)

# 3. 배치 크기 (한 번에 처리할 상품 개수)
BATCH_SIZE = int(os.getenv("CJ_BATCH_SIZE", "50"))

# --- 설정 정보 출력 ---
print("\n" + "="*60)
print("🛒 CJ 할인 데이터 일괄 업로드 도구")
print("="*60)
print(f"📁 엑셀 폴더: {EXCEL_FOLDER}")
print(f"📂 리포트 폴더: {REPORT_FOLDER}")
print(f"📦 배치 크기: {BATCH_SIZE}개/배치")
print("="*60 + "\n")

# --- 코드 실행 부분 ---

def load_cj_excel_files(folder_path):
    """CJ할인설정 폴더의 모든 엑셀 파일을 로드합니다."""
    print(f"📁 폴더 스캔: {folder_path}")
    
    if not os.path.exists(folder_path):
        print(f"❌ 폴더를 찾을 수 없습니다: {folder_path}")
        print(f"\n💡 해결 방법:")
        print(f"   1. 폴더가 존재하는지 확인하세요.")
        print(f"   2. .env 파일에서 CJ_EXCEL_FOLDER 경로를 확인하세요.")
        print(f"   3. 또는 이 스크립트의 EXCEL_FOLDER 변수를 직접 수정하세요.")
        return [], []
    
    # 엑셀 파일 목록 가져오기
    excel_files = glob.glob(os.path.join(folder_path, "*.xlsx"))
    excel_files.sort()  # 파일명 순으로 정렬
    
    print(f"📊 발견된 엑셀 파일: {len(excel_files)}개")
    
    all_products = []
    file_summary = []
    
    for i, file_path in enumerate(excel_files, 1):
        try:
            print(f"\n[{i}/{len(excel_files)}] 처리 중: {os.path.basename(file_path)}")
            
            # 2행을 헤더로 읽기 (A3행부터 데이터)
            df = pd.read_excel(file_path, header=2)
            
            # 빈 행 제거
            df = df.dropna(how='all')
            
            if df.empty:
                print(f"  ⚠️  빈 파일입니다.")
                continue
            
            # 컬럼명 정리
            df.columns = ['itemCode', 'salePrice', 'commissionRate', 'supplyPrice', 'applyDate', 'applyTime']
            
            # 숫자형으로 변환
            df['itemCode'] = df['itemCode'].astype(str).str.replace('.0', '', regex=False)
            df['salePrice'] = pd.to_numeric(df['salePrice'], errors='coerce')
            df['commissionRate'] = pd.to_numeric(df['commissionRate'], errors='coerce')
            df['supplyPrice'] = pd.to_numeric(df['supplyPrice'], errors='coerce')
            
            # 공급가가 없는 경우 수수료율로 계산
            mask_no_supply_price = df['supplyPrice'].isna() | (df['supplyPrice'] == 0)
            df.loc[mask_no_supply_price, 'supplyPrice'] = (
                df.loc[mask_no_supply_price, 'salePrice'] * 
                (100 - df.loc[mask_no_supply_price, 'commissionRate']) / 100
            )
            
            # 디버깅: 엑셀에서 읽은 원본 데이터 확인
            print(f"  🔍 엑셀 원본 데이터 확인:")
            for idx, row in df.head(3).iterrows():
                if not pd.isna(row['itemCode']):
                    print(f"    상품 {row['itemCode']}: 판매가 {row['salePrice']:,}원, 공급가 {row['supplyPrice']:,}원, 수수료율 {row['commissionRate']}%")
            
            # NaN 값들을 0으로 대체 후 정수 변환
            df['supplyPrice'] = df['supplyPrice'].fillna(0).astype(int)
            
            # 필요한 컬럼만 선택
            df = df[['itemCode', 'salePrice', 'supplyPrice', 'commissionRate']].copy()
            
            # 유효한 데이터만 필터링
            valid_df = df.dropna(subset=['itemCode', 'salePrice'])
            
            if valid_df.empty:
                print(f"  ⚠️  유효한 데이터가 없습니다.")
                continue
            
            # 상품 데이터 추가
            file_products = []
            for _, row in valid_df.iterrows():
                product = {
                    'itemCode': str(row['itemCode']),
                    'salePrice': int(row['salePrice']),
                    'commissionRate': row['commissionRate'] if not pd.isna(row['commissionRate']) else None,
                    'applyDate': '',
                    'fileName': os.path.basename(file_path)
                }
                file_products.append(product)
                all_products.append(product)
            
            file_summary.append({
                'fileName': os.path.basename(file_path),
                'totalRows': len(df),
                'validProducts': len(file_products)
            })
            
            print(f"  ✅ {len(file_products)}개 상품 로드 완료")
            
            # 샘플 데이터 표시 (처음 3개만)
            if file_products:
                print(f"  📋 샘플 데이터:")
                for j, product in enumerate(file_products[:3]):
                    print(f"    {j+1}. {product['itemCode']}: {product['salePrice']:,}원 (수수료율: {product.get('commissionRate', 'N/A')}%)")
                if len(file_products) > 3:
                    print(f"    ... 외 {len(file_products)-3}개")
            
        except Exception as e:
            print(f"  ❌ 오류: {e}")
            file_summary.append({
                'fileName': os.path.basename(file_path),
                'totalRows': 0,
                'validProducts': 0,
                'error': str(e)
            })
    
    return all_products, file_summary

def batch_upload_to_cj(products, batch_size=50):
    """상품들을 배치로 나누어 CJ API에 업로드합니다."""
    print(f"\n🚀 CJ API 일괄 업로드 시작")
    print(f"📊 총 {len(products)}개 상품을 {batch_size}개씩 배치 처리")
    
    cj_client = CJAPIClient()
    results = []
    
    # 배치로 나누기
    for i in range(0, len(products), batch_size):
        batch = products[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(products) + batch_size - 1) // batch_size
        
        print(f"\n📦 배치 {batch_num}/{total_batches} 처리 중... ({len(batch)}개 상품)")
        
        # 각 상품별로 개별 요청
        batch_results = []
        for j, product in enumerate(batch, 1):
            print(f"  [{j}/{len(batch)}] {product['itemCode']} 처리 중...", end=" ")
            
            # CJ API 요청 데이터
            api_data = {
                'itemCode': product['itemCode'],
                'salePrice': product['salePrice'],
                'commissionRate': product.get('commissionRate', None),
                'applyDate': ''
            }
            
            result = cj_client.change_price(
                price_change_name=f"CJ일괄업로드-{product['fileName']}-{product['itemCode']}",
                sale_price_info_list=[api_data]
            )
            
            # CJ API 응답에서 실제 성공/실패 확인
            api_success = result.get('success', False)
            api_data_response = result.get('data', {})
            
            # CJ API 응답에서 error 필드 확인
            if api_data_response and api_data_response.get('error', False):
                api_success = False
                error_message = api_data_response.get('returnMessage', 'Unknown error')
            # CJ API 응답에서 failList 확인
            elif api_data_response and 'failList' in api_data_response and api_data_response['failList']:
                api_success = False
                error_message = api_data_response['failList'][0].get('errorMessage', 'Unknown error')
            else:
                error_message = result.get('error', '')
            
            batch_results.append({
                'itemCode': product['itemCode'],
                'salePrice': product['salePrice'],
                'commissionRate': product.get('commissionRate', None),
                'fileName': product['fileName'],
                'success': api_success,
                'error': error_message,
                'statusCode': result.get('status_code', 0)
            })
            
            if api_success:
                print(f"✅ 성공")
            else:
                print(f"❌ 실패: {error_message}")
        
        results.extend(batch_results)
        
        # 배치 간 잠시 대기 (API 부하 방지)
        if i + batch_size < len(products):
            print(f"  ⏳ 2초 대기 중...")
            import time
            time.sleep(2)
    
    return results

def generate_report(results, file_summary):
    """실행 결과 리포트를 생성합니다."""
    print(f"\n" + "=" * 60)
    print(f"📊 실행 결과 리포트")
    print(f"=" * 60)
    
    # 전체 통계
    total_products = len(results)
    success_count = sum(1 for r in results if r['success'])
    failed_count = total_products - success_count
    
    print(f"📈 전체 통계:")
    print(f"  총 상품 수: {total_products:,}개")
    print(f"  성공: {success_count:,}개 ({success_count/total_products*100:.1f}%)")
    print(f"  실패: {failed_count:,}개 ({failed_count/total_products*100:.1f}%)")
    
    # 파일별 통계
    print(f"\n📁 파일별 통계:")
    for file_info in file_summary:
        if 'error' in file_info:
            print(f"  ❌ {file_info['fileName']}: 오류 - {file_info['error']}")
        else:
            print(f"  📄 {file_info['fileName']}: {file_info['validProducts']}개 상품")
    
    # 실패한 상품들
    failed_products = [r for r in results if not r['success']]
    if failed_products:
        print(f"\n❌ 실패한 상품들 (최대 10개):")
        for product in failed_products[:10]:
            print(f"  - {product['itemCode']} ({product['fileName']}): {product['error']}")
        if len(failed_products) > 10:
            print(f"  ... 외 {len(failed_products)-10}개")
    
    # 성공한 상품들 샘플
    success_products = [r for r in results if r['success']]
    if success_products:
        print(f"\n✅ 성공한 상품들 샘플 (최대 5개):")
        for product in success_products[:5]:
            print(f"  - {product['itemCode']}: {product['salePrice']:,}원 ({product['fileName']})")
    
    # 엑셀 리포트 생성
    os.makedirs(REPORT_FOLDER, exist_ok=True)
    report_df = pd.DataFrame(results)
    report_file = f"cj_upload_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    report_path = os.path.join(REPORT_FOLDER, report_file)
    report_df.to_excel(report_path, index=False)
    print(f"\n📄 상세 리포트 저장: {report_path}")

def test_mode_only(products, file_summary):
    """테스트 모드로 데이터만 분석합니다."""
    print(f"\n" + "=" * 60)
    print(f"📊 테스트 모드 분석 결과 (실제 업로드 안함)")
    print(f"=" * 60)
    
    # 전체 통계
    total_products = len(products)
    print(f"📈 전체 통계:")
    print(f"  총 상품 수: {total_products:,}개")
    print(f"  처리된 파일: {len(file_summary)}개")
    
    # 파일별 통계
    print(f"\n📁 파일별 통계:")
    for file_info in file_summary:
        if 'error' in file_info:
            print(f"  ❌ {file_info['fileName']}: 오류 - {file_info['error']}")
        else:
            print(f"  📄 {file_info['fileName']}: {file_info['validProducts']}개 상품")
    
    # 가격 분포 분석
    if products:
        prices = [p['salePrice'] for p in products]
        print(f"\n💰 가격 분포 분석:")
        print(f"  최저가: {min(prices):,}원")
        print(f"  최고가: {max(prices):,}원")
        print(f"  평균가: {sum(prices)/len(prices):,.0f}원")
        
        # 가격대별 분포
        price_ranges = {
            "1만원 미만": len([p for p in prices if p < 10000]),
            "1-2만원": len([p for p in prices if 10000 <= p < 20000]),
            "2-3만원": len([p for p in prices if 20000 <= p < 30000]),
            "3-5만원": len([p for p in prices if 30000 <= p < 50000]),
            "5만원 이상": len([p for p in prices if p >= 50000])
        }
        
        print(f"\n📊 가격대별 분포:")
        for range_name, count in price_ranges.items():
            if count > 0:
                print(f"  {range_name}: {count:,}개 ({count/total_products*100:.1f}%)")
    
    # 샘플 상품들
    print(f"\n📋 샘플 상품들 (최대 10개):")
    for i, product in enumerate(products[:10], 1):
        print(f"  {i:2d}. {product['itemCode']}: {product['salePrice']:,}원 - {product['fileName']}")
    
    if len(products) > 10:
        print(f"  ... 외 {len(products)-10}개")
    
    # 엑셀 리포트 생성
    if products:
        os.makedirs(REPORT_FOLDER, exist_ok=True)
        report_df = pd.DataFrame(products)
        report_file = f"cj_products_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        report_path = os.path.join(REPORT_FOLDER, report_file)
        report_df.to_excel(report_path, index=False)
        print(f"\n📄 상세 리포트 저장: {report_path}")

def main():
    """메인 함수"""
    # 1단계: 엑셀 파일들 로드
    print(f"\n📁 1단계: 엑셀 파일 로드")
    products, file_summary = load_cj_excel_files(EXCEL_FOLDER)
    
    if not products:
        print("❌ 로드된 상품이 없습니다.")
        return
    
    print(f"\n📊 로드 완료: {len(products)}개 상품")
    
    # 2단계: 모드 선택
    print(f"\n📋 실행 모드를 선택하세요:")
    print(f"1. 테스트 모드 (데이터 분석만, 실제 업로드 안함)")
    print(f"2. 실제 업로드 모드 (CJ API로 실제 가격 변경)")
    
    choice = input(f"\n선택하세요 (1/2): ").strip()
    
    if choice == "1":
        # 테스트 모드
        print(f"\n🔍 테스트 모드 실행")
        test_mode_only(products, file_summary)
        print(f"\n🎉 테스트 분석이 완료되었습니다!")
        print(f"💡 실제 업로드를 원하시면 다시 실행해서 2번을 선택하세요.")
        
    elif choice == "2":
        # 실제 업로드 모드
        print(f"\n⚠️  주의: {len(products)}개 상품의 가격이 실제로 변경됩니다!")
        print(f"📁 대상 폴더: {EXCEL_FOLDER}")
        
        confirm = input(f"\n정말로 진행하시겠습니까? (y/N): ")
        if confirm.lower() not in ['y', 'yes']:
            print("취소되었습니다.")
            return
        
        # 3단계: CJ API 업로드
        print(f"\n🚀 2단계: CJ API 업로드")
        results = batch_upload_to_cj(products, BATCH_SIZE)
        
        # 4단계: 리포트 생성
        print(f"\n📊 3단계: 리포트 생성")
        generate_report(results, file_summary)
        
        print(f"\n🎉 일괄 업로드가 완료되었습니다!")
    
    else:
        print("❌ 잘못된 선택입니다.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 작업이 중단되었습니다.")
    except Exception as e:
        print(f"\n\n❌ 예상치 못한 오류가 발생했습니다: {e}")
        print("\n💡 이 오류가 계속 발생하면 GitHub Issues에 보고해주세요.")
