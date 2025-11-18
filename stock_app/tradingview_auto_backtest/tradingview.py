import time
import json
import pandas as pd  # 엑셀 저장을 위해 추가
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

# --- ⬇️ XPath 변수 (수익지수 제거됨) ⬇️ ---

# 1. '총손익률 %' 값 (검증 완료)
PROFIT_PCT_XPATH = "//div[starts-with(@class, 'reportContainerOld-')]//div[starts-with(@class, 'change-') and contains(text(), '%')]"
# 2. '수익지수' (제거됨)
# 3. '거래 목록' 탭 버튼 (검증 완료)
TRADE_LIST_TAB_XPATH = "//button[@data-overflow-tooltip-text='거래목록']"
# 4. '개요' 탭 버튼 (검증 완료)
OVERVIEW_TAB_XPATH = "//button[@data-overflow-tooltip-text='오버뷰']"
# 5. '1번 거래 진입 시점' (검증 완료)
TRADE_1_ENTRY_XPATH = "//tr[@data='1']/td[4]//div[@data-part='1']"
# 6. '현재 심볼 이름' (검증 완료)
SYMBOL_NAME_XPATH = "//button[@id='header-toolbar-symbol-search']//div[contains(@class, 'js-button-text')]"
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
            # 요소를 찾아서 현재 텍스트를 가져옵니다.
            element_text = driver.find_element(*self.locator).text
            # 현재 텍스트가 이전 텍스트와 다르면 True를 반환
            return element_text != self.text
        except StaleElementReferenceException:
            # 요소가 stale(사라짐) 상태면, 확실히 변경된 것이므로 True
            return True
        except NoSuchElementException:
            # 요소를 아직 찾을 수 없으면 (로딩 중), False를 반환하고 계속 대기
            return False
# --- ⬆️ 커스텀 클래스 추가 완료 ⬆️ ---


def get_strategy_data(driver, wait, previous_profit_pct):
    """
    현재 차트의 전략 테스터에서 데이터를 스크래핑합니다. (수익지수 제거됨)
    """
    data = {}
    try:
        # 0. '개요' 탭이 활성 상태인지 확인 (먼저 클릭해서 보장)
        print("    (0/5) '개요' 탭 클릭 시도...")
        wait.until(EC.element_to_be_clickable((By.XPATH, OVERVIEW_TAB_XPATH))).click()
        print("        -> '개요' 탭 활성화")

        # 0.5. '총손익률' 값이 이전 값과 달라질 때까지 대기
        print("    (0.5/5) '전략 데이터' 로딩 대기중... (값이 바뀔 때까지)")
        wait.until(
            text_to_be_different_from((By.XPATH, PROFIT_PCT_XPATH), previous_profit_pct)
        )
        print("        -> '전략 데이터' 로딩 완료")

        # 1. 개요 탭 데이터 수집
        print("    (1/5) '총손익률 %' (값) 찾는 중...")
        profit_pct_element = wait.until(
            EC.visibility_of_element_located((By.XPATH, PROFIT_PCT_XPATH))
        )
        data['profit_pct'] = profit_pct_element.text
        print(f"        -> 찾음: {data['profit_pct']}")

        # (2/6) '수익지수' 단계 제거됨

        # 2. '거래목록' 탭 클릭
        print("    (2/5) '거래 목록' 탭 클릭 시도...")
        wait.until(EC.element_to_be_clickable((By.XPATH, TRADE_LIST_TAB_XPATH))).click()
        print("        -> 클릭 성공")

        # 3. 거래목록 데이터 수집 (1번 거래 진입 시점)
        print("    (3/5) '1번 거래 진입 시점' 찾는 중...")
        trade_1_entry = wait.until(
            EC.visibility_of_element_located((By.XPATH, TRADE_1_ENTRY_XPATH))
        ).text
        data['trade_1_entry'] = trade_1_entry
        print(f"        -> 찾음: {data['trade_1_entry']}")

        # 4. 데이터 수집 후 '개요' 탭으로 복귀 (다음 루프를 위해)
        print("    (4/5) '개요' 탭으로 복귀 시도...")
        wait.until(EC.element_to_be_clickable((By.XPATH, OVERVIEW_TAB_XPATH))).click()
        print("        -> 클릭 성공 (데이터 수집 완료)")

        return data

    except TimeoutException as e:
        print(f"    [오류] 위 단계 중 하나에서 타임아웃 발생.")
        print(f"    (참고: 새 종목의 백테스트 결과가 'N/A'이거나 데이터가 없을 수 있습니다.)")
        return None
    except Exception as e:
        print(f"    [오류] 예외 발생: {e}")
        return None

