import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from datetime import datetime
import threading
import time
import pandas as pd
import json

# --- Selenium 관련 라이브러리 ---
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# ==================================================================================
# [SECTION 1] 핵심 시스템 (Core System) - 절대 수정 금지
# 설명: 전략 테스터의 데이터를 수집하는 핵심 로직입니다.
# ==================================================================================

# --- ⬇️ Core XPath 변수 ⬇️ ---
PROFIT_PCT_XPATH = "//div[starts-with(@class, 'reportContainerOld-')]//div[starts-with(@class, 'change-') and contains(text(), '%')]"
TRADE_LIST_TAB_XPATH = "//button[@data-overflow-tooltip-text='거래목록']"
OVERVIEW_TAB_XPATH = "//button[@data-overflow-tooltip-text='오버뷰']"
SYMBOL_NAME_XPATH = "//button[@id='header-toolbar-symbol-search']//div[contains(@class, 'js-button-text')]"
TRADE_1_ENTRY_XPATH = "//tr[@data='1']/td[4]//div[@data-part='1']"
PERFORMANCE_TAB_XPATH = "//button[@data-overflow-tooltip-text='성과']"
TRADE_ANALYSIS_TAB_XPATH = "//button[@data-overflow-tooltip-text='거래 분석']"
RISK_RATIOS_TAB_XPATH = "//button[@data-overflow-tooltip-text='위험/성과 비율']"
NET_PROFIT_ANCHOR_XPATH = "//tr[.//div[contains(text(), '순이익')]]//div[starts-with(@class, 'percentValue-')]"
BUY_HOLD_RETURN_ANCHOR_XPATH = "//tr[.//div[contains(text(), '매수 후 보유 수익')]]//div[starts-with(@class, 'percentValue-')]"
WIN_RATE_ANCHOR_XPATH = "//tr[.//div[contains(text(), '승률')]]//div[starts-with(@class, 'value-') and contains(text(), '%')]"
MAX_LOSS_ANCHOR_XPATH = "//tr[.//div[contains(text(), '최대 손실 거래')]]//div[starts-with(@class, 'value-') and contains(text(), '%')]"
PROFIT_FACTOR_ANCHOR_XPATH = "//tr[.//div[contains(text(), '수익지수')]]//div[starts-with(@class, 'value-') and not(contains(text(), '%'))]"
SHARPE_RATIO_ANCHOR_XPATH = "//tr[.//div[contains(text(), '샤프 레이쇼')]]//div[starts-with(@class, 'value-') and not(contains(text(), '%'))]"
SORTINO_RATIO_ANCHOR_XPATH = "//tr[.//div[contains(text(), '소티노 레이쇼')]]//div[starts-with(@class, 'value-') and not(contains(text(), '%'))]"

# --- ⬇️ Core Helper Classes & Functions ⬇️ ---
class text_to_be_different_from:
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
    if not profit_str or profit_str in ['N/A', 'Scrape Fail', '—']: return None
    import re
    match = re.search(r'[+\-−]?[\d,]+\.?\d*%', profit_str)
    if not match: return None
    clean_str = match.group().replace(',', '').replace('%', '').replace('+', '').replace('−', '-').strip()
    try: return float(clean_str)
    except ValueError: return None

def scrape_performance(driver, wait, data):
    try:
        wait.until(EC.element_to_be_clickable((By.XPATH, PERFORMANCE_TAB_XPATH))).click()
        data['buy_hold_return'] = wait.until(EC.visibility_of_element_located((By.XPATH, BUY_HOLD_RETURN_ANCHOR_XPATH))).text
        data['net_profit'] = wait.until(EC.visibility_of_element_located((By.XPATH, NET_PROFIT_ANCHOR_XPATH))).text
    except TimeoutException:
        data['buy_hold_return'] = 'Scrape Fail'; data['net_profit'] = 'Scrape Fail'
    return data

