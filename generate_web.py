import os
import pandas as pd
import glob
from datetime import datetime
from pytz import timezone

# 匯入核心組件 (確保這些檔案在同一個資料夾下)
try:
    from pattern_recognizer import PatternRecognizer
    from data_engine import DataEngine
except ImportError as e:
    print(f"❌ 核心組件載入失敗，請確認檔案是否存在: {e}")
    exit(1)

def get_html_template(title, rows, now_str):
    """
    通用 HTML 模板：
    1. 凍結選單 (position: sticky) 方便在手機與電腦上快速導航[cite: 1, 7]。
    2. 移除 target="_blank"，確保所有工具都在原視窗切換，相容手機操作[cite: 7]。
    3. 導覽列包含：型態篩選、全球排行、布林三步曲、外資日報[cite: 1, 7]。
    """
    is_index = "型態篩選" in title
    is_ranking = "排行榜" in title
    
    return f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} - IKE TOOL</title>
        <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
        <style>
            body {{ font-family: "PingFang TC", "Microsoft JhengHei", sans-serif; background: #0d1117; color: #c9d1d9; margin: 0; padding: 0; }}
            
            /* 凍結選單設置[cite: 7] */
            .navbar {{ 
                background: #161b22; 
                padding: 10px 15px; 
                border-bottom: 1px solid #30363d; 
                display: flex; 
                gap: 12px; 
                position: sticky; 
                top: 0; 
                z-index: 1000; 
                align-items: center;
                box-shadow: 0 2px 10px rgba(0,0,0,0.5);
                overflow-x: auto; /* 手機版寬度不足時支援橫向滑動選單 */
                white-space: nowrap;
                -webkit-overflow-scrolling: touch;
            }}
            
            .navbar a {{ color: #c9d1d9; text-decoration: none; font-weight: bold; font-size: 13px; padding: 6px 10px; border-radius: 4px; flex-shrink: 0; transition: 0.2s; }}
            .navbar a:hover {{ background: #30363d; color: #58a6ff; }}
            .navbar a.active {{ color: #58a6ff; border-bottom: 2px solid #58a6ff; border-radius: 0; }}
            
            /* 外部連結樣式區分[cite: 7] */
            .navbar .external-link {{ color: #ffab70; border: 1px solid #ffab7033; }}
            .navbar .external-link:hover {{ background: #ffab7022; }}

            .container {{ max-width: 1250px; margin: 15px auto; padding: 0 15px; }}
            h1 {{ color: #58a6ff; font-size: 22px; margin-top: 5px; }}
            .update-time {{ color: #8b949e; margin-bottom: 15px; font-size: 13px; }}
            
            /* Table 樣式優化：適配手機顯示[cite: 7] */
            table.dataTable {{ background: #161b22 !important; border: 1px solid #30363d !important; border-radius: 8px; }}
            table.dataTable thead th {{ background: #21262d !important; color: #8b949e; font-size: 14px; border-bottom: 1px solid #30363d !important; }}
            table.dataTable tbody td {{ border-bottom: 1px solid #21262d !important; font-size: 14px; }}
            
            .dataTables_wrapper .dataTables_length, .dataTables_wrapper .dataTables_filter, 
            .dataTables_wrapper .dataTables_info, .dataTables_wrapper .dataTables_paginate {{ color: #8b949e !important; padding-top: 15px; font-size: 13px; }}
            input {{ background: #0d1117; border: 1px solid #30363d; color: white; padding: 5px; border-radius: 4px; }}
            
            /* 歷史紀錄面板[cite: 7] */
            #history-panel {{ background: #1c2128; padding: 12px; border-radius: 6px; margin-bottom: 15px; display: none; border: 1px solid #30363d; }}
            .history-item {{ display: inline-block; background: #30363d; padding: 4px 8px; border-radius: 4px; margin: 4px; font-size: 11px; color: #58a6ff; }}
        </style>
    </head>
    <body>
        <div class="navbar">
            <a href="index.html" class="{'active' if is_index else ''}">🎯 型態篩選</a>
            <a href="ranking.html" class="{'active' if is_ranking else ''}">📊 全球排行</a>
            
            <!-- 外部連結：移除 target="_blank"，支援原視窗來回切換[cite: 7] -->
            <a href="https://daniel-chen168.github.io/new11/" class="external-link">📈 布林三步曲</a>
            <a href="https://chiahowu1231-ship-it.github.io/Foreign_point_stock_report/" class="external-link">🏛️ 外資日報</a>
            
            <a href="javascript:void(0)" onclick="toggleHistory()">🕒 紀錄</a>
        </div>

        <div class="container">
            <h1>{title}</h1>
            <div class="update-time">最後更新：{now_str} (台北時間)</div>
            
            <div id="history-panel">
                <strong>最近瀏覽：</strong>
                <div id="history-list">尚無紀錄</div>
            </div>

            <table id="mainTable" class="display" style="width:100%">
                <thead>
                    <tr>
                        <th>代碼</th>
                        <th>名稱</th>
                        <th>現價</th>
                        <th>20MA乖離</th>
                        <th>型態標籤</th>
                        <th>指標細節</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>

        <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
        <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
        <script>
            $(document).ready(function() {{
                $('#mainTable').DataTable({{
                    "order": [[ {2 if not is_index else 4}, "desc" ]],
                    "pageLength": 50,
                    "scrollX": true, // 支援手機橫向滑動表格[cite: 7]
                    "language": {{
                        "search": "搜尋:",
                        "lengthMenu": "_MENU_",
                        "info": "共 _TOTAL_ 筆",
                        "paginate": {{ "next": ">", "previous": "<" }}
                    }},
                    "columnDefs": [{{ "type": "num", "targets": 2 }}]
                }});
                loadHistory();
            }});

            function saveHistory(ticker) {{
                let history = JSON.parse(localStorage.getItem('ike_history') || '[]');
                if(!history.includes(ticker)) {{
                    history.unshift(ticker);
                    if(history.length > 12) history.pop();
                    localStorage.setItem('ike_history', JSON.stringify(history));
                }}
            }}

            function loadHistory() {{
                let history = JSON.parse(localStorage.getItem('ike_history') || '[]');
                if(history.length > 0) {{
                    $('#history-list').html(history.map(t => `<span class="history-item">${{t}}</span>`).join(''));
                }}
            }}

            function toggleHistory() {{ $('#history-panel').toggle(); }}
        </script>
    </body>
    </html>
    """

def generate_web():
    # 統一路徑規範[cite: 1, 7]
    db_path = os.path.normpath("stock_data/1d")
    ticker_file = "ticker_names.txt"
    
    # 1. 載入股票名稱對照表[cite: 1, 7]
    name_map = {}
    if os.path.exists(ticker_file):
        for enc in ['utf-8', 'cp950', 'utf-16']:
            try:
                with open(ticker_file, 'r', encoding=enc, errors='ignore') as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 2: name_map[parts[0]] = parts[1]
                break
            except: continue

    # 2. 掃描所有 Parquet 檔案[cite: 1, 7]
    all_stocks = []
    files = glob.glob(os.path.join(db_path, "*.parquet"))
    print(f"📡 正在處理 {len(files)} 檔數據...")

    for f in files:
        try:
            df = pd.read_parquet(f)
            if df.empty or len(df) < 20: continue
            
            clean_name = os.path.basename(f).replace(".parquet", "")
            base = clean_name.split('_')
            ticker = f"{base[0]}.{base[1]}" if len(base) > 1 else base[0]
            
            engine = DataEngine(ticker)
            engine.df = df
            engine.add_indicators()
            engine.df.dropna(subset=['MA20', '10MA', 'MA5'], inplace=True)
            
            if engine.df.empty: continue
            
            last_close = float(engine.df['Close'].iloc[-1])
            if pd.isna(last_close): continue

            # 執行型態辨識[cite: 3, 7]
            analysis = PatternRecognizer.find_triangle_lines(engine.df)
            
            all_stocks.append({
                'ticker': ticker,
                'name': name_map.get(ticker, "未知"),
                'price': last_close,
                'stars': analysis['stars'],
                'status': analysis['status'],
                'details': analysis['details'],
                'bias': analysis['bias20']
            })
        except: continue

    # 3. 準備生成網頁[cite: 7]
    taipei_tz = timezone('Asia/Taipei')
    now_str = datetime.now(taipei_tz).strftime("%Y-%m-%d %H:%M:%S")

    def build_rows(data_list):
        html_rows = ""
        for s in data_list:
            short_ticker = s['ticker'].split('.')[0]
            histock_url = f"https://histock.tw/stock/{short_ticker}"
            star_str = "⭐" * s['stars']
            bias_color = "#f85149" if s['bias'] > 10 else "#3fb950" if s['bias'] < -5 else "#c9d1d9"
            
            html_rows += f"""
            <tr>
                <td><a href="{histock_url}" class="stock-link" data-ticker="{s['ticker']}" style="color: #58a6ff; text-decoration: none;">{s['ticker']} 🔗</a></td>
                <td>{s['name']}</td>
                <td style="text-align: right; font-weight: bold;">{s['price']:.2f}</td>
                <td style="color: {bias_color};">{s['bias']:.1f}%</td>
                <td>{star_str} {s['status']}</td>
                <td style="font-size: 12px; color: #8b949e;">{s['details']}</td>
            </tr>"""
        return html_rows

    # 分類資料[cite: 7]
    screened_list = [s for s in all_stocks if s['stars'] > 0]
    
    # 4. 產出檔案[cite: 7]
    os.makedirs("public", exist_ok=True)
    
    with open("public/index.html", "w", encoding="utf-8") as f:
        f.write(get_html_template("IKE TOOL - 型態篩選精選", build_rows(screened_list), now_str))
        
    with open("public/ranking.html", "w", encoding="utf-8") as f:
        f.write(get_html_template("IKE TOOL - 全市場排行榜", build_rows(all_stocks), now_str))

    print(f"✅ 網頁生成成功！")

if __name__ == "__main__":
    generate_web()
