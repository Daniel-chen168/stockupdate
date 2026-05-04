import pandas as pd
import requests
import io
import os
import logging # 改用 logging 來記錄過程

# ★★★ 修正點 2：統一檔案名稱為小寫 't' ★★★
OUTPUT_FILENAME = "ticker_names.txt" 
output_path = os.path.join(os.getcwd(), OUTPUT_FILENAME)

TWSE_URL = "https://mopsfin.twse.com.tw/opendata/t187ap03_L.csv"  # 上市
TPEX_URL = "https://mopsfin.twse.com.tw/opendata/t187ap03_O.csv"  # 上櫃

INDUSTRY_MAPPING = {
    '1': '水泥工業', '2': '食品工業', '3': '塑膠工業', '4': '紡織纖維',
    '5': '電機機械', '6': '電器電纜', '7': '化學工業', '8': '生技醫療業',
    '9': '玻璃陶瓷', '10': '造紙工業', '11': '鋼鐵工業', '12': '橡膠工業',
    '13': '汽車工業', '14': '建材營造', '15': '航運業', '16': '觀光餐旅',
    '17': '金融保險業', '18': '貿易百貨', '19': '綜合', '20': '其他',
    '21': '半導體業', '22': '電腦及週邊設備業', '23': '光電業',
    '24': '通信網路業', '25': '電子零組件業', '26': '電子通路業',
    '27': '資訊服務業', '28': '其他電子業', '29': '文化創意業',
    '30': '農業科技業', '31': '電子商務', '32': '油電燃氣業',
    '35': '綠能環保', '36': '數位雲端', '37': '運動休閒', '38': '居家生活',
    '80': '其他', '99': '其他',
}

def get_industry_name(code_or_name: str) -> str:
    key = str(code_or_name).strip()
    if key.isdigit():
        normalized_key = str(int(key))
    else:
        normalized_key = key
    
    if normalized_key in INDUSTRY_MAPPING:
        return INDUSTRY_MAPPING[normalized_key]
    
    if len(key) > 2 and not key.isdigit():
        return key
        
    return f"未分類 ({key})"

def fetch_and_process_ticker_data(url: str, market_suffix: str) -> list[str]:
    logging.info(f"-> 正在下載 {market_suffix} 市場資料...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        response.encoding = 'utf-8'
        data = io.StringIO(response.text)
        df = pd.read_csv(data, dtype={'公司代號': str, '公司簡稱': str, '產業別': str})

        required_columns = ['公司代號', '公司簡稱', '產業別']
        if not all(col in df.columns for col in required_columns):
            logging.error(f"  [錯誤] {market_suffix} CSV 格式不符，缺少必要欄位。")
            return []

        ticker_list = []
        for index, row in df.iterrows():
            ticker_code = str(row['公司代號']).strip()
            stock_name = str(row['公司簡稱']).strip()
            industry_raw = str(row['產業別']).strip()
            industry_name = get_industry_name(industry_raw)
            
            if '.' in ticker_code:
                ticker_code = ticker_code.split('.')[0]
            if not ticker_code or len(ticker_code) < 4:
                continue

            formatted_line = f"{ticker_code}.{market_suffix} {stock_name} {industry_name}"
            ticker_list.append(formatted_line)
        
        logging.info(f"-> {market_suffix} 市場資料處理完成，共取得 {len(ticker_list)} 筆記錄。")
        return ticker_list

    except requests.exceptions.RequestException as e:
        logging.error(f"  [致命錯誤] {market_suffix} 網路請求失敗: {e}")
        return []
    except Exception as e:
        logging.error(f"  [致命錯誤] 處理 {market_suffix} 資料時發生意外錯誤: {e}")
        return []

# ★★★ 修正點 1：將您的 main() 邏輯封裝成可被匯入的函式 ★★★
def update_stock_list():
    """主程式：負責協調下載、合併和儲存，並回傳結果給 UI。"""
    logging.info("-" * 40)
    logging.info(f"開始更新股票清單到 {OUTPUT_FILENAME}")
    
    all_tickers = []
    
    # 處理上市股票 (TWSE)
    twse_list = fetch_and_process_ticker_data(TWSE_URL, "TW")
    if twse_list:
        all_tickers.extend(twse_list)

    # 處理上櫃股票 (TPEx)
    tpex_list = fetch_and_process_ticker_data(TPEX_URL, "TWO")
    if tpex_list:
        all_tickers.extend(tpex_list)

    if not all_tickers:
        message = "所有資料來源下載或處理失敗，更新終止。"
        logging.error(message)
        return False, message

    try:
        # 排序並寫入檔案
        all_tickers.sort()
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(all_tickers))
        
        total_count = len(all_tickers)
        message = f"股票清單更新成功！共 {total_count} 筆資料。"
        logging.info("-" * 40)
        logging.info(f"✅ 成功! 完整清單已儲存至：{output_path}")
        logging.info(f"總計 {total_count} 筆股票資料。")
        logging.info("-" * 40)
        return True, message
        
    except Exception as e:
        message = f"寫入檔案時發生錯誤: {e}"
        logging.error(f"  [致命錯誤] {message}")
        return False, message

# 保留 if __name__ == "__main__" 區塊，讓此檔案也能獨立執行測試
if __name__ == "__main__":
    try:
        import pandas as pd
        import requests
    except ImportError:
        print("🚨 警告: 找不到 'pandas' 或 'requests' 函式庫。")
        print("請先在您的環境中安裝它們，指令：pip install pandas requests")
    else:
        # 設定基本的日誌，以便獨立執行時能看到訊息
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        update_stock_list()
