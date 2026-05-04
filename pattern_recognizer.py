import os
import pandas as pd
import numpy as np

class PatternRecognizer:
    @staticmethod
    def find_triangle_lines(df):
        """
        核心型態辨識：整合均線糾結、VCP、多頭排列與乖離率計算
        """
        if df is None or len(df) < 60:
            return {'stars': 0, 'status': "數據不足", 'details': "", 'bias20': 0, 'is_bullish_align': False}
        
        last = df.iloc[-1]
        close = last['Close']
        ma5, ma10, ma20 = last['MA5'], last['10MA'], last['MA20']
        
        # 1. 計算 20MA 乖離率 (Bias Rate) - 僅記錄不限制
        bias20 = (close - ma20) / ma20 * 100 if ma20 > 0 else 0
        
        # 2. 計算均線糾結度 (Squeeze Rate)
        ma_list = [ma5, ma10, ma20]
        ma_max, ma_min = max(ma_list), min(ma_list)
        squeeze_rate = (ma_max - ma_min) / ma_min * 100
        
        # 3. VCP 波動收縮偵測 (最近5日 vs 前20日)
        recent_range = (df['High'].tail(5).max() - df['Low'].tail(5).min()) / close
        prev_range = (df['High'].iloc[-25:-5].max() - df['Low'].iloc[-25:-5].min()) / close
        vcp_tightness = recent_range / prev_range if prev_range > 0 else 1
        
        # 4. 強勢多頭排列判定 (股價 > 5MA > 10MA > 20MA)
        is_bullish_align = close > ma5 > ma10 > ma20
        
        # 5. 評分與標籤邏輯
        score = 0
        status_tags = []
        
        if is_bullish_align:
            score += 2
            status_tags.append("多頭排列")
            
        if squeeze_rate < 3:
            score += 2
            status_tags.append("均線糾結")
        elif squeeze_rate < 5:
            status_tags.append("趨勢靠攏")
        
        if vcp_tightness < 0.6:
            score += 1
            status_tags.append("VCP緊實")
            
        # 成交量確認
        vol_ma5 = df['Volume'].tail(5).mean()
        vol_ratio = last['Volume'] / vol_ma5 if vol_ma5 > 0 else 0
        if close > df['High'].iloc[-10:-1].max() and vol_ratio > 1.2:
            score += 1
            status_tags.append("帶量突破")
            
        status_str = f"[{' / '.join(status_tags)}]" if status_tags else "[整理中]"
        details = f"乖離:{bias20:.1f}% | 糾結:{squeeze_rate:.1f}% | 緊實:{vcp_tightness:.2f}"
        
        return {
            'stars': min(score, 5),
            'status': status_str,
            'details': details,
            'is_bullish_align': is_bullish_align,
            'bias20': bias20
        }

class StockScreener:
    def __init__(self, db_dir="stock_data/1d"):
        self.db_dir = db_dir

    def scan_logic(self, file_name):
        # 實際掃描由 GUI 調用 DataEngine 確保數據完整性
        return None
