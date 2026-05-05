import pandas as pd
import FinanceDataReader as fdr
import json
import numpy as np
from datetime import datetime, timedelta

# 1. 사용자 상수 및 경로 설정
TICKER_PATH = './tickers/kskq350.xlsx'
OUTPUT_PATH = 'double_bottom.json'

def get_double_bottom_stocks():
    try:
        # 엑셀 파싱 (코드 6자리, 이름 7자리 이후)
        df_tickers = pd.read_excel(TICKER_PATH)
        raw_list = df_tickers['symbols'].astype(str).tolist()
    except Exception as e:
        print(f"파일 로드 실패: {e}")
        return

    results = []
    today = datetime.now().strftime('%Y-%m-%d')
    # 분석을 위해 충분한 데이터 로드 (최근 60일)
    start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')

    print(f"--- 더블바텀 스캔 시작: {today} ---")

    for entry in raw_list:
        try:
            code = entry[:6]
            name = entry[7:].strip()
            
            df = fdr.DataReader(code, start_date)
            if len(df) < 20: continue

            close = df['Close'].values
            
            # 2. 더블바텀 탐지 로직 (최근 20일 중심)
            # Local Minima(국소 저점)를 찾기 위해 단순화된 로직 적용
            # 1단계: 최근 20일 중 최저점(Second Bottom) 찾기
            second_bottom = np.min(close[-10:]) 
            # 2단계: 그 이전 10일 중 최저점(First Bottom) 찾기
            first_bottom = np.min(close[-20:-10]) 
            
            # 3단계: 패턴 검증
            # - 두 저점의 가격 차이가 5% 이내 (쌍바닥의 평탄함)
            # - 현재가가 두 번째 저점보다 높아야 함 (반등 중)
            price_diff = abs(first_bottom - second_bottom) / first_bottom
            current_price = close[-1]
            
            if price_diff <= 0.05 and current_price > second_bottom:
                # 5ma > 20ma 조건 추가하여 추세 전환 확인
                ma5 = df['Close'].rolling(5).mean().iloc[-1]
                ma20 = df['Close'].rolling(20).mean().iloc[-1]
                
                if ma5 > ma20:
                    results.append({
                        "code": code,
                        "name": name,
                        "bottom_diff": round(price_diff * 100, 2), # 소수점 2자리
                        "current_price": int(current_price),
                        "update_date": today
                    })
                    print(f"🎯 쌍바닥 포착: {name}({code}) - 차이: {round(price_diff * 100, 2)}%")

        except Exception as e:
            continue

    # 3. JSON 저장
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    print(f"\n✅ 완료: {len(results)}개 종목이 {OUTPUT_PATH}에 저장되었습니다.")

if __name__ == "__main__":
    get_double_bottom_stocks()