import os
import sys
fpath = os.path.abspath(os.path.join(os.path.dirname(__file__), "..","trades"))
sys.path.append(fpath)
fpath = os.path.abspath(os.path.join(os.path.dirname(__file__), "..","publish_database"))
sys.path.append(fpath)
fpath = os.path.abspath(os.path.join(os.path.dirname(__file__), "..","access_config"))
sys.path.append(fpath)

from config import config
from access_token import access_token
import pandas as pd
import numpy as np
from datetime import datetime
import math
import psycopg2
import pandas_ta as ta
def supertrend(df, atr_period, multiplier):
    
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    # calculate ATR
    price_diffs = [high - low, 
                   high - close.shift(), 
                   close.shift() - low]
    true_range = pd.concat(price_diffs, axis=1)
    true_range = true_range.abs().max(axis=1)
    # default ATR calculation in supertrend indicator
    # atr = true_range.ewm(alpha=1/atr_period,min_periods=atr_period).mean() 
    atr = true_range.ewm(atr_period).mean() 
    
    # atr = true_range.rolling(window=atr_period).mean() 
    
    # print([df['Datetime'].tolist(),atr])
    # df['atr'] = df['tr'].rolling(atr_period).mean()
    
    # HL2 is simply the average of high and low prices
    hl2 = (high + low) / 2
    # upperband and lowerband calculation
    # notice that final bands are set to be equal to the respective bands
    final_upperband = upperband = hl2 + (multiplier * atr)
    final_lowerband = lowerband = hl2 - (multiplier * atr)
    
    # initialize Supertrend column to True
    supertrend = [True] * len(df)
    
    for i in range(1, len(df.index)):
        curr, prev = i, i-1
        
        # if current close price crosses above upperband
        if close[curr] > final_upperband[prev]:
            supertrend[curr] = True
        # if current close price crosses below lowerband
        elif close[curr] < final_lowerband[prev]:
            supertrend[curr] = False
        # else, the trend continues
        else:
            supertrend[curr] = supertrend[prev]
            
            # adjustment to the final bands
            if supertrend[curr] == True and final_lowerband[curr] < final_lowerband[prev]:
                final_lowerband[curr] = final_lowerband[prev]
            if supertrend[curr] == False and final_upperband[curr] > final_upperband[prev]:
                final_upperband[curr] = final_upperband[prev]

        # to remove bands according to the trend direction
        if supertrend[curr] == True:
            final_upperband[curr] = np.nan
        else:
            final_lowerband[curr] = np.nan
    
    return pd.DataFrame({
        'Supertrend': supertrend,
        'Final Lowerband': final_lowerband,
        'Final Upperband': final_upperband
    }, index=df.index)
    


if __name__ == "__main__":    
    atr_period = 10
    atr_multiplier = 1.0
    # params = config()
    # 	# high_low = config(section = 'high_low')
    # 	# connect to the PostgreSQL serve
    # connection = psycopg2.connect(**params)
    # connection.autocommit = True

    # 	# cursor object for database
    # cursor = connection.cursor()
    # query = 'SELECT * FROM banknifty_cleaned WHERE instrument_token = \'17385986\' ORDER BY date_time ASC'
    # cursor.execute(query)
    # data = cursor.fetchall()

    # columns = ['instrument_token','Datetime','Close','High','Low','row_number']
    # data = pd.DataFrame(data, columns = columns)
 
    columns = ['index','instrument_token', 'date_time', 'Close', 'High', 'Low']
    extract_1 = pd.read_csv("G:\DS - Competitions and projects\Supertrend_strategy_v1\Supertrend\extract1.csv"  )
    extract_1.columns = columns
    extract_1 = extract_1.iloc[::-1]
    
    sti = ta.supertrend(extract_1['High'], extract_1['Low'],extract_1['Close'], 10 ,1)
    sti.columns = ['value_req', 'ne', 'nee' , 'mee']
    sti['date_time'] = extract_1.date_time
    print(sti['value_req'].tolist()[-1])
    # sti.to_csv('supertrend_ta.csv')
    # supertrend_val = supertrend(extract_1, 10, 1)
    # print(supertrend_val)
    # supertrend_val.to_csv('supertrend_3.csv')
    

