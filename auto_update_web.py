import os
import threading
import logging
from datetime import datetime
from pytz import timezone

# 匯入你原本的核心模組
from data_downloader import DataDownloader
from pattern_recognizer import StockScreener
from generate_web import generate_web  # 確保你的 generate_web.py 已包含先前的雙網頁邏輯

def run_auto_pipeline():
    # 設定路徑
    db_path = "stock_data"
    ticker_file = "ticker_names.txt"
    taipei_tz = timezone('Asia/Taipei')
    
    print("="*50)
    print(f"🚀 IKE TOOL 自動化流水線啟動: {datetime.now(taipei_tz).strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)

    # --- 步驟 1: 強制下載全市場數據 ---
    print("\n📥 [Step 1/3] 開始強制下載全市場數據...")
    downloader = DataDownloader(data_dir=db_path)
    
    # 建立一個停止訊號 (原本 downloader 需要的參數)
    stop_flag = threading.Event()
    
    # 讀取股票清單
    name_map = {}
    if os.path.exists(ticker_file):
        with open(ticker_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                p = line.strip().split()
                if len(p) >= 2: name_map[p[0]] = p[1]
    
    tickers = list(name_map.keys())
    
    # 執行強制更新 (force_full_refresh=True 會刪除舊檔重新抓取)
    # 使用你原本 data_downloader.py 中的函式
    status = downloader.download_and_cache_all_raw_data(
        tickers_to_update=tickers,
        stop_flag=stop_flag,
        force_full_refresh=True,
        force_update_tickers=True
    )
    
    if status == "完成":
        print("✅ 數據下載成功。")
    else:
        print(f"⚠️ 下載結束，狀態：{status}")

    # --- 步驟 2 & 3: 執行分析並產出網頁 ---
    # 這裡直接呼叫我們之前寫好的 generate_web.py 邏輯
    print("\n🧠 [Step 2 & 3] 啟動型態辨識並產生更新網頁...")
    try:
        # 這個函式內部會呼叫 DataEngine 補齊 10MA 等指標
        generate_web() 
        print("✅ 網頁更新完畢 (index.html & ranking.html)")
    except Exception as e:
        print(f"❌ 網頁生成失敗: {e}")

    print("\n" + "="*50)
    print(f"✨ 流程全部結束！請檢查 public/ 資料夾。")
    print("="*50)

if __name__ == "__main__":
    run_auto_pipeline()
