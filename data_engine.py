import pandas as pd
import numpy as np
from scipy.signal import argrelextrema
import logging

class DataEngine:
    def __init__(self, symbol):
        self.symbol = symbol
        self.df = None

    def add_indicators(self):
        """
        計算技術指標，補齊 PatternRecognizer 所需的 10MA
        """
        if self.df is None or self.df.empty:
            return

        # 計算移動平均線 (包含 10MA 以修正 KeyError)
        self.df['MA5'] = self.df['Close'].rolling(window=5).mean()
        self.df['10MA'] = self.df['Close'].rolling(window=10).mean() # 關鍵補位
        self.df['MA20'] = self.df['Close'].rolling(window=20).mean()
        self.df['MA60'] = self.df['Close'].rolling(window=60).mean()

        # 計算 RSI
        delta = self.df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        self.df['RSI'] = 100 - (100 / (1 + rs))

        # 修正 FutureWarning: 使用 bfill() 代替 fillna(method='bfill')
        self.df.bfill(inplace=True)

    def find_extrema(self, order=5):
        """
        尋找區域高低點，產出 Local_Max/Min 數值欄位
        """
        if self.df is None or len(self.df) < (order * 2 + 1):
            return

        # 標記轉折點布林值
        self.df['is_max'] = False
        max_idx = argrelextrema(self.df['High'].values, np.greater, order=order)[0]
        self.df.iloc[max_idx, self.df.columns.get_loc('is_max')] = True

        self.df['is_min'] = False
        min_idx = argrelextrema(self.df['Low'].values, np.less, order=order)[0]
        self.df.iloc[min_idx, self.df.columns.get_loc('is_min')] = True

        # 產出 PatternRecognizer 需要的數值欄位
        self.df['Local_Max'] = np.nan
        self.df['Local_Min'] = np.nan
        self.df.loc[self.df['is_max'], 'Local_Max'] = self.df['High']
        self.df.loc[self.df['is_min'], 'Local_Min'] = self.df['Low']

    def get_latest_data(self):
        if self.df is not None and not self.df.empty:
            return self.df.iloc[-1]
        return None
