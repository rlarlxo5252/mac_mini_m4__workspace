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
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

# ==================================================================================
# [SECTION 1] 핵심 시스템 (Core System) - 수정 주의
# 설명: 전략 테스터의 데이터를 수집하는 핵심 로직입니다. 이 영역의 XPath나 로직은 충돌 방지를 위해 보존합니다.
# ==================================================================================

# --- ⬇️ Core XPath 변수 ⬇️ ---
# 1. 메인 탭 및 버튼
PROFIT_PCT_XPATH = "//div[starts-with(@class, 'reportContainerOld-')]//div[starts-with(@class, 'change-') and contains(text(), '%')]"
TRADE_LIST_TAB_XPATH = "//button[@data-overflow-tooltip-text='거래목록']"
OVERVIEW_TAB_XPATH = "//button[@data-overflow-tooltip-text='오버뷰']"
SYMBOL_NAME_XPATH = "//button[@id='header-toolbar-symbol-search']//div[contains(@class, 'js-button-text')]"
TRADE_1_ENTRY_XPATH = "//tr[@data='1']/td[4]//div[@data-part='1']"

# 2. 추가 탭 버튼
PERFORMANCE_TAB_XPATH = "//button[@data-overflow-tooltip-text='성과']"
TRADE_ANALYSIS_TAB_XPATH = "//button[@data-overflow-tooltip-text='거래 분석']"
RISK_RATIOS_TAB_XPATH = "//button[@data-overflow-tooltip-text='위험/성과 비율']"

# 3. 추가 데이터 앵커
NET_PROFIT_ANCHOR_XPATH = "//tr[.//div[contains(text(), '순이익')]]//div[starts-with(@class, 'percentValue-')]"
BUY_HOLD_RETURN_ANCHOR_XPATH = "//tr[.//div[contains(text(), '매수 후 보유 수익')]]//div[starts-with(@class, 'percentValue-')]"

# 거래 분석 탭 데이터
WIN_RATE_ANCHOR_XPATH = "//tr[.//div[contains(text(), '승률')]]//div[starts-with(@class, 'value-') and contains(text(), '%')]"
MAX_LOSS_ANCHOR_XPATH = "//tr[.//div[contains(text(), '최대 손실 거래')]]//div[starts-with(@class, 'value-') and contains(text(), '%')]"

# 위험/성과 비율 탭 데이터
PROFIT_FACTOR_ANCHOR_XPATH = "//tr[.//div[contains(text(), '수익지수')]]//div[starts-with(@class, 'value-') and not(contains(text(), '%'))]"
SHARPE_RATIO_ANCHOR_XPATH = "//tr[.//div[contains(text(), '샤프 레이쇼')]]//div[starts-with(@class, 'value-') and not(contains(text(), '%'))]"
SORTINO_RATIO_ANCHOR_XPATH = "//tr[.//div[contains(text(), '소티노 레이쇼')]]//div[starts-with(@class, 'value-') and not(contains(text(), '%'))]"


# --- ⬇️ Core Helper Classes & Functions ⬇️ ---
class text_to_be_different_from:
    """텍스트가 변경될 때까지 대기하는 커스텀 조건"""
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

def parse_profit_string(profit_str):
    """퍼센트 문자열 파싱"""
    if not profit_str or profit_str in ['N/A', 'Scrape Fail', '—']:
        return None
    import re
    match = re.search(r'[+\-−]?[\d,]+\.?\d*%', profit_str)
    if not match:
        return None
    percent_part = match.group()
    clean_str = percent_part.replace(',', '').replace('%', '').replace('+', '').replace('−', '-').strip()
    if not clean_str or clean_str == '-':
        return None
    try:
        return float(clean_str)
    except ValueError:
        return None 

