import pandas as pd
import requests
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import warnings
import tkinter as tk
from tkinter import ttk

# 경고 메시지 무시
warnings.filterwarnings('ignore', category=FutureWarning)

def set_korean_font():
    """Matplotlib에서 한글 폰트를 자동으로 찾아 설정합니다."""
    try:
        font_list = [f.name for f in fm.fontManager.ttflist]
        priority_list = ['NanumGothic', 'AppleGothic', 'Malgun Gothic', 'Noto Sans KR']
        for font_name in priority_list:
            if font_name in font_list:
                plt.rc('font', family=font_name)
                plt.rcParams['axes.unicode_minus'] = False
                print(f"✅ 한글 폰트 '{font_name}'을(를) 설정했습니다.")
                return
        print("⚠️ 경고: 한글 폰트를 찾지 못했습니다. 그래프의 글자가 깨질 수 있습니다.")
    except Exception as e:
        print(f"⚠️ 경고: 폰트 설정 중 오류가 발생했습니다. ({e})")

def fetch_data_from_web(url_template, start_date_str, end_date_str):
    """(디버깅용) 웹사이트에서 실제로 어떤 내용을 보내주는지 파일로 저장하여 확인합니다."""
    all_dfs = []
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    print("\n데이터 수집을 시작합니다...")
    for i, current_date in enumerate(date_range):
        date_str = current_date.strftime("%Y-%m-%d")
        url = url_template.format(date_str)

        print(f"   - [{i+1}/{len(date_range)}] {date_str} 데이터 확인 중...", end='\r')

        try:
            response = requests.get(url, headers=headers, timeout=10)

            if i == 0 and response.status_code != 200:
                with open("debug_page.html", "w", encoding="utf-8") as f:
                    f.write(response.text)
                print(f"\n\n[알림] 디버깅을 위해 첫 날짜({date_str})의 접속 결과가 'debug_page.html' 파일로 저장되었습니다.")
                print("스크립트 실행 후 이 파일을 열어 내용을 꼭 확인해주세요.\n")

            if response.status_code != 200:
                continue

            tables = pd.read_html(response.text, header=0, encoding='utf-8')
            if tables:
                df = tables[0]
                if '종목명' not in df.columns:
                    continue
                df['날짜'] = pd.to_datetime(date_str)
                all_dfs.append(df)

        except requests.exceptions.RequestException as e:
            print(f"\n   - {date_str} 에서 네트워크 오류 발생: {e}")
            continue
        except Exception:
            continue

    print("\n✅ 데이터 수집 완료!")

    if not all_dfs:
        return pd.DataFrame()
    master_df = pd.concat(all_dfs, ignore_index=True)
    master_df['평가금액(원)'] = pd.to_numeric(master_df['평가금액(원)'].astype(str).str.replace(',', ''), errors='coerce')
    master_df['비중(%)'] = pd.to_numeric(master_df['비중(%)'], errors='coerce')
    master_df.dropna(subset=['종목명', '평가금액(원)', '비중(%)'], inplace=True)
    return master_df

# --- 이하 그래프 및 테이블 함수는 변경 사항 없음 ---
def plot_total_value(df):
    daily_total = df.groupby('날짜')['평가금액(원)'].sum() / 1_000_000_000
    plt.figure(figsize=(12, 6))
    daily_total.plot(kind='line', marker='o', grid=True)
    plt.title('총 평가금액 변화 추이', fontsize=16)
    plt.ylabel('평가금액 (십억원)', fontsize=12)
    plt.xlabel('날짜', fontsize=12)
    plt.tight_layout()

