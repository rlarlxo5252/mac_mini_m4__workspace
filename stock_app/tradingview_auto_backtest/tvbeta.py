import time
import json
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains  # 추가
from webdriver_manager.chrome import ChromeDriverManager

# --- ⬇️ XPath 변수 (성과 탭 데이터 최종 수정) ⬇️ ---

# 1. 메인 탭 및 버튼 (기존)
PROFIT_PCT_XPATH = "//div[starts-with(@class, 'reportContainerOld-')]//div[starts-with(@class, 'change-') and contains(text(), '%')]"
TRADE_LIST_TAB_XPATH = "//button[@data-overflow-tooltip-text='거래목록']"
OVERVIEW_TAB_XPATH = "//button[@data-overflow-tooltip-text='오버뷰']"
SYMBOL_NAME_XPATH = "//button[@id='header-toolbar-symbol-search']//div[contains(@class, 'js-button-text')]"
TRADE_1_ENTRY_XPATH = "//tr[@data='1']/td[4]//div[@data-part='1']" # 거래 시작일

# 2. 추가 탭 버튼 (기존)
PERFORMANCE_TAB_XPATH = "//button[@data-overflow-tooltip-text='성과']"
TRADE_ANALYSIS_TAB_XPATH = "//button[@data-overflow-tooltip-text='거래 분석']"
RISK_RATIOS_TAB_XPATH = "//button[@data-overflow-tooltip-text='위험/성과 비율']"

# 3. 추가 데이터 앵커 (TR/Row 기반, 최종 교정됨)
# [수정] 성과 탭 데이터 - 퍼센트 값만 정확히 추출
NET_PROFIT_ANCHOR_XPATH = "//tr[.//div[contains(text(), '순이익')]]//div[starts-with(@class, 'percentValue-')]"
BUY_HOLD_RETURN_ANCHOR_XPATH = "//tr[.//div[contains(text(), '매수 후 보유 수익')]]//div[starts-with(@class, 'percentValue-')]"

# 거래 분석 탭 데이터
WIN_RATE_ANCHOR_XPATH = "//tr[.//div[contains(text(), '승률')]]//div[starts-with(@class, 'value-') and contains(text(), '%')]"
MAX_LOSS_ANCHOR_XPATH = "//tr[.//div[contains(text(), '최대 손실 거래')]]//div[starts-with(@class, 'value-') and contains(text(), '%')]"

# 위험/성과 비율 탭 데이터
PROFIT_FACTOR_ANCHOR_XPATH = "//tr[.//div[contains(text(), '수익지수')]]//div[starts-with(@class, 'value-') and not(contains(text(), '%'))]"
SHARPE_RATIO_ANCHOR_XPATH = "//tr[.//div[contains(text(), '샤프 레이쇼')]]//div[starts-with(@class, 'value-') and not(contains(text(), '%'))]"
SORTINO_RATIO_ANCHOR_XPATH = "//tr[.//div[contains(text(), '소티노 레이쇼')]]//div[starts-with(@class, 'value-') and not(contains(text(), '%'))]"
# --- ⬆️ 여기까지 XPath 변수 ⬆️ ---


# --- ⬇️ 'EC.not_'을 대체할 커스텀 대기 클래스 ⬇️ ---
class text_to_be_different_from:
    """
    요소의 텍스트가 주어진 텍스트와 달라질 때까지 기다리는
    커스텀 expected_condition 클래스입니다.
    """
    def __init__(self, locator, text_):
        self.locator = locator
        self.text = text_

    def __call__(self, driver):
        try:
            element_text = driver.find_element(*self.locator).text
            return element_text != self.text
        except StaleElementReferenceException:
            return True
        except NoSuchElementException:
            return False
# --- ⬆️ 커스텀 클래스 추가 완료 ⬆️ ---


