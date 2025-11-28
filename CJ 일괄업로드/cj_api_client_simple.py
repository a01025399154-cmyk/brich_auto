#!/usr/bin/env python3
"""
CJ API 클라이언트 (간소화 버전)
환경변수를 통해 설정을 관리하며 외부 의존성을 최소화했습니다.
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict

# 환경변수 로드 (선택사항)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class CJAPIClient:
    """CJ 오쇼핑 API 클라이언트"""
    
    def __init__(self):
        # 환경변수에서 설정 로드
        self.vendor_code = os.getenv('CJ_VENDOR_CODE', '456988')
        self.auth_key = os.getenv('CJ_AUTH_KEY', '')
        self.api_url = os.getenv(
            'CJ_API_URL',
            'https://ingress-api.cjoshopping.com/item/setItemPriceMod'
        )
        
        # 프록시 설정 (환경변수에서 자동으로 읽음)
        self.proxies = {}
        if os.getenv('HTTP_PROXY'):
            self.proxies['http'] = os.getenv('HTTP_PROXY')
        if os.getenv('HTTPS_PROXY'):
            self.proxies['https'] = os.getenv('HTTPS_PROXY')
        
        # API 인증 키 확인
        if not self.auth_key:
            print("⚠️  경고: CJ_AUTH_KEY 환경변수가 설정되지 않았습니다.")
            print("   .env 파일에 CJ_AUTH_KEY를 설정하거나 환경변수를 설정하세요.")
    
    def get_headers(self) -> Dict:
        """API 요청 헤더 생성"""
        return {
            'Content-Type': 'application/json;charset=UTF-8',
            'vendorCode': self.vendor_code,
            'authentication': self.auth_key
        }
    
    def _get_current_datetime(self) -> str:
        """현재 시간을 YYYY-MM-DD HH:mm:ss 형식으로 반환 (10초 후)"""
        now = datetime.now() + timedelta(seconds=10)
        return now.strftime('%Y-%m-%d %H:%M:%S')
    
    def change_price(self, 
                    price_change_name: str,
                    sale_price_info_list: List[Dict],
                    price_change_reason_code: str = "50",
                    access_level: str = "01") -> Dict:
        """
        CJ 오쇼핑에서 상품 가격을 변경합니다.
        
        Args:
            price_change_name: 가격 변경명
            sale_price_info_list: 판매가격 정보 리스트
            price_change_reason_code: 가격 변경 사유 코드 (기본값: "50")
            access_level: 접근 레벨 (기본값: "01")
            
        Returns:
            API 응답 딕셔너리
        """
        
        # applyDate 자동 설정
        current_datetime = self._get_current_datetime()
        for item in sale_price_info_list:
            if 'applyDate' not in item or not item['applyDate']:
                item['applyDate'] = current_datetime
        
        # 요청 데이터 구성
        request_data = {
            "priceChangeName": price_change_name,
            "priceChangeReasonCode": price_change_reason_code,
            "accessLevel": access_level,
            "salePriceInformationList": sale_price_info_list
        }
        
        try:
            # 프록시 사용 여부 출력
            proxy_status = "사용" if self.proxies else "미사용"
            print(f"CJ API 호출 중... (프록시: {proxy_status})")
            
            # API 호출
            response = requests.post(
                self.api_url,
                headers=self.get_headers(),
                json=request_data,
                proxies=self.proxies if self.proxies else None,
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json() if response.content else {}
                
                # CJ API 응답에서 error 필드 확인
                if response_data.get('error', False):
                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "error": response_data.get('returnMessage', 'Unknown error'),
                        "data": response_data
                    }
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "data": response_data
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text
                }
                
        except requests.exceptions.ProxyError as e:
            return {
                "success": False,
                "error": f"프록시 연결 오류: {e}"
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"요청 오류: {e}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"예상치 못한 오류: {e}"
            }

# 사용 예시
if __name__ == "__main__":
    print("CJ API 클라이언트 테스트")
    print("=" * 60)
    
    client = CJAPIClient()
    
    print(f"API URL: {client.api_url}")
    print(f"Vendor Code: {client.vendor_code}")
    print(f"프록시 설정: {client.proxies if client.proxies else '없음'}")
    print("=" * 60)