def scrape_performance(driver, wait, data):
    """'성과' 탭 스크래핑"""
    print("    [Sub] '성과' 탭 클릭 시도...")
    wait.until(EC.element_to_be_clickable((By.XPATH, PERFORMANCE_TAB_XPATH))).click()
    try:
        print("    (2a/10) '매수 후 보유 수익' 찾는 중...")
        data['buy_hold_return'] = wait.until(
            EC.visibility_of_element_located((By.XPATH, BUY_HOLD_RETURN_ANCHOR_XPATH))
        ).text
        print(f"        -> 찾음: {data['buy_hold_return']}")
        
        print("    (2b/10) '순이익' 찾는 중...")
        data['net_profit'] = wait.until(
            EC.visibility_of_element_located((By.XPATH, NET_PROFIT_ANCHOR_XPATH))
        ).text
        print(f"        -> 찾음: {data['net_profit']}")
    except TimeoutException:
        print("    [오류] '성과' 탭 데이터 로딩 실패.")
        data['buy_hold_return'] = 'Scrape Fail'
        data['net_profit'] = 'Scrape Fail'
    return data

def scrape_trade_analysis(driver, wait, data):
    """'거래 분석' 탭 스크래핑"""
    print("    [Sub] '거래 분석' 탭 클릭 시도...")
    wait.until(EC.element_to_be_clickable((By.XPATH, TRADE_ANALYSIS_TAB_XPATH))).click()
    try:
        print("    (2c/10) '승률' 찾는 중...")
        data['win_rate_pct'] = wait.until(
            EC.visibility_of_element_located((By.XPATH, WIN_RATE_ANCHOR_XPATH))
        ).text
        print(f"        -> 찾음: {data['win_rate_pct']}")
        
        print("    (2d/10) '최대 손실 거래' 찾는 중...")
        data['max_loss_trade'] = wait.until(
            EC.visibility_of_element_located((By.XPATH, MAX_LOSS_ANCHOR_XPATH))
        ).text
        print(f"        -> 찾음: {data['max_loss_trade']}")
    except TimeoutException:
        print("    [오류] '거래 분석' 탭 데이터 로딩 실패.")
        data['win_rate_pct'] = 'Scrape Fail'
        data['max_loss_trade'] = 'Scrape Fail'
    return data

def scrape_risk_ratios(driver, wait, data):
    """'위험/성과 비율' 탭 스크래핑"""
    print("    [Sub] '위험/성과 비율' 탭 클릭 시도...")
    wait.until(EC.element_to_be_clickable((By.XPATH, RISK_RATIOS_TAB_XPATH))).click()
    try:
        print("    (2e/10) '수익지수' 찾는 중...")
        data['profit_factor'] = wait.until(
            EC.visibility_of_element_located((By.XPATH, PROFIT_FACTOR_ANCHOR_XPATH))
        ).text
        print(f"        -> 찾음: {data['profit_factor']}")

        print("    (2f/10) '샤프 레이쇼' 찾는 중...")
        data['sharpe_ratio'] = wait.until(
            EC.visibility_of_element_located((By.XPATH, SHARPE_RATIO_ANCHOR_XPATH))
        ).text
        print(f"        -> 찾음: {data['sharpe_ratio']}")

        print("    (2g/10) '소티노 레이쇼' 찾는 중...")
        data['sortino_ratio'] = wait.until(
            EC.visibility_of_element_located((By.XPATH, SORTINO_RATIO_ANCHOR_XPATH))
        ).text
        print(f"        -> 찾음: {data['sortino_ratio']}")
    except TimeoutException:
        print("    [오류] '위험/성과 비율' 탭 데이터 로딩 실패.")
        data['profit_factor'] = 'Scrape Fail'
        data['sharpe_ratio'] = 'Scrape Fail'
        data['sortino_ratio'] = 'Scrape Fail'
    return data

