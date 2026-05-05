import pandas as pd
import FinanceDataReader as fdr
import json
import numpy as np
import os
from datetime import datetime

# 1. 사용자 상수 및 경로 설정
TICKER_PATH = './tickers/kskq350.xlsx'
OUTPUT_PATH = 'round_bottom.json'

# 사용자 제공 타겟 패턴 (16일 5ma diff)
TARGET_PATTERN = np.array([1.00, 0.97, 0.96, 0.93, 0.90, 0.93, 0.96, 0.96, 0.95, 1.01, 1.05])

def get_precision_similarity(v1, v2):
    """
    1.0을 차감하여 변화의 '기울기' 방향성만 극대화하여 유사도 계산
    """
    v1_centered = v1 - 1.0
    v2_centered = v2 - 1.0
    
    norm_v1 = np.linalg.norm(v1_centered)
    norm_v2 = np.linalg.norm(v2_centered)
    
    if norm_v1 == 0 or norm_v2 == 0:
        return 0
    
    # 코사인 유사도 계산
    similarity = np.dot(v1_centered, v2_centered) / (norm_v1 * norm_v2)
    return round(float(similarity) * 100, 2)

def run_quant_analysis():
    # 2. 엑셀 파일 로드 및 종목 파싱
    try:
        df_tickers = pd.read_excel(TICKER_PATH)
        # symbols 열에서 코드와 이름 분리
        raw_list = df_tickers['symbols'].astype(str).tolist()
    except Exception as e:
        print(f"파일 로드 실패: {e}")
        return

    results = []
    today = datetime.now().strftime('%Y-%m-%d')
    
    print(f"--- 분석 시작: {today} (유사도 70% 이상 & 5ma > 20ma) ---")

    for entry in raw_list:
        try:
            # 지침: 앞 6자 코드, 7자부터 종목명
            code = entry[:6]
            name = entry[7:].strip()
            
            # 3. 한국 종목 데이터 로드 (FinanceDataReader)
            df = fdr.DataReader(code)
            if len(df) < 40: continue

            # 이평선 계산
            ma5 = df['Close'].rolling(5).mean()
            ma20 = df['Close'].rolling(20).mean()
            
            # 4. 5ma diff 계산 (t / t-1)
            ma5_diff = (ma5 / ma5.shift(1)).dropna()
            if len(ma5_diff) < 16: continue
            
            # 최근 16일 패턴 추출
            current_pattern = ma5_diff.iloc[-11:].values
            
            # 5. 유사도 측정 (변별력을 높인 정밀 로직)
            sim_score = get_precision_similarity(TARGET_PATTERN, current_pattern)
            
            # 6. 필터링: 유사도 70% 이상 & 정배열(5ma > 20ma)
            curr_ma5 = ma5.iloc[-1]
            curr_ma20 = ma20.iloc[-1]
            
            if sim_score >= 40 and curr_ma5 > curr_ma20:
                results.append({
                    "code": code,
                    "name": name,
                    "u_score": sim_score,
                    "current_price": int(df['Close'].iloc[-1]),
                    "ma_status": "Bullish(5>20)",
                    "update_date": today
                })
                print(f"🎯 매칭: {name}({code}) - 유사도: {sim_score}%")

        except Exception as e:
            continue

    # 7. JSON 저장 (결과가 없을 경우 빈 리스트 저장)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    print(f"\n✅ 분석 완료: {len(results)}개 종목이 {OUTPUT_PATH}에 기록되었습니다.")

if __name__ == "__main__":
    run_quant_analysis()