def parse_profit_string(profit_str):
    """퍼센트 문자열에서 퍼센트 값만 추출하고 float으로 변환."""
    if not profit_str or profit_str in ['N/A', 'Scrape Fail', '—']:
        return None
    
    # % 기호가 있는 부분만 추출 (정규식 사용)
    import re
    # 패턴: 숫자(음수 포함), 쉼표, 소수점을 포함하고 % 기호로 끝나는 부분
    match = re.search(r'[+\-−]?[\d,]+\.?\d*%', profit_str)
    
    if not match:
        return None
    
    percent_part = match.group()
    
    # 쉼표, 퍼센트, + 기호 제거, − (마이너스 유니코드)를 - 로 변환
    clean_str = percent_part.replace(',', '').replace('%', '').replace('+', '').replace('−', '-').strip()
    
    # 빈 문자열이나 '-'만 있는 경우 처리
    if not clean_str or clean_str == '-':
        return None
    
    try:
        return float(clean_str)
    except ValueError:
        return None 

def scrape_performance(driver, wait, data):
    """'성과' 탭을 클릭하고 매수 후 보유 수익, 순이익을 파싱합니다."""
    print("    [Sub] '성과' 탭 클릭 시도...")
    wait.until(EC.element_to_be_clickable((By.XPATH, PERFORMANCE_TAB_XPATH))).click()
    
    try:
        # 매수 후 보유 수익 (Buy & Hold Return) - % 값
        print("    (2a/10) '매수 후 보유 수익' 찾는 중...")
        data['buy_hold_return'] = wait.until(
            EC.visibility_of_element_located((By.XPATH, BUY_HOLD_RETURN_ANCHOR_XPATH))
        ).text
        print(f"        -> 찾음: {data['buy_hold_return']}")
        
        # 순이익 (Net Profit) - % 값
        print("    (2b/10) '순이익' 찾는 중...")
        data['net_profit'] = wait.until(
            EC.visibility_of_element_located((By.XPATH, NET_PROFIT_ANCHOR_XPATH))
        ).text
        print(f"        -> 찾음: {data['net_profit']}")
        
    except TimeoutException:
        print("    [오류] '성과' 탭 데이터 로딩 실패 (XPath 확인 필요).")
        data['buy_hold_return'] = 'Scrape Fail'
        data['net_profit'] = 'Scrape Fail'
        
    return data

def scrape_trade_analysis(driver, wait, data):
    """'거래 분석' 탭을 클릭하고 승률, 최대 손실 거래를 파싱합니다."""
    print("    [Sub] '거래 분석' 탭 클릭 시도...")
    wait.until(EC.element_to_be_clickable((By.XPATH, TRADE_ANALYSIS_TAB_XPATH))).click()
    
    try:
        # 승률 (Win Rate)
        print("    (2c/10) '승률' 찾는 중...")
        data['win_rate_pct'] = wait.until(
            EC.visibility_of_element_located((By.XPATH, WIN_RATE_ANCHOR_XPATH))
        ).text
        print(f"        -> 찾음: {data['win_rate_pct']}")
        
        # 최대 손실 거래 (Max Loss Trade)
        print("    (2d/10) '최대 손실 거래' 찾는 중...")
        data['max_loss_trade'] = wait.until(
            EC.visibility_of_element_located((By.XPATH, MAX_LOSS_ANCHOR_XPATH))
        ).text
        print(f"        -> 찾음: {data['max_loss_trade']}")
        
    except TimeoutException:
        print("    [오류] '거래 분석' 탭 데이터 로딩 실패 (XPath 확인 필요).")
        data['win_rate_pct'] = 'Scrape Fail'
        data['max_loss_trade'] = 'Scrape Fail'
        
    return data