def scrape_trade_analysis(driver, wait, data):
    try:
        wait.until(EC.element_to_be_clickable((By.XPATH, TRADE_ANALYSIS_TAB_XPATH))).click()
        data['win_rate_pct'] = wait.until(EC.visibility_of_element_located((By.XPATH, WIN_RATE_ANCHOR_XPATH))).text
        data['max_loss_trade'] = wait.until(EC.visibility_of_element_located((By.XPATH, MAX_LOSS_ANCHOR_XPATH))).text
    except TimeoutException:
        data['win_rate_pct'] = 'Scrape Fail'; data['max_loss_trade'] = 'Scrape Fail'
    return data

def scrape_risk_ratios(driver, wait, data):
    try:
        wait.until(EC.element_to_be_clickable((By.XPATH, RISK_RATIOS_TAB_XPATH))).click()
        data['profit_factor'] = wait.until(EC.visibility_of_element_located((By.XPATH, PROFIT_FACTOR_ANCHOR_XPATH))).text
        data['sharpe_ratio'] = wait.until(EC.visibility_of_element_located((By.XPATH, SHARPE_RATIO_ANCHOR_XPATH))).text
        data['sortino_ratio'] = wait.until(EC.visibility_of_element_located((By.XPATH, SORTINO_RATIO_ANCHOR_XPATH))).text
    except TimeoutException:
        data['profit_factor'] = 'Scrape Fail'; data['sharpe_ratio'] = 'Scrape Fail'; data['sortino_ratio'] = 'Scrape Fail'
    return data

def get_strategy_data(driver, wait, previous_profit_pct):
    data = {}
    try:
        wait.until(EC.element_to_be_clickable((By.XPATH, OVERVIEW_TAB_XPATH))).click()
        wait.until(text_to_be_different_from((By.XPATH, PROFIT_PCT_XPATH), previous_profit_pct))
        data['profit_pct'] = wait.until(EC.visibility_of_element_located((By.XPATH, PROFIT_PCT_XPATH))).text
        
        data = scrape_performance(driver, wait, data)
        data = scrape_trade_analysis(driver, wait, data)
        data = scrape_risk_ratios(driver, wait, data)
        
        wait.until(EC.element_to_be_clickable((By.XPATH, TRADE_LIST_TAB_XPATH))).click()
        data['trade_1_entry'] = wait.until(EC.visibility_of_element_located((By.XPATH, TRADE_1_ENTRY_XPATH))).text
        
        wait.until(EC.element_to_be_clickable((By.XPATH, OVERVIEW_TAB_XPATH))).click()
        return data
    except:
        return None

# ==================================================================================
# [SECTION 2] 확장 기능 (Extensions) - 사용자 정의 기능
# ==================================================================================
WATCHLIST_TITLE_XPATH = "//div[contains(@class, 'widgetbar-widget-watchlist')]//span[contains(@class, 'titleRow-')]"
DETAILS_FULL_NAME_XPATH = "//a[@data-qa-id='details-element description']"
DETAILS_EXCHANGE_XPATH = "//span[@data-qa-id='details-element exchange']"
DETAILS_PERF_CONTAINER_XPATH = "//div[@data-qa-id='details-element performance']"

def scrape_symbol_details(driver, wait, target_periods):
    details = {'full_name': 'N/A', 'exchange': 'N/A'}
    for p in target_periods: details[f'return_{p}'] = 'N/A'
    try:
        # 종목명 수집
        details['full_name'] = wait.until(EC.visibility_of_element_located((By.XPATH, DETAILS_FULL_NAME_XPATH))).text
        details['exchange'] = wait.until(EC.visibility_of_element_located((By.XPATH, DETAILS_EXCHANGE_XPATH))).text
    except: pass
    try:
        # 수익률 수집
        wait.until(EC.presence_of_element_located((By.XPATH, DETAILS_PERF_CONTAINER_XPATH)))
        for period in target_periods:
            xpath = f"//div[@data-qa-id='details-element performance']//span[text()='{period}']/preceding-sibling::span"
            try: details[f'return_{period}'] = driver.find_element(By.XPATH, xpath).text
            except: pass
    except: pass
    return details

# ==================================================================================
# [GUI Class] 트레이딩뷰 자동화 메인 인터페이스
# ==================================================================================

class TradingViewApp:
    def __init__(self, master):
        self.master = master
        master.title("TradingView Backtest Auto (Final + No.)")
        master.geometry("550x920") 
        
        # --- 제어 변수 ---
        self.is_running = False
        self.is_paused = False
        self.stop_requested = False
        self.start_time = None
        self.driver = None
        self.wait = None
        
        self.login_event = threading.Event()
        self.asset_type_var = tk.IntVar(value=1)
        
        # 폰트 설정
        self.default_font = ('Helvetica', 10)
        self.bold_font = ('Helvetica', 10, 'bold')
        self.title_font = ('Helvetica', 11, 'bold')

        # UI 생성
        self._create_widgets()
        self.update_button_states("ready")
        self.log_system("시스템 준비 완료. (버튼 하단 + 순번 추가)")

    def _create_widgets(self):
        # 1. 설정 섹션 (Top)
        frame_settings = tk.LabelFrame(self.master, text="🛠️ 기본 설정", padx=10, pady=10)
        frame_settings.pack(side="top", padx=10, pady=5, fill="x")

        tk.Label(frame_settings, text="자산 유형:", font=self.bold_font).grid(row=0, column=0, sticky="nw", pady=5)
        frame_radio = tk.Frame(frame_settings)
        frame_radio.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        tk.Radiobutton(frame_radio, text="주식 (Stocks) [1W~1Y]", variable=self.asset_type_var, value=1).pack(anchor="w")
        tk.Radiobutton(frame_radio, text="ETP (ETF/ETN) [1M~5Y]", variable=self.asset_type_var, value=2).pack(anchor="w")

        tk.Label(frame_settings, text="수집 개수:", font=self.bold_font).grid(row=1, column=0, sticky="w", pady=10)
        self.count_entry = tk.Entry(frame_settings, width=10)
        self.count_entry.grid(row=1, column=1, sticky="w", padx=5, pady=10)
        self.count_entry.insert(0, "10")

        tk.Label(frame_settings, text="기준일:", font=self.bold_font).grid(row=2, column=0, sticky="w", pady=5)
        self.date_entry = tk.Entry(frame_settings, width=15)
        self.date_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        self.date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))

        # 2. 정보 표시 섹션 (Top)
        frame_info = tk.LabelFrame(self.master, text="📊 분석 현황", padx=10, pady=10)
        frame_info.pack(side="top", padx=10, pady=5, fill="x")

        # Row 0: 현재 심볼
        tk.Label(frame_info, text="현재 심볼:", font=self.bold_font, fg="gray").grid(row=0, column=0, sticky="w", pady=2)
        self.lbl_current_data = tk.Label(frame_info, text="대기 중...", font=self.bold_font, fg="blue")
        self.lbl_current_data.grid(row=0, column=1, sticky="w", padx=5)

        # Row 1: 현재 종목명
        tk.Label(frame_info, text="종목명:", font=self.bold_font, fg="gray").grid(row=1, column=0, sticky="w", pady=2)
        self.lbl_current_name = tk.Label(frame_info, text="-", font=self.default_font, fg="black")
        self.lbl_current_name.grid(row=1, column=1, sticky="w", padx=5)

        # Row 2: 경과 시간
        tk.Label(frame_info, text="경과 시간:", font=self.bold_font, fg="gray").grid(row=2, column=0, sticky="w", pady=2)
        self.lbl_timer = tk.Label(frame_info, text="00:00:00", font=self.default_font, fg="#e74c3c")
        self.lbl_timer.grid(row=2, column=1, sticky="w", padx=5)
        
        # Row 3: 파일명
        tk.Label(frame_info, text="파일명:", font=self.bold_font, fg="gray").grid(row=3, column=0, sticky="w", pady=2)
        self.lbl_filename = tk.Label(frame_info, text="-", font=self.default_font)
        self.lbl_filename.grid(row=3, column=1, sticky="w", padx=5)

        # Row 4: 진행률 바 (Progress Bar) & 퍼센트 라벨
        tk.Label(frame_info, text="진행률:", font=self.bold_font, fg="gray").grid(row=4, column=0, sticky="w", pady=10)
        
        self.progress = ttk.Progressbar(frame_info, orient="horizontal", length=250, mode="determinate")
        self.progress.grid(row=4, column=1, sticky="w", padx=5, pady=10)
        
        self.lbl_progress_pct = tk.Label(frame_info, text="0%", font=self.bold_font, fg="blue")
        self.lbl_progress_pct.grid(row=4, column=2, sticky="w", padx=5)

        # 3. 제어 버튼 섹션 (★ 수정됨: side="bottom"으로 하단 고정 ★)
        frame_ctrl = tk.LabelFrame(self.master, text="🎮 제어 패널", padx=10, pady=10)
        frame_ctrl.pack(side="bottom", padx=10, pady=5, fill="x")

        frame_top = tk.Frame(frame_ctrl)
        frame_top.pack(fill="x", pady=(0, 5))
        self.btn_start = tk.Button(frame_top, text="▶ 분석 시작", command=self.start_analysis, bg="#2ecc71", fg="white", font=self.title_font, height=2)
        self.btn_start.pack(side="left", fill="x", expand=True, padx=2)
        self.btn_pause = tk.Button(frame_top, text="⏸ 일시정지", command=self.toggle_pause, bg="#f39c12", fg="white", font=self.title_font, height=2)
        self.btn_pause.pack(side="right", fill="x", expand=True, padx=2)

        frame_bot = tk.Frame(frame_ctrl)
        frame_bot.pack(fill="x")
        self.btn_stop_task = tk.Button(frame_bot, text="⏹ 분석 종료 (Save & Stop)", command=self.stop_task, bg="#95a5a6", fg="white", font=self.title_font, height=2)
        self.btn_stop_task.pack(side="left", fill="x", expand=True, padx=2)
        self.btn_exit = tk.Button(frame_bot, text="❌ 프로그램 종료", command=self.exit_program, bg="#c0392b", fg="white", font=self.title_font, height=2)
        self.btn_exit.pack(side="right", fill="x", expand=True, padx=2)

        # 4. 로그 섹션 (★ 수정됨: 남은 공간 채우기 ★)
        frame_logs = tk.Frame(self.master)
        frame_logs.pack(side="top", padx=10, pady=5, fill="both", expand=True)
        
        tk.Label(frame_logs, text="💾 엑셀 저장 기록", font=self.bold_font).pack(anchor="w")
        self.file_log_text = scrolledtext.ScrolledText(frame_logs, height=4, state='disabled', font=('Consolas', 9), fg="green")
        self.file_log_text.pack(fill="x", pady=(0, 10))
        
        tk.Label(frame_logs, text="📜 시스템 로그", font=self.bold_font).pack(anchor="w")
        self.sys_log_text = scrolledtext.ScrolledText(frame_logs, height=8, state='disabled', font=('Consolas', 9))
        self.sys_log_text.pack(fill="both", expand=True)

    # --- UI 기능 함수 ---
    def log_system(self, message):
        self.sys_log_text.config(state='normal')
        self.sys_log_text.insert(tk.END, datetime.now().strftime("[%H:%M:%S] ") + message + "\n")
        self.sys_log_text.see(tk.END)
        self.sys_log_text.config(state='disabled')

    def log_file(self, message):
        self.file_log_text.config(state='normal')
        self.file_log_text.insert(tk.END, datetime.now().strftime("[%H:%M] ") + message + "\n")
        self.file_log_text.see(tk.END)
        self.file_log_text.config(state='disabled')

    def update_timer(self):
        if self.is_running and not self.is_paused:
            elapsed = time.time() - self.start_time
            self.lbl_timer.config(text=time.strftime("%H:%M:%S", time.gmtime(elapsed)))
            self.master.after(1000, self.update_timer)
        elif self.is_paused:
            self.master.after(1000, self.update_timer)

    def update_button_states(self, state):
        if state == "ready":
            self.btn_start.config(state="normal", bg="#2ecc71")
            self.btn_pause.config(state="disabled", bg="#f39c12", text="⏸ 일시정지")
            self.btn_stop_task.config(state="disabled", bg="#95a5a6")
        elif state == "running":
            self.btn_start.config(state="disabled", bg="gray")
            self.btn_pause.config(state="normal", bg="#f39c12", text="⏸ 일시정지")
            self.btn_stop_task.config(state="normal", bg="#e67e22")
        elif state == "paused":
            self.btn_pause.config(state="normal", bg="#27ae60", text="▶ 재개 (Resume)")

    def start_analysis(self):
        # 1. 입력 검증
        try:
            cnt = int(self.count_entry.get())
            if cnt <= 0: raise ValueError
            self.target_count = cnt
        except:
            messagebox.showerror("오류", "심볼 개수를 확인하세요."); return

        self.target_date_str = self.date_entry.get().strip()
        if not self.target_date_str: messagebox.showerror("오류", "기준일을 입력하세요."); return

        # 2. 상태 초기화
        self.is_running = True; self.is_paused = False; self.stop_requested = False
        self.start_time = time.time()
        
        # 프로그래스 바 초기화
        self.progress['maximum'] = self.target_count
        self.progress['value'] = 0
        self.lbl_progress_pct.config(text="0%") # 초기화
        
        self.update_button_states("running")
        self.log_system("=== 분석 시작 ===")
        self.update_timer()
        
        # 3. 스레드 실행
        threading.Thread(target=self.run_selenium_logic, daemon=True).start()

    def toggle_pause(self):
        if not self.is_running: return
        if self.is_paused:
            self.is_paused = False
            self.update_button_states("running")
            self.log_system("▶ 분석 재개")
        else:
            self.is_paused = True
            self.update_button_states("paused")
            self.log_system("⏸ 일시정지됨")

    def stop_task(self):
        if not self.is_running: return
        if messagebox.askyesno("확인", "분석을 중단하고 현재까지의 데이터를 저장하시겠습니까?"):
            self.stop_requested = True
            self.log_system("🛑 중단 요청됨... 현재 작업 완료 후 종료합니다.")

    def exit_program(self):
        if messagebox.askokcancel("종료", "프로그램을 종료하시겠습니까?\n(브라우저도 닫힙니다)"):
            self.stop_requested = True
            if self.driver:
                try: self.driver.quit()
                except: pass
            self.master.destroy()

    def is_driver_alive(self):
        if self.driver is None: return False
        try:
            _ = self.driver.title 
            return True
        except WebDriverException:
            return False

    def show_login_popup(self):
        messagebox.showinfo("알림", "로그인 및 차트 세팅 후 [확인]을 눌러주세요.\n(확인을 눌러야 분석이 시작됩니다)")
        self.login_event.set()

    # --- 핵심 로직 (Core + GUI Feedback) ---
    def run_selenium_logic(self):
        try:
            driver_needs_init = False
            
            # 브라우저 세션 관리
            if not self.is_driver_alive():
                self.log_system("브라우저 실행 중... (New Session)")
                self.driver = webdriver.Chrome(service=webdriver.chrome.service.Service(ChromeDriverManager().install()))
                self.wait = WebDriverWait(self.driver, 15)
                self.driver.maximize_window()
                self.driver.get("https://www.tradingview.com/chart/")
                driver_needs_init = True
            else:
                self.log_system("기존 브라우저 세션을 사용합니다.")

            if driver_needs_init:
                self.log_system("사용자 로그인 대기 중...")
                self.login_event.clear()
                self.master.after(0, self.show_login_popup)
                self.login_event.wait()
                self.log_system("사용자 확인 완료. 분석을 시작합니다.")
                time.sleep(1)

            asset_mode = self.asset_type_var.get()
            if asset_mode == 2: target_periods = ['1M', '3M', 'YTD', '1Y', '3Y', '5Y']
            else: target_periods = ['1W', '1M', '3M', '6M', 'YTD', '1Y']
            
            # 파일명 설정
            try:
                watchlist_title = self.wait.until(EC.visibility_of_element_located((By.XPATH, WATCHLIST_TITLE_XPATH))).text.strip()
                final_filename = f"{watchlist_title}_{self.target_date_str}.xlsx"
            except:
                final_filename = f"TV_Data_{self.target_date_str}.xlsx"
            
            self.master.after(0, lambda: self.lbl_filename.config(text=final_filename))

            collected_data = []
            current_symbol = ""
            last_profit_pct = ""
            end_date_obj = datetime.strptime(self.target_date_str, '%Y-%m-%d')

            # --- 수집 루프 ---
            for i in range(self.target_count):
                # [Step 4] 진행률 및 퍼센트 업데이트
                current_progress = i + 1
                pct = (current_progress / self.target_count) * 100
                self.master.after(0, lambda val=current_progress: self.progress.configure(value=val))
                self.master.after(0, lambda p=pct: self.lbl_progress_pct.config(text=f"{p:.1f}%"))
                
                if self.stop_requested:
                    self.log_system("사용자 요청에 의해 작업 중단.")
                    break
                
                while self.is_paused:
                    time.sleep(0.5)
                    if self.stop_requested: break

                self.log_system(f"[{i+1}/{self.target_count}] 수집 진행 중...")

                try:
                    if not self.is_driver_alive(): raise Exception("브라우저가 닫혔습니다.")

                    # A. 심볼 감지
                    if i > 0:
                        self.wait.until(text_to_be_different_from((By.XPATH, SYMBOL_NAME_XPATH), current_symbol))
                    
                    current_symbol = self.wait.until(EC.visibility_of_element_located((By.XPATH, SYMBOL_NAME_XPATH))).text
                    
                    self.master.after(0, lambda s=current_symbol: self.lbl_current_data.config(text=s))
                    self.master.after(0, lambda: self.lbl_current_name.config(text="가져오는 중..."))

                    # B. 상세 정보
                    details_data = scrape_symbol_details(self.driver, self.wait, target_periods)
                    
                    full_name = details_data.get('full_name', 'N/A')
                    self.master.after(0, lambda n=full_name: self.lbl_current_name.config(text=n))

                    # C. 전략 데이터
                    data = get_strategy_data(self.driver, self.wait, last_profit_pct)

                    if data:
                        data['symbol'] = current_symbol
                        data.update(details_data)
                        
                        # D. 계산 로직
                        data['trading_duration_years'] = "N/A"
                        data['simple_avg_return_pct'] = "N/A"
                        data['cagr_pct'] = "N/A"
                        data['alpha_beta_status'] = "분석 불가"

                        try:
                            net_profit_float = parse_profit_string(data.get('net_profit'))
                            buy_hold_float = parse_profit_string(data.get('buy_hold_return'))
                            if net_profit_float is not None and buy_hold_float is not None:
                                data['alpha_beta_status'] = "알파(α)" if net_profit_float > buy_hold_float else "베타(β)"
                            
                            start_date_obj = datetime.strptime(data['trade_1_entry'].replace(' ', ''), '%Y년%m월%d일')
                            duration = (end_date_obj - start_date_obj).days / 365.25
                            if duration > 0:
                                profit = float(data['profit_pct'].replace('%','').replace(',','').replace('+',''))
                                data['trading_duration_years'] = f"{duration:.1f}년"
                                data['simple_avg_return_pct'] = f"{(profit/duration):.2f}%"
                                ending_ratio = 1 + (profit/100)
                                if ending_ratio > 0: data['cagr_pct'] = f"{((ending_ratio**(1/duration))-1)*100:.2f}%"
                        except Exception as e:
                            self.log_system(f"계산 오류: {e}")

                        collected_data.append(data)
                        last_profit_pct = data['profit_pct']
                        self.log_system(f"  -> 성공: {current_symbol} ({full_name})")
                    else:
                        self.log_system(f"  -> 전략 없음/실패: {current_symbol}")
                        last_profit_pct = "N/A"

                    # E. 다음 종목
                    self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ARROW_DOWN)
                    time.sleep(0.5)

                except Exception as e:
                    self.log_system(f"Error (Index {i}): {e}")
                    if "브라우저가 닫혔습니다" in str(e):
                        self.log_system("⚠️ 브라우저 연결 끊김. 저장 후 종료.")
                        break
            
            # 완료 시 100% 표시 보장
            self.master.after(0, lambda: self.progress.configure(value=self.target_count))
            self.master.after(0, lambda: self.lbl_progress_pct.config(text="100%"))

            # --- 엑셀 저장 ---
            if collected_data:
                self.log_system(f"총 {len(collected_data)}개 데이터 저장 시작...")
                df = pd.DataFrame(collected_data)
                
                # 1. 컬럼 순서 지정
                columns_order = ['symbol', 'full_name', 'exchange']
                columns_order += [f'return_{p}' for p in target_periods]
                columns_order += ['alpha_beta_status', 'profit_pct', 'trade_1_entry', 'trading_duration_years',
                                  'simple_avg_return_pct', 'cagr_pct', 'win_rate_pct', 'max_loss_trade',
                                  'profit_factor', 'sharpe_ratio', 'sortino_ratio', 'buy_hold_return', 'net_profit']
                
                final_columns = [col for col in columns_order if col in df.columns]
                df = df[final_columns]
                
                # 2. 컬럼명 한글 변환
                rename_map = {
                    'symbol': '종목코드', 'full_name': '종목명(Full)', 'exchange': '거래소',
                    'alpha_beta_status': '수익기준(Alpha/Beta)', 'profit_pct': '총손익률(%)',
                    'trade_1_entry': '1번거래진입시점', 'trading_duration_years': '총거래기간(년)',
                    'simple_avg_return_pct': '연평균단순수익률(%)', 'cagr_pct': '연복리수익률(CAGR,%)',
                    'win_rate_pct': '승률(%)', 'max_loss_trade': '최대손실거래(%)',
                    'profit_factor': '수익지수', 'sharpe_ratio': '샤프레이쇼', 'sortino_ratio': '소티노레이쇼',
                    'buy_hold_return': '매수후보유수익(참고)', 'net_profit': '순이익(참고)'
                }
                for p in target_periods:
                    rename_map[f'return_{p}'] = f'{p}(%)'
                
                df = df.rename(columns=rename_map)

                # [★ 추가됨] 3. 가장 오른쪽 열에 추출 순서 번호 매기기 (No.)
                df['No.'] = range(1, len(df) + 1)

                # 저장
                df.to_excel(final_filename, index=False)
                
                total_elapsed = time.time() - self.start_time
                elapsed_str = time.strftime("%H:%M:%S", time.gmtime(total_elapsed))
                
                # 로그에 수집 개수 기록
                log_msg = f"{final_filename} 저장됨 (소요: {elapsed_str}, 수집: {self.target_count}개)"
                self.master.after(0, lambda m=log_msg: self.log_file(m))
                
                self.log_system("모든 작업이 완료되었습니다.")
            else:
                self.log_system("수집된 데이터가 없어 저장하지 않았습니다.")

        except Exception as e:
            self.log_system(f"치명적 오류 발생: {e}")

        finally:
            self.is_running = False
            self.master.after(0, lambda: self.update_button_states("ready"))
            self.master.after(0, lambda: self.lbl_current_data.config(text="대기 (완료)"))
            self.master.after(0, lambda: self.lbl_current_name.config(text="-"))

if __name__ == "__main__":
    root = tk.Tk()
    app = TradingViewApp(root)
    root.mainloop()