def get_strategy_data(driver, wait, previous_profit_pct):
    """전략 데이터 수집 메인 함수 (Core)"""
    data = {}
    try:
        print("    (0/10) '개요' 탭 클릭 시도...")
        wait.until(EC.element_to_be_clickable((By.XPATH, OVERVIEW_TAB_XPATH))).click()

        print("    (0.5/10) '전략 데이터' 로딩 대기중... (값이 바뀔 때까지)")
        wait.until(
            text_to_be_different_from((By.XPATH, PROFIT_PCT_XPATH), previous_profit_pct)
        )
        
        print("    (1/10) '총손익률 %' (값) 찾는 중...")
        profit_pct_element = wait.until(
            EC.visibility_of_element_located((By.XPATH, PROFIT_PCT_XPATH))
        )
        data['profit_pct'] = profit_pct_element.text
        print(f"        -> 찾음: {data['profit_pct']}")

        data = scrape_performance(driver, wait, data)
        data = scrape_trade_analysis(driver, wait, data)
        data = scrape_risk_ratios(driver, wait, data)

        print("    (5/10) '거래 목록' 탭 클릭 시도...")
        wait.until(EC.element_to_be_clickable((By.XPATH, TRADE_LIST_TAB_XPATH))).click()

        print("    (6/10) '1번 거래 진입 시점' 찾는 중...")
        trade_1_entry = wait.until(
            EC.visibility_of_element_located((By.XPATH, TRADE_1_ENTRY_XPATH))
        ).text
        data['trade_1_entry'] = trade_1_entry
        print(f"        -> 찾음: {data['trade_1_entry']}")

        print("    (7/10) '개요' 탭으로 복귀 시도...")
        wait.until(EC.element_to_be_clickable((By.XPATH, OVERVIEW_TAB_XPATH))).click()

        return data

    except TimeoutException:
        print(f"    [오류] 타임아웃 발생. (백테스트 결과 N/A 가능성)")
        return None
    except Exception as e:
        print(f"    [오류] 예외 발생: {e}")
        return data if data else None

# ==================================================================================
# [SECTION 2] 확장 기능 (Extensions) - 사용자 정의 기능
# 설명: 왓치리스트, 우측 패널 정보 수집 등 사용자의 요청에 의해 추가된 기능들입니다.
# ==================================================================================

# --- ⬇️ Extension XPath ⬇️ ---
WATCHLIST_TITLE_XPATH = "//div[contains(@class, 'widgetbar-widget-watchlist')]//span[contains(@class, 'titleRow-')]"
DETAILS_FULL_NAME_XPATH = "//a[@data-qa-id='details-element description']"
DETAILS_EXCHANGE_XPATH = "//span[@data-qa-id='details-element exchange']"
DETAILS_PERF_CONTAINER_XPATH = "//div[@data-qa-id='details-element performance']"

# --- ⬇️ Extension Functions ⬇️ ---
def scrape_symbol_details(driver, wait, target_periods):
    """
    [확장 기능] 우측 패널에서 종목 풀네임, 거래소, 선택된 기간별 수익률을 수집합니다.
    """
    details = {
        'full_name': 'N/A', 
        'exchange': 'N/A',
    }
    for p in target_periods:
        details[f'return_{p}'] = 'N/A'
    
    # 1. 기본 정보 (Full Name, Exchange)
    try:
        full_name_el = wait.until(EC.visibility_of_element_located((By.XPATH, DETAILS_FULL_NAME_XPATH)))
        details['full_name'] = full_name_el.text
        exchange_el = wait.until(EC.visibility_of_element_located((By.XPATH, DETAILS_EXCHANGE_XPATH)))
        details['exchange'] = exchange_el.text
    except Exception as e:
        print(f"      [오류] 이름/거래소 수집 실패: {e}")

    # 2. 기간별 수익률 (Stocks vs ETP)
    try:
        print("      [상세정보] 기간별 수익률 스캔 중...")
        # 컨테이너 로딩 확인
        wait.until(EC.presence_of_element_located((By.XPATH, DETAILS_PERF_CONTAINER_XPATH)))
        
        for period in target_periods:
            xpath = f"//div[@data-qa-id='details-element performance']//span[text()='{period}']/preceding-sibling::span"
            try:
                val_element = driver.find_element(By.XPATH, xpath)
                details[f'return_{period}'] = val_element.text
            except NoSuchElementException:
                pass # N/A 유지
                
        if target_periods:
            print(f"      [완료] 수익률 수집 완료")
        
    except Exception as e:
        print(f"      [오류] 수익률 섹션 접근 실패: {e}")
        
    return details

# ==================================================================================
# [SECTION 3] 메인 실행 루프 (Main Execution)
# ==================================================================================