def scrape_risk_ratios(driver, wait, data):
    """'위험/성과 비율' 탭을 클릭하고 수익 지수, 샤프, 소티노 비율을 파싱합니다."""
    print("    [Sub] '위험/성과 비율' 탭 클릭 시도...")
    wait.until(EC.element_to_be_clickable((By.XPATH, RISK_RATIOS_TAB_XPATH))).click()
    
    try:
        # 수익 지수 (Profit Factor)
        print("    (2e/10) '수익지수' 찾는 중...")
        data['profit_factor'] = wait.until(
            EC.visibility_of_element_located((By.XPATH, PROFIT_FACTOR_ANCHOR_XPATH))
        ).text
        print(f"        -> 찾음: {data['profit_factor']}")

        # 샤프 비율 (Sharpe Ratio)
        print("    (2f/10) '샤프 레이쇼' 찾는 중...")
        data['sharpe_ratio'] = wait.until(
            EC.visibility_of_element_located((By.XPATH, SHARPE_RATIO_ANCHOR_XPATH))
        ).text
        print(f"        -> 찾음: {data['sharpe_ratio']}")

        # 소티노 비율 (Sortino Ratio)
        print("    (2g/10) '소티노 레이쇼' 찾는 중...")
        data['sortino_ratio'] = wait.until(
            EC.visibility_of_element_located((By.XPATH, SORTINO_RATIO_ANCHOR_XPATH))
        ).text
        print(f"        -> 찾음: {data['sortino_ratio']}")
        
    except TimeoutException:
        print("    [오류] '위험/성과 비율' 탭 데이터 로딩 실패 (XPath 확인 필요).")
        data['profit_factor'] = 'Scrape Fail'
        data['sharpe_ratio'] = 'Scrape Fail'
        data['sortino_ratio'] = 'Scrape Fail'
        
    return data


def get_strategy_data(driver, wait, previous_profit_pct):
    """
    현재 차트의 전략 테스터에서 데이터를 스크래핑합니다. (모든 탭 포함)
    """
    data = {}
    
    try:
        # 0. '개요' 탭이 활성 상태인지 확인 (먼저 클릭해서 보장)
        print("    (0/10) '개요' 탭 클릭 시도...")
        wait.until(EC.element_to_be_clickable((By.XPATH, OVERVIEW_TAB_XPATH))).click()
        print("        -> '개요' 탭 활성화")

        # 0.5. '총손익률' 값이 이전 값과 달라질 때까지 대기
        print("    (0.5/10) '전략 데이터' 로딩 대기중... (값이 바뀔 때까지)")
        wait.until(
            text_to_be_different_from((By.XPATH, PROFIT_PCT_XPATH), previous_profit_pct)
        )
        print("        -> '전략 데이터' 로딩 완료")

        # 1. 개요 탭 데이터 수집 (총손익률)
        print("    (1/10) '총손익률 %' (값) 찾는 중...")
        profit_pct_element = wait.until(
            EC.visibility_of_element_located((By.XPATH, PROFIT_PCT_XPATH))
        )
        data['profit_pct'] = profit_pct_element.text
        print(f"        -> 찾음: {data['profit_pct']}")

        # 2. '성과' 탭 데이터 스크래핑
        data = scrape_performance(driver, wait, data)
        
        # 3. '거래 분석' 탭 스크래핑
        data = scrape_trade_analysis(driver, wait, data)
        
        # 4. '위험/성과 비율' 탭 스크래핑
        data = scrape_risk_ratios(driver, wait, data)

        # 5. '거래목록' 탭 클릭 (시작일을 위해 필요)
        print("    (5/10) '거래 목록' 탭 클릭 시도...")
        wait.until(EC.element_to_be_clickable((By.XPATH, TRADE_LIST_TAB_XPATH))).click()
        print("        -> 클릭 성공")

        # 6. 거래목록 데이터 수집 (1번 거래 진입 시점)
        print("    (6/10) '1번 거래 진입 시점' 찾는 중...")
        trade_1_entry = wait.until(
            EC.visibility_of_element_located((By.XPATH, TRADE_1_ENTRY_XPATH))
        ).text
        data['trade_1_entry'] = trade_1_entry  # 변수 할당 추가
        print(f"        -> 찾음: {data['trade_1_entry']}")

        # 7. 데이터 수집 후 '개요' 탭으로 복귀 (다음 루프를 위해)
        print("    (7/10) '개요' 탭으로 복귀 시도...")
        wait.until(EC.element_to_be_clickable((By.XPATH, OVERVIEW_TAB_XPATH))).click()
        print("        -> 클릭 성공 (데이터 수집 완료)")

        return data

    except TimeoutException as e:
        print(f"    [오류] 위 단계 중 하나에서 타임아웃 발생.")
        print(f"    (참고: 새 종목의 백테스트 결과가 'N/A'이거나 데이터가 없을 수 있습니다.)")
        return None
    except Exception as e:
        # 오류 발생 시 수집된 데이터(data)를 반환하도록 변경
        print(f"    [오류] 예외 발생: {e}")
        return data if data else None

