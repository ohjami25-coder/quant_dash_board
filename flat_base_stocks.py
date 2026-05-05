import pandas as pd
import FinanceDataReader as fdr
import json
import numpy as np
from datetime import datetime, timedelta

# 1. 사용자 상수 및 경로 설정
TICKER_PATH = './tickers/kskq350.xlsx'
OUTPUT_PATH = 'flat_base_stocks.json'

def get_flat_base_stocks():
    try:
        # 엑셀 파싱 (앞 6자 코드, 7자 이후 이름)
        df_tickers = pd.read_excel(TICKER_PATH)
        raw_list = df_tickers['symbols'].astype(str).tolist()
    except Exception as e:
        print(f"파일 로드 실패: {e}")
        return

    results = []
    today = datetime.now().strftime('%Y-%m-%d')
    # 최근 20거래일 데이터 확보
    start_date = (datetime.now() - timedelta(days=40)).strftime('%Y-%m-%d')

    print(f"--- 횡보 응축(Low StdDev) 스캔 시작: {today} ---")

    for entry in raw_list:
        try:
            code = entry[:6]
            name = entry[7:].strip()
            
            df = fdr.DataReader(code, start_date)
            if len(df) < 5: continue

            # 2. 최근 5거래일 종가 추출 (역순)
            recent_5_days = df['Close'].iloc[-5:].values
            
            # 3. 표준편차 계산
            std_dev = np.std(recent_5_days)
            # 주가 대비 표준편차 비율(변동 계수 느낌)로 계산해야 종목간 비교가 가능함
            std_ratio = (std_dev / recent_5_days[-1]) * 100
            
            # 4. 필터링: 표준편차 비율이 매우 낮은 종목 (예: 0.5% 미만)
            # 숫자가 작을수록 일직선에 가까운 횡보입니다.
            if std_ratio < 0.7: 
                results.append({
                    "code": code,
                    "name": name,
                    "std_ratio": round(float(std_ratio), 2), # 소수점 2자리
                    "current_price": int(recent_5_days[-1]),
                    "update_date": today
                })
                print(f"📦 에너지 응축: {name}({code}) - 변동률: {round(float(std_ratio), 2)}%")

        except Exception as e:
            continue

    # 5. JSON 저장
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    print(f"\n✅ 완료: {len(results)}개 종목이 {OUTPUT_PATH}에 저장되었습니다.")

if __name__ == "__main__":
    get_flat_base_stocks()