def plot_top_n_weight_change(df, top_n):
    last_day = df['날짜'].max()
    top_n_stocks = df[df['날짜'] == last_day].nlargest(top_n, '비중(%)')['종목명'].tolist()
    pivot_df = df[df['종목명'].isin(top_n_stocks)].pivot_table(index='날짜', columns='종목명', values='비중(%)')
    colors = plt.get_cmap('tab20').colors
    linestyles = ['-', '--', ':', '-.']
    plt.figure(figsize=(12, 7))
    ax = plt.gca()
    for i, column in enumerate(pivot_df.columns):
        color = colors[i % len(colors)]
        linestyle = linestyles[(i // len(colors)) % len(linestyles)]
        pivot_df[column].plot(kind='line', marker='.', ax=ax, grid=True, color=color, linestyle=linestyle, label=column)
    plt.title(f'보유 비중 상위 {top_n}개 종목 비중 변화', fontsize=16)
    plt.ylabel('비중 (%)', fontsize=12)
    plt.xlabel('날짜', fontsize=12)
    plt.legend(title='종목명', bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.tight_layout()

def plot_pie_chart_for_last_day(df):
    last_day = df['날짜'].max()
    last_day_str = last_day.strftime('%Y-%m-%d')
    last_day_data = df[df['날짜'] == last_day]
    top10 = last_day_data.nlargest(10, '비중(%)')
    others_weight = 100 - top10['비중(%)'].sum()
    pie_data = pd.concat([
        top10[['종목명', '비중(%)']].set_index('종목명'),
        pd.DataFrame({'비중(%)': [others_weight]}, index=['기타'])
    ])
    plt.figure(figsize=(10, 10))
    pie_data.plot(kind='pie', y='비중(%)', autopct='%1.1f%%', legend=False, textprops={'fontsize': 10}, ax=plt.gca())
    plt.title(f'{last_day_str} 기준 포트폴리오 구성 (상위 10개 + 기타)', fontsize=16)
    plt.ylabel('')
    plt.tight_layout()

def display_table_in_new_window(df):
    if df['날짜'].nunique() < 2:
        print("\n⚠️ 기간 내 데이터가 하루치밖에 없어 종목 변동을 분석할 수 없습니다.")
        return
    start_date = df['날짜'].min()
    end_date = df['날짜'].max()
    start_df = df[df['날짜'] == start_date].set_index('종목명')
    end_df = df[df['날짜'] == end_date].set_index('종목명')
    all_stocks = set(start_df.index) | set(end_df.index)
    table_data = []
    for stock in all_stocks:
        start_weight = start_df.loc[stock, '비중(%)'] if stock in start_df.index else 0
        end_weight = end_df.loc[stock, '비중(%)'] if stock in end_df.index else 0
        change = end_weight - start_weight
        if start_weight == 0:
            first_appearance_date = df[df['종목명'] == stock]['날짜'].min().strftime('%Y-%m-%d')
            status = f'신규 편입 ({first_appearance_date})'
        elif end_weight == 0:
            status = '편출'
        else:
            status = '비중 변경'
        table_data.append([stock, f"{start_weight:.2f}%", f"{end_weight:.2f}%", f"{change:+.2f}%", status])
    if not table_data:
        print("\nℹ️ 기간 내 종목 변동이 없습니다.")
        return
    root = tk.Tk()
    root.title(f"종목 변동 내역 ({start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')})")
    frame = ttk.Frame(root, padding="10")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    columns = ['종목명', '시작일 비중', '종료일 비중', '비중 변화', '상태']
    tree = ttk.Treeview(frame, columns=columns, show='headings')
    for col in columns:
        tree.heading(col, text=col, command=lambda _col=col: treeview_sort_column(tree, _col, False))
        tree.column(col, width=150, anchor='center')
    for row in table_data:
        tree.insert('', 'end', values=row)
    scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    tree.grid(row=0, column=0, sticky='nsew')
    scrollbar.grid(row=0, column=1, sticky='ns')
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)
    print("\n📜 종목 변동 내역 테이블을 별도 창에 표시합니다.")
    root.mainloop()

def treeview_sort_column(tree, col, reverse):
    try:
        data_list = [(float(tree.set(k, col).replace('%','')), k) for k in tree.get_children('')]
    except (ValueError, AttributeError):
        data_list = [(tree.set(k, col), k) for k in tree.get_children('')]
    data_list.sort(reverse=reverse)
    for index, (val, k) in enumerate(data_list):
        tree.move(k, '', index)
    tree.heading(col, command=lambda: treeview_sort_column(tree, col, not reverse))

# ✨✨✨ [수정된 부분] ETF 목록에 '글로벌탑픽액티브' 추가 ✨✨✨
def main():
    """메인 실행 함수"""
    set_korean_font()

    # ETF 목록 정의
    ETF_LIST = {
        # 글로벌 시리즈
        '1': ("미국나스닥100액티브", "https://timefolioetf.co.kr/m11_view.php?idx=2&cate=&pdfDate={}"),
        '2': ("차이나AI테크액티브", "https://timefolioetf.co.kr/m11_view.php?idx=19&cate=&pdfDate={}"),
        '3': ("글로벌AI인공지능액티브", "https://timefolioetf.co.kr/m11_view.php?idx=6&cate=&pdfDate={}"),
        '4': ("미국S&P500액티브", "https://timefolioetf.co.kr/m11_view.php?idx=5&cate=&pdfDate={}"),
        '5': ("미국배당다우존스액티브", "https://timefolioetf.co.kr/m11_view.php?idx=18&cate=&pdfDate={}"),
        '6': ("글로벌우주테크&방산액티브", "https://timefolioetf.co.kr/m11_view.php?idx=20&cate=&pdfDate={}"),
        '7': ("미국나스닥100채권혼합50액티브", "https://timefolioetf.co.kr/m11_view.php?idx=10&cate=&pdfDate={}"),
        '8': ("글로벌소비트렌드액티브", "https://timefolioetf.co.kr/m11_view.php?idx=8&cate=&pdfDate={}"),
        '9': ("글로벌안티에이징바이오액티브", "https://timefolioetf.co.kr/m11_view.php?idx=9&cate=&pdfDate={}"),
        '10': ("글로벌탑픽액티브", "https://timefolioetf.co.kr/m11_view.php?idx=22&cate=&pdfDate={}"),
        # K 시리즈
        'a': ("K바이오액티브", "https://timefolioetf.co.kr/m11_view.php?idx=13&cate=&pdfDate={}"),
        'b': ("Korea플러스배당액티브", "https://timefolioetf.co.kr/m11_view.php?idx=12&cate=&pdfDate={}"),
        'c': ("코스피액티브", "https://timefolioetf.co.kr/m11_view.php?idx=11&cate=&pdfDate={}"),
        'd': ("코리아밸류업액티브", "https://timefolioetf.co.kr/m11_view.php?idx=15&cate=&pdfDate={}"),
        'e': ("K이노베이션액티브", "https://timefolioetf.co.kr/m11_view.php?idx=17&cate=&pdfDate={}"),
        'f': ("K컬처액티브", "https://timefolioetf.co.kr/m11_view.php?idx=1&cate=&pdfDate={}"),
        'g': ("K신재생에너지액티브", "https://timefolioetf.co.kr/m11_view.php?idx=16&cate=&pdfDate={}")
    }

    print("-" * 50)
    print("Timefolio ETF 포트폴리오 분석기")
    print("-" * 50)

    # --- ETF 선택 메뉴 출력 ---
    print("\n분석할 ETF를 선택하세요.")
    # 글로벌 시리즈와 K 시리즈를 분리하여 정렬 후 출력
    global_series = {k: v for k, v in ETF_LIST.items() if k.isdigit()}
    k_series = {k: v for k, v in ETF_LIST.items() if k.isalpha()}

    print("--- 글로벌 시리즈 ---")
    for key, (name, _) in sorted(global_series.items(), key=lambda item: int(item[0])):
        print(f"  {key}. {name}")

    print("\n--- K 시리즈 (알파벳으로 선택) ---")
    for key, (name, _) in sorted(k_series.items()):
        print(f"  {key}. {name}")


    choice = input("\n>> 선택 (기본값: 1. 미국나스닥100액티브): ") or '1'

    # 선택한 ETF 정보 가져오기 (잘못된 입력 시 기본값 '1'로 설정)
    selected_etf = ETF_LIST.get(choice, ETF_LIST['1'])
    etf_name, url_template = selected_etf

    print(f"\n✅ '{etf_name}'을(를) 선택했습니다.")

    # --- 날짜 및 기타 정보 입력 ---
    today = datetime.now()
    default_start = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    default_end = today.strftime('%Y-%m-%d')
    start_input = input(f"시작일을 입력하세요 (기본값: {default_start}): ") or default_start
    end_input = input(f"종료일을 입력하세요 (기본값: {default_end}): ") or default_end
    top_n_input = input("분석할 보유 비중 상위 종목 개수를 입력하세요 (기본값: 5): ") or "5"
    top_n = int(top_n_input)

    # --- 데이터 수집 및 분석 실행 ---
    data = fetch_data_from_web(url_template, start_input, end_input)

    if data.empty:
        print("\n❌ 분석할 데이터를 찾지 못했습니다. 기간 내에 PDF 자료가 없는 날이 많을 수 있습니다.")
        return

    print("\n📊 분석 그래프를 생성합니다...")
    plot_total_value(data)
    plot_top_n_weight_change(data, top_n)
    plot_pie_chart_for_last_day(data)

    print("✅ 그래프 생성이 완료되었습니다. 이제 테이블 창을 띄웁니다.")
    plt.show(block=False)

    display_table_in_new_window(data)

    print("\n모든 분석 창이 닫혔습니다. 프로그램을 종료합니다.")

if __name__ == "__main__":
    main()