def main():
    # --- ⬇️ 심볼 개수 입력받기 ⬇️ ---
    while True:
        try:
            TOTAL_SYMBOLS_TO_SCRAPE = int(input("수집할 심볼 개수를 입력하세요 (예: 10): "))
            if TOTAL_SYMBOLS_TO_SCRAPE > 0:
                break
            else:
                print("0보다 큰 숫자를 입력하세요.")
        except ValueError:
            print("오류: 유효한 숫자를 입력하세요.")
            
    # --- ⬇️ 기준일 입력받기 ⬇️ ---
    today_str = datetime.now().strftime('%Y-%m-%d')
    while True:
        end_date_input = input(f"기준일(YYYY-MM-DD)을 입력하세요 (기본값: {today_str}): ")
        if not end_date_input: # User pressed Enter
            end_date_obj = datetime.now()
            break
        try:
            end_date_obj = datetime.strptime(end_date_input, '%Y-%m-%d')
            break
        except ValueError:
            print("오류: YYYY-MM-DD 형식이 아닙니다. 다시 입력하세요.")
    
    print(f"기준일이 {end_date_obj.strftime('%Y-%m-%d')}로 설정되었습니다.")
    
    # --- ⬇️ 무기한 대기 입력받기 ⬇️ ---
    driver = webdriver.Chrome(service=webdriver.chrome.service.Service(ChromeDriverManager().install()))
    wait = WebDriverWait(driver, 15) # 요소를 찾을 때까지 최대 15초 대기
    driver.maximize_window()

    chart_url = "https://www.tradingview.com/chart/" 
    driver.get(chart_url)

    print(f"\n--- [SETUP MODE] ---")
    print(f"브라우저가 열렸습니다. 트레이딩뷰에서 다음 작업을 수동으로 완료해주세요:")
    print("1. 로그인 (Login)")
    print("2. 관심종목 목록 열기")
    print("3. 전략 테스터 열기")
    print("\n✅ 준비가 완료되면, **터미널에 'now'를 입력**하세요.")
    
    # 'now'가 입력될 때까지 무기한으로 대기
    while input().strip().lower() != 'now':
        print("잘못된 입력입니다. 'now'를 입력하여 계속하세요.")
    
    print("자동화를 시작합니다.")
    # --- ⬆️ 무기한 대기 입력받기 완료 ⬆️ ---

    collected_data = []
    current_symbol = ""
    last_profit_pct = "" # 이전 총손익률을 기억할 변수

    for i in range(TOTAL_SYMBOLS_TO_SCRAPE):
        print(f"\n--- 심볼 {i+1}/{TOTAL_SYMBOLS_TO_SCRAPE} 수집 시작 ---")
        try:
            # (A) 현재 심볼 이름 가져오기
            print("  (A) 현재 심볼 이름 찾는 중...")
            
            if i > 0:
                print("      다음 심볼 로딩 중... (심볼 이름이 바뀔 때까지 대기)")
                wait.until(
                    text_to_be_different_from(
                        (By.XPATH, SYMBOL_NAME_XPATH), current_symbol
                    )
                )
                print("      로딩 완료.")

            current_symbol_element = wait.until(
                EC.visibility_of_element_located((By.XPATH, SYMBOL_NAME_XPATH))
            )
            current_symbol = current_symbol_element.text
            print(f"      -> 찾음: [{current_symbol}]")

            # (B) 데이터 수집
            print("  (B) 전략 데이터 수집 시작...")
            data = get_strategy_data(driver, wait, last_profit_pct) 
            
            if data:
                data['symbol'] = current_symbol

                # --- ⬇️ 계산 로직 (알파/베타 및 기하 평균 추가) ⬇️ ---
                data['trading_duration_years'] = "N/A"
                data['simple_avg_return_pct'] = "N/A" 
                data['cagr_pct'] = "N/A"              
                data['alpha_beta_status'] = "분석 불가" # 신규 컬럼 기본값
                
                try:
                    # 1. 알파/베타 구분 (순이익 vs 매수 후 보유 수익)
                    net_profit_str = data.get('net_profit', 'N/A')
                    buy_hold_str = data.get('buy_hold_return', 'N/A')
                    
                    print(f"    [디버그] 순이익 원본: '{net_profit_str}'")
                    print(f"    [디버그] 매수후보유 원본: '{buy_hold_str}'")
                    
                    net_profit_float = parse_profit_string(net_profit_str) 
                    buy_hold_float = parse_profit_string(buy_hold_str)
                    
                    print(f"    [디버그] 순이익 파싱: {net_profit_float}")
                    print(f"    [디버그] 매수후보유 파싱: {buy_hold_float}")
                    
                    if net_profit_float is not None and buy_hold_float is not None:
                        if net_profit_float > buy_hold_float:
                            data['alpha_beta_status'] = "알파(α)"
                            print(f"    [디버그] 결과: 알파 (순이익 {net_profit_float} > 매수후보유 {buy_hold_float})")
                        else:
                            data['alpha_beta_status'] = "베타(β)"
                            print(f"    [디버그] 결과: 베타 (순이익 {net_profit_float} <= 매수후보유 {buy_hold_float})")
                    else:
                        print(f"    [디버그] 파싱 실패로 알파/베타 판별 불가")
                    
                    # 2. 거래 기간 및 수익률 계산 (총손익률 기준)
                    profit_pct_str = data['profit_pct']
                    profit_pct_float = float(profit_pct_str.replace('+', '').replace(',', '').replace('%', ''))
                    
                    start_date_str = data['trade_1_entry']
                    # [날짜 파싱 수정] 공백 제거 후 파싱
                    start_date_clean = start_date_str.replace(' ', '')
                    start_date_obj = datetime.strptime(start_date_clean, '%Y년%m월%d일')
                    
                    duration_delta = end_date_obj - start_date_obj
                    duration_years = duration_delta.days / 365.25

                    if duration_years <= 0:
                        data['trading_duration_years'] = "0.0년"
                    else:
                        data['trading_duration_years'] = f"{duration_years:.1f}년"

                        # 3. 연평균 단순 수익률 계산
                        simple_avg_return = profit_pct_float / duration_years
                        data['simple_avg_return_pct'] = f"{simple_avg_return:.2f}%"
                        
                        # 4. 연복리 수익률 (CAGR, 기하 평균) 계산
                        total_return_decimal = profit_pct_float / 100
                        ending_ratio = 1 + total_return_decimal
                        
                        if ending_ratio <= 0:
                            data['cagr_pct'] = "N/A (손실)"
                        else:
                            cagr = (ending_ratio ** (1 / duration_years)) - 1
                            data['cagr_pct'] = f"{cagr * 100:.2f}%"

                except ValueError as e:
                    # 파싱 실패 (값이 'N/A' 또는 '-' 등)
                    print(f"    [정보] 수익률/날짜 파싱 실패. 계산을 건너뜁니다.")
                except Exception as e:
                    # 기타 예외
                    print(f"    [오류] 계산 중 알 수 없는 오류: {e}")
                    data['trading_duration_years'] = "계산 오류"
                    data['simple_avg_return_pct'] = "계산 오류"
                    data['cagr_pct'] = "계산 오류"
                # --- ⬆️ 계산 로직 완료 ⬆️ ---

                collected_data.append(data)
                print(f"  [성공] 데이터: {data}")
                last_profit_pct = data['profit_pct'] # 새 값을 기억
            else:
                print(f"  [정보] 심볼 [{current_symbol}]의 전략 데이터가 없습니다 (N/A).")
                last_profit_pct = "N/A" # 실패/N/A일 경우, 다음 루프를 위해 값을 리셋

            # (C) 다음 심볼로 이동 (데이터 수집 성공/실패와 무관하게)
            print("  (C) 다음 심볼로 이동합니다.")
            body = driver.find_element(By.TAG_NAME, 'body')
            body.send_keys(Keys.ARROW_DOWN)
            time.sleep(0.5)  # 짧은 대기 추가

        except TimeoutException:
            print(f"  [치명적 오류] 심볼 {i+1} 처리 중 타임아웃.")
            print("  (A) 단계에서 SYMBOL_NAME_XPATH 확인이 필요합니다.")
            break
        except Exception as e:
            print(f"  [치명적 오류] 알 수 없는 오류 발생: {e}")
            break

    driver.quit()
    
    print("\n--- 🏁 최종 수집 데이터 ---")
    # 터미널에도 보기 좋게 출력 (JSON 형식)
    print(json.dumps(collected_data, indent=2, ensure_ascii=False))

    # --- ⬇️ 엑셀 파일로 저장 ⬇️ ---
    if collected_data:
        print("\n데이터를 엑셀 파일로 저장 중...")
        try:
            # 1. 데이터를 Pandas DataFrame으로 변환
            df = pd.DataFrame(collected_data)
            
            # 2. (선택) 컬럼 순서 지정
            # 가독성 순서: 심볼 -> 기간/수익률 -> 위험 지표 -> CAGR(최종 결과)
            columns_order = [
                'symbol', 
                'alpha_beta_status',        # 신규 컬럼 추가
                'profit_pct', 
                'trade_1_entry', 
                'trading_duration_years', 
                'simple_avg_return_pct',  
                'win_rate_pct',             
                'max_loss_trade',           
                'profit_factor',            
                'sharpe_ratio',             
                'sortino_ratio',            
                'cagr_pct',                 
                'buy_hold_return',          # 참고용
                'net_profit',               # 참고용
            ]
            # data에 없는 컬럼이 있을 수 있으니, 실제 존재하는 컬럼만 필터링
            final_columns = [col for col in columns_order if col in df.columns]
            df = df[final_columns]
            
            # 3. 컬럼 이름 한글화 (선택 사항)
            df = df.rename(columns={
                'symbol': '종목코드',
                'alpha_beta_status': '수익기준(Alpha/Beta)', # 신규 컬럼 한글화
                'profit_pct': '총손익률(%)',
                'trade_1_entry': '1번거래진입시점',
                'trading_duration_years': '총거래기간(년)',
                'simple_avg_return_pct': '연평균단순수익률(%)',
                'cagr_pct': '연복리수익률(CAGR,%)',
                'win_rate_pct': '승률(%)',
                'max_loss_trade': '최대손실거래(%)',
                'profit_factor': '수익지수',
                'sharpe_ratio': '샤프레이쇼',
                'sortino_ratio': '소티노레이쇼',
                'buy_hold_return': '매수후보유수익(참고)',
                'net_profit': '순이익(참고)'
            })
            
            # 4. 엑셀 파일로 저장
            output_filename = 'tradingview_data.xlsx'
            df.to_excel(output_filename, index=False, engine='openpyxl')
            print(f"'{output_filename}' 파일로 저장 완료.")
            
        except Exception as e:
            print(f"[오류] 엑셀 저장 중 오류 발생: {e}")
            print("JSON으로 대신 저장합니다.")
            # 엑셀 저장이 실패할 경우를 대비해 JSON으로 백업 저장
            with open('tradingview_data_backup.json', 'w', encoding='utf-8') as f:
                json.dump(collected_data, f, indent=2, ensure_ascii=False)

    else:
        print("\n수집된 데이터가 없어 엑셀 파일을 저장하지 않았습니다.")
    # --- ⬆️ 엑셀 저장 완료 ⬆️ ---


if __name__ == "__main__":
    main()