def main():
    # --- ⬇️ [수정] 심볼 개수 입력받기 ⬇️ ---
    while True:
        try:
            TOTAL_SYMBOLS_TO_SCRAPE = int(input("수집할 심볼 개수를 입력하세요 (예: 10): "))
            if TOTAL_SYMBOLS_TO_SCRAPE > 0:
                break
            else:
                print("0보다 큰 숫자를 입력하세요.")
        except ValueError:
            print("오류: 유효한 숫자를 입력하세요.")
            
    # --- ⬇️ [수정] 기준일 입력받기 ⬇️ ---
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
    # --- ⬆️ 입력받기 완료 ⬆️ ---

    driver = webdriver.Chrome(service=webdriver.chrome.service.Service(ChromeDriverManager().install()))
    wait = WebDriverWait(driver, 15) # 요소를 찾을 때까지 최대 15초 대기
    driver.maximize_window()

    chart_url = "https://www.tradingview.com/chart/" 
    driver.get(chart_url)

    print(f"브라우저에서 로그인 및 차트 로드를 60초간 기다립니다...")
    print("60초 이내에 [로그인], [관심종목], [전략 테스터]를 모두 수동으로 열어주세요.")
    time.sleep(60) 
    print("자동화를 시작합니다.")

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

                # --- ⬇️ [수정] 계산 로직 (기하 평균 추가) ⬇️ ---
                data['trading_duration_years'] = "N/A" # 기본값을 N/A로 설정
                data['simple_avg_return_pct'] = "N/A" # (이름 변경) 연평균 단순 수익률
                data['cagr_pct'] = "N/A"               # (신규 추가) 연복리 수익률 (기하 평균)
                
                try:
                    # 1. 수익률 파싱 (N/A 확인)
                    profit_pct_str = data['profit_pct']
                    profit_pct_float = float(profit_pct_str.replace('+', '').replace(',', '').replace('%', ''))

                    # 2. 시작 날짜 파싱 (N/A 확인)
                    start_date_str = data['trade_1_entry'] # "1991년 5월 03일"
                    start_date_obj = datetime.strptime(start_date_str, '%Y년 %m월 %d일')

                    # 3. 거래 기간(년) 계산
                    duration_delta = end_date_obj - start_date_obj
                    duration_years = duration_delta.days / 365.25

                    if duration_years <= 0:
                        data['trading_duration_years'] = "0.0년"
                    else:
                        data['trading_duration_years'] = f"{duration_years:.1f}년"

                        # 4. 연평균 단순 수익률 계산 (기존)
                        simple_avg_return = profit_pct_float / duration_years
                        data['simple_avg_return_pct'] = f"{simple_avg_return:.2f}%"
                        
                        # 5. 연복리 수익률 (CAGR, 기하 평균) 계산 (신규)
                        total_return_decimal = profit_pct_float / 100
                        ending_ratio = 1 + total_return_decimal
                        
                        if ending_ratio <= 0:
                            # 100% 이상 손실 시 기하 평균 계산 불가
                            data['cagr_pct'] = "N/A (손실)"
                        else:
                            cagr = (ending_ratio ** (1 / duration_years)) - 1
                            data['cagr_pct'] = f"{cagr * 100:.2f}%"

                except ValueError as e:
                    # 파싱 실패 (값이 'N/A' 또는 '-' 등)
                    print(f"    [정보] 수익률/날짜 파싱 실패. 계산을 건너뜁니다. (값: {profit_pct_str}, {start_date_str})")
                    # data의 값은 "N/A"로 유지됨
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

    # --- ⬇️ [수정] 엑셀 파일로 저장 ⬇️ ---
    if collected_data:
        print("\n데이터를 엑셀 파일로 저장 중...")
        try:
            # 1. 데이터를 Pandas DataFrame으로 변환
            df = pd.DataFrame(collected_data)
            
            # 2. (선택) 컬럼 순서 지정
            columns_order = [
                'symbol', 
                'profit_pct', 
                'trade_1_entry', 
                'trading_duration_years', 
                'simple_avg_return_pct',  # 이름 변경
                'cagr_pct'                  # 신규 추가
            ]
            # data에 없는 컬럼이 있을 수 있으니, 실제 존재하는 컬럼만 필터링
            final_columns = [col for col in columns_order if col in df.columns]
            df = df[final_columns]

            # 3. 엑셀 파일로 저장
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