def main():
    # 1. 설정 입력
    while True:
        try:
            TOTAL_SYMBOLS_TO_SCRAPE = int(input("수집할 심볼 개수를 입력하세요 (예: 10): "))
            if TOTAL_SYMBOLS_TO_SCRAPE > 0: break
            else: print("0보다 큰 숫자를 입력하세요.")
        except ValueError:
            print("오류: 유효한 숫자를 입력하세요.")
            
    today_str = datetime.now().strftime('%Y-%m-%d')
    while True:
        end_date_input = input(f"기준일(YYYY-MM-DD)을 입력하세요 (기본값: {today_str}): ")
        if not end_date_input:
            end_date_obj = datetime.now()
            end_date_str = today_str
            break
        try:
            end_date_obj = datetime.strptime(end_date_input, '%Y-%m-%d')
            end_date_str = end_date_input
            break
        except ValueError:
            print("오류: YYYY-MM-DD 형식이 아닙니다.")
    
    # [확장 기능] 자산 유형 선택
    print("\n[설정] 수집할 자산 유형을 선택하세요:")
    print("1. 주식 (Stocks) - [1W, 1M, 3M, 6M, YTD, 1Y]")
    print("2. ETP (ETF/ETN) - [1M, 3M, YTD, 1Y, 3Y, 5Y]")
    asset_type_input = input("선택 (엔터 시 기본값 1): ").strip()

    if asset_type_input == '2':
        target_periods = ['1M', '3M', 'YTD', '1Y', '3Y', '5Y']
        asset_mode_name = "ETP"
    else:
        target_periods = ['1W', '1M', '3M', '6M', 'YTD', '1Y']
        asset_mode_name = "주식(Stocks)"
    
    print(f"✅ 모드: {asset_mode_name} | 기준일: {end_date_str}")

    # 2. 브라우저 시작
    driver = webdriver.Chrome(service=webdriver.chrome.service.Service(ChromeDriverManager().install()))
    wait = WebDriverWait(driver, 15)
    driver.maximize_window()
    driver.get("https://www.tradingview.com/chart/")

    print(f"\n--- [SETUP MODE] ---")
    print("1. 로그인 / 2. 왓치리스트 열기 / 3. 우측 정보 패널 확인 / 4. 전략 테스터 열기")
    while input("준비되면 'now' 입력: ").strip().lower() != 'now': pass
    print("자동화 시작...")

    # 3. 왓치리스트 제목 추출 (파일명 생성)
    final_output_filename = "tradingview_data.xlsx"
    try:
        watchlist_title = wait.until(EC.visibility_of_element_located((By.XPATH, WATCHLIST_TITLE_XPATH))).text.strip()
        final_output_filename = f"{watchlist_title}_{end_date_str}.xlsx"
        print(f"✅ 파일명 설정: {final_output_filename}")
    except:
        print("⚠️ 왓치리스트 이름 추출 실패, 기본 파일명 사용.")

    collected_data = []
    current_symbol = ""
    last_profit_pct = ""

    # 4. 데이터 수집 루프
    for i in range(TOTAL_SYMBOLS_TO_SCRAPE):
        print(f"\n--- [{i+1}/{TOTAL_SYMBOLS_TO_SCRAPE}] 수집 시작 ---")
        try:
            # (A) 심볼 감지
            if i > 0:
                wait.until(text_to_be_different_from((By.XPATH, SYMBOL_NAME_XPATH), current_symbol))
            
            current_symbol = wait.until(EC.visibility_of_element_located((By.XPATH, SYMBOL_NAME_XPATH))).text
            print(f"  심볼: [{current_symbol}]")

            # (B) 확장 데이터 수집 (우측 패널)
            details_data = scrape_symbol_details(driver, wait, target_periods)

            # (C) 핵심 데이터 수집 (전략 테스터)
            data = get_strategy_data(driver, wait, last_profit_pct)
            
            if data:
                data['symbol'] = current_symbol
                data.update(details_data) # 확장 데이터 병합

                # (D) 파생 지표 계산 (Alpha/Beta, CAGR 등)
                data['trading_duration_years'] = "N/A"
                data['simple_avg_return_pct'] = "N/A" 
                data['cagr_pct'] = "N/A"              
                data['alpha_beta_status'] = "분석 불가"
                
                try:
                    net_profit_float = parse_profit_string(data.get('net_profit'))
                    buy_hold_float = parse_profit_string(data.get('buy_hold_return'))
                    
                    if net_profit_float is not None and buy_hold_float is not None:
                        data['alpha_beta_status'] = "알파(α)" if net_profit_float > buy_hold_float else "베타(β)"
                    
                    profit_pct_float = float(data['profit_pct'].replace('+', '').replace(',', '').replace('%', ''))
                    start_date_obj = datetime.strptime(data['trade_1_entry'].replace(' ', ''), '%Y년%m월%d일')
                    duration_years = (end_date_obj - start_date_obj).days / 365.25

                    if duration_years > 0:
                        data['trading_duration_years'] = f"{duration_years:.1f}년"
                        data['simple_avg_return_pct'] = f"{(profit_pct_float / duration_years):.2f}%"
                        ending_ratio = 1 + (profit_pct_float / 100)
                        if ending_ratio > 0:
                            data['cagr_pct'] = f"{((ending_ratio ** (1 / duration_years)) - 1) * 100:.2f}%"
                        else:
                            data['cagr_pct'] = "N/A (손실)"
                    else:
                        data['trading_duration_years'] = "0.0년"
                        
                except Exception as e:
                    print(f"    [계산 오류] {e}")

                collected_data.append(data)
                last_profit_pct = data['profit_pct']
            else:
                print(f"  [정보] 전략 데이터 없음 (N/A)")
                last_profit_pct = "N/A"

            # (E) 다음 종목 이동
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ARROW_DOWN)
            time.sleep(0.5)

        except Exception as e:
            print(f"  [치명적 오류] {e}")
            break

    driver.quit()

    # 5. 엑셀 저장
    if collected_data:
        try:
            df = pd.DataFrame(collected_data)
            
            # 컬럼 순서 정의 (Core + Extensions)
            columns_order = ['symbol', 'full_name', 'exchange'] # 기본 정보
            columns_order += [f'return_{p}' for p in ['1W', '1M', '3M', '6M', 'YTD', '1Y', '3Y', '5Y']] # 수익률
            columns_order += ['alpha_beta_status', 'profit_pct', 'trade_1_entry', 'trading_duration_years', 
                              'simple_avg_return_pct', 'win_rate_pct', 'max_loss_trade', 'profit_factor', 
                              'sharpe_ratio', 'sortino_ratio', 'cagr_pct', 'buy_hold_return', 'net_profit'] # 전략 지표
            
            # 실제 존재하는 컬럼만 선택
            final_columns = [col for col in columns_order if col in df.columns]
            df = df[final_columns]
            
            # 한글 컬럼명 매핑
            rename_map = {
                'symbol': '종목코드', 'full_name': '종목명(Full)', 'exchange': '거래소',
                'alpha_beta_status': '수익기준(Alpha/Beta)', 'profit_pct': '총손익률(%)',
                'trade_1_entry': '1번거래진입시점', 'trading_duration_years': '총거래기간(년)',
                'simple_avg_return_pct': '연평균단순수익률(%)', 'cagr_pct': '연복리수익률(CAGR,%)',
                'win_rate_pct': '승률(%)', 'max_loss_trade': '최대손실거래(%)',
                'profit_factor': '수익지수', 'sharpe_ratio': '샤프레이쇼', 'sortino_ratio': '소티노레이쇼',
                'buy_hold_return': '매수후보유수익(참고)', 'net_profit': '순이익(참고)'
            }
            # 수익률 컬럼 한글화 추가
            for p in ['1W', '1M', '3M', '6M', 'YTD', '1Y', '3Y', '5Y']:
                rename_map[f'return_{p}'] = f'{p}(%)'
                
            df = df.rename(columns=rename_map)
            df.to_excel(final_output_filename, index=False, engine='openpyxl')
            print(f"\n💾 저장 완료: {final_output_filename}")
            
        except Exception as e:
            print(f"엑셀 저장 실패: {e}")
            with open('backup_data.json', 'w') as f: json.dump(collected_data, f, default=str)

if __name__ == "__main__":
    main()
