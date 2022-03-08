from supertrend import supertrend
import pandas as pd
from orders import place_order
import datetime
import pandas_ta as ta
timestamp_string = 'exchange_timestamp'

def trade_strategy(tradefile,tradefile_parser, parser, next, query_cursor, options_data):
    
    put_token = tradefile_parser.get('trades','put_token')
    call_token = tradefile_parser.get('trades','call_token')
    
    if(put_token == 'closed' and call_token == 'closed'):
        return
    
    
    if(put_token == 'closed'):
        option_token = tradefile_parser.get('trades','call_token')
        option_symbol = tradefile_parser.get('trades','call_symbol')
    if(call_token == 'closed'):
        option_token = tradefile_parser.get('trades','put_token')
        option_symbol = tradefile_parser.get('trades','put_symbol')
    
    option_price = float(next[str(option_token)]['last_price'])
    
    query = f"""SELECT * FROM banknifty_option_data WHERE instrument_token = \'{str(option_token)}\' 
    order by date_time desc LIMIT 20
    """
    query_cursor.execute(query)
    columns = ['instrument_token','date_time','Close','High','Low']
    df = pd.DataFrame(query_cursor.fetchall(), columns = columns)
    
    # Convert to list and reverse so the latest time is later
    close = df['Close'].tolist()[::-1]
    high = df['High'].tolist()[::-1]
    low = df['Low'].tolist()[::-1]
    date_time = df['date_time'].tolist()[::-1]
    
    # Add the latest price, high, low data
    high.append(float(parser.get(str(option_token),'high')))
    low.append(float(parser.get(str(option_token),'low')))
    close.append(option_price)
    date_time.append(next[str(option_token)][timestamp_string])
    
    df = pd.DataFrame({'High':high,'Low':low,'Close':close,'Datetime':date_time})
  
    # Get the supertrend Indicator
    # sti = supertrend(df,10,1)
    
    sti = ta.supertrend(df['High'], df['Low'],df['Close'], 10 ,1)
    # trending = sti['Supertrend'].tolist()[-1]
    
    sti.columns = ['value_req', 'not_req', 'not_req1', 'not_req2']
    supertrend_value = sti['value_req'].tolist()[-1]
    
    # if(trending == True):
    #     supertrend_value = sti['Final Lowerband'].tolist()[-1]
    # else:
    #     supertrend_value = sti['Final Upperband'].tolist()[-1]
    
    if(option_price > supertrend_value):
        
        # Sqaure off the option when candle closes above supertrend
        tokens = [option_symbol]
        buy_sell = ['buy']
        strike = tradefile_parser.get('trades','strike')
        
        place_order(tokens, buy_sell, strike, tradefile)
        
        # place a new straddle
        options_df, strike_new = get_tradingsymbol(options_data,next)
        # options_symbols = options_df['tradingsymbol'].tolist()
        place_straddle(options_df,strike_new, "entry",tradefile)
    
    
    return


def get_tradingsymbol(options_data,next):
    """" returns a dataframe with the instruments for which 
    straddle is to be placed based on current
    underlying price"""
    banknifty_token = options_data[options_data['tradingsymbol'] == 'NIFTY BANK']['instrument_token'].values[0]
    print(banknifty_token)

    banknifty_ltp = next[str(banknifty_token)]['last_price']
    
    # Round to the nearest 100
    strike = round(banknifty_ltp,-2)
    
    all_expiries = options_data['expiry'].dropna().unique()
    
    '''
    # In case the run daate is on expiry then data is collected for the nearest
    # and next expiry.
    # But the trades are only run for the nearest expiry
    
    '''
    all_expiries = sorted(all_expiries)
    
    options_symbol = options_data[(options_data['strike'] == strike) & 
                                  (options_data['expiry'] == all_expiries[0])]
    
    return options_symbol , strike


def place_straddle(options_symbols,strike, entry_exit,tradefile):
    
    if(entry_exit == 'entry'):
        buy_sell = ['sell','sell']
    else:
        buy_sell = ['buy', 'buy']
        
    symbols = options_symbols['tradingsymbol'].tolist()
    place_order(symbols,strike,buy_sell,tradefile)
    return


def check_stoploss(tradefile_parser, next, tradefile, next_timestamp):
    
    pe_token = tradefile_parser.get('trades','put_token')
    ce_token = tradefile_parser.get('trades','call_token')
    
    pe_symbol = tradefile_parser.get('trades','put_symbol')
    ce_symbol = tradefile_parser.get('trades','call_symbol')
    
    pe_ltp = next[str(pe_token)]['last_price']
    ce_ltp = next[str(ce_token)]['last_price']
    
    put_price = tradefile_parser.get('trades','put_price')
    call_price = tradefile_parser.get('trades','call_price')
    
    strike = float(tradefile_parser.get('trades','strike'))
    print(pe_ltp,ce_ltp)
    time_now = datetime.datetime.now()
    weekday = time_now.weekday()
    
    banknifty_token = tradefile_parser.get('trades','banknifty_token')
    # print(next.keys())
    banknifty_ltp = float(next[str(banknifty_token)]['last_price'])
    
    if(weekday == 0 or weekday == 4):
        
        if(pe_ltp >= (1.245 * float(put_price))):
            print("buy put")
            place_order([pe_symbol],strike,['buy'],tradefile)
        if(ce_ltp >= (1.245 * float(call_price))):
            print("buy call")
            place_order([ce_symbol],strike,['buy'],tradefile)
    
    if(weekday >=1 and weekday <= 3):
        if(next_timestamp.minute % 5 == 0):
            if(next_timestamp.second == 0):
                if((banknifty_ltp - strike) > 200):
                    print("buy call")
                    place_order([ce_symbol],strike,['buy'],tradefile)
                    
                if((strike - banknifty_ltp) > 200):
                    print("buy put")
                    place_order([pe_symbol],strike,['buy'],tradefile)
            
        print("strategy")
    
    
    return


def exit_position(tradefile_parser,tradefile):
    
    put_symbol = tradefile_parser.get('trades','put_symbol')
    call_symbol = tradefile_parser.get('trades','call_symbol')
    
    option_symbols = []
    buy_sell = []
    if(put_symbol != 'closed'):
        option_symbols.append(put_symbol)
        buy_sell.append("buy")
    if(call_symbol != 'closed'):
        option_symbols.append(call_symbol)
        buy_sell.append("buy")
    strike = tradefile_parser.get('trades','strike')
    # print(option_symbols,strike, buy_sell)
    if(len(option_symbols) > 0):
        place_order(option_symbols,strike,buy_sell,tradefile)
    
    
    return 