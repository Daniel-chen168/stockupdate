import os
import threading
from datetime import datetime
from pytz import timezone

from ticker_updater import update_stock_list  #[cite: 4]
from data_downloader import DataDownloader    #[cite: 2]
from generate_web import generate_web          #[cite: 7]

def run_auto_pipeline():
    taipei_tz = timezone('Asia/Taipei')
    print(f"🚀 啟動流水線: {datetime.now(taipei_tz)}")

    # 1. 更新清單[cite: 4]
    update_stock_list()

    # 2. 下載數據[cite: 2]
    downloader = DataDownloader(data_dir="stock_data")
    with open("ticker_names.txt", 'r', encoding='utf-8') as f:
        tickers = [line.split()[0] for line in f if line.strip()]
    
    downloader.download_and_cache_all_raw_data(
        tickers_to_update=tickers,
        stop_flag=threading.Event(),
        force_full_refresh=True
    )

    # 3. 生成網頁[cite: 7]
    generate_web()
    print("✨ 自動化更新完成！")

if __name__ == "__main__":
    run_auto_pipeline()