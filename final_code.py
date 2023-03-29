import pandas as pd
from backtesting.lib import resample_apply
import numpy as np 
from backtesting import Strategy
from backtesting.lib import crossover
import yfinance as yf
from backtesting import Backtest
from datetime import datetime, date, timedelta
import talib
from th_dict import thrushold_value
import time
import schedule
from Zerodha_automation import buy, sell
import pytz

def download_transform_to_numpy(ticker):
       
        data = yf.download(tickers = ticker, period='2mo',  interval='1h')
        
        #yf.download("POLYCAB.NS", start="2022-01-15", end="2022-02-28",interval='1h')
        return data
    
def get_sma(prices, rate):
    return prices.rolling(rate).mean()

def get_bollinger_bands(prices, rate=20):
    prices = pd.Series(prices)
    sma = get_sma(prices, rate)
    std = prices.rolling(rate).std()
    bollinger_up = sma + std * 1.3 # Calculate top band
    bollinger_down = sma - std * 1.3 # Calculate bottom band
    #area = (bollinger_up/bollinger_down) * 100
    A =  bollinger_up - bollinger_down
    B = (A / bollinger_up ) * 100
    return bollinger_up, bollinger_down

def SM1(data11, n):
    #data11 = 
    data_min = pd.Series(data11).rolling(n).min()
    print("data minimum")
    print(data_min)
    data_max = pd.Series(data11).rolling(n).max()
    print("data maximum")
    print (data_max)
    data_diff = data_max - data_min 
    data_25 =(data_diff/100) * 20
    Not_buying_zone = data_max + data_25
    return Not_buying_zone

def SMA(values, n):
    """
    Return simple moving average of `values`, at
    each step taking into account `n` previous values.
    """
    #print(len(values))
    return pd.Series(values).rolling(n).mean()


def calc_kama(src, length, fastend=0.666, slowend=0.0645):
    src = pd.Series(src)
    diff = abs(src-np.roll(src,1))
    noise = talib.SUM(diff, length)
    noise= np.where(np.isnan(noise),1,noise)
    signal = talib.MOM(src,length)
    signal  = np.where(np.isnan(signal),0,signal)
    efratio = np.where((noise!=0) , (signal/noise), 1)
    efratio = np.round(efratio,2)
    smoothing_constant = pow(efratio*(fastend-slowend)+slowend,2)
    smoothing_constant = pd.Series(smoothing_constant)
    src = pd.Series(src)
    sma = pd.Series(src.rolling(length).mean(), name="SMA")
    kama = []
    for smooth, sma_param, price in zip(
        smoothing_constant.iteritems(), sma.shift().iteritems(), src.iteritems()
    ):
        try:
            kama.append(kama[-1] + smooth[1] * (price[1] - kama[-1]))
        except (IndexError, TypeError):
            if pd.notnull(sma_param[1]):
                kama.append(sma_param[1] + smooth[1] * (price[1] - sma_param[1]))
            else:
                kama.append(None)
    ## apply the kama list to existing index
    kama_s = pd.Series(kama, index=sma.index).round(2)
    #kama_s = savgol_filter(kama, window_length=35, polyorder=2, mode='nearest')
    return kama_s




def dif(data):
    result =[]
    data = pd.Series(data).rolling(10).median()
    for i in range(len(data)):
        if (i == len(data)-1):
            result.append(1)
            break
        if (np.isnan(data[i]).any()):
            result.append(1)
        else:
            result.append(data[i+1] - data[i])

    return result

def area(up, down, n7):
    up = pd.Series(up).rolling(n7).median()
    down = pd.Series(down).rolling(n7).median()
    #mad = lambda x: np.fabs(x - x.mean()).mean()

    #up = up.rolling(n7).apply(mad, raw=True)
    #down = down.rolling(n7).apply(mad, raw=True)
    A =  up - down
    B = (A / up ) * 100
    return B


class SmaCross(Strategy):
    # Define the two MA lags as *class variables*
    # for later optimization


    def init(self):
        tickker = self.data.ticker[-1]
        print (tickker)
        self.n1 = 7
        self.n2 = 14
        self.n3 = 35
        self.n6 = thrushold_value.get(tickker)
        # Precompute the two moving averages
        self.sma1 = self.I(SMA, self.data.Close, self.n1)
        self.sma2 = self.I(SMA, self.data.Close, self.n2)
        self.sma6 = self.I(SMA, self.data.Close, self.n6)
        self.kama = self.I (calc_kama,self.data.Close,self.n3)
        self.dif = self.I(dif, self.kama)
        
    def next(self):
        tickker = self.data.ticker[-1]
        price = self.data.Close[-1]
        df = pd.read_csv("C:/Users/ultragen74/Desktop/HH/test.csv")
        try:
            sp = df.loc[df["tradingsymbol"] ==  tickker, "selling_price"].iloc[0]
            if price > sp:
                sell(tickker)
        except:
            pass
        current_date   = self.data.index[-1]
        exit_time = date(2020, 12, 13)
        flag = 1 #SAVE TOP
        flag1 = 0 #BUYING ZONE len(self.orders)
        flag2 = 0 #SIDEWAYS# len(self.position._Position__broker.closed_trades)
        flag3 = 1 #BUY self.position._Position__broker.orders
        flag4 = 1 #SELL
        flag5 = 1
        flag6 = 1 #SAVE TOP
        if len(self.position._Position__broker.closed_trades) > 0:
            try:

                ep1 = self.closed_trades[-1].exit_price
                if ep1 == None:
                    ep1 = 0
                else:
                    ep = ep1

                exit_time = self.closed_trades[-1].exit_time
                if exit_time == None:
                    exit_time = date(2020, 12, 13)
                else:
                    et = exit_time
            except:
                pass

        if len(self.orders) > 0:
            flag3 = 0
        else:
            flag3 = 1
        
        if len(self.orders) > 0:
            flag4 = 1
        else:
            flag4 = 0
       
        #Flag for Not buying in the top
        try:
            if   (current_date < et + timedelta(days = 5)):
                flag6 = 0
            else:
                flag6 = 1
        except:
            pass
        
          #(ep < price) and Flag for Not buying in the top((current_date > et + timedelta(days = 5)) and (current_date < et + timedelta(days = 10)
        try:
            date_5 = et + timedelta(days = 6)
            date_10 = et + timedelta(days = 15)
            if ( (current_date in range(date_5, date_10)) and (self.dif in range(-0.02, 0.02))):
                flag = 0
            else:
                flag = 1
        except:
            pass
        #Flag for buy in a Zone 
        if (  self.data.Close >= self.kama  or self.sma1 >= self.kama or self.sma2 >=self.kama or self.sma6 >= self.kama):
            flag1 = 1
        else:
            flag1 = 1

        #Flag for not buying in Sideways (-0.01 <= self.dif  <= 0.01)
        if  (self.dif < -0.3):
            flag2 = 0
        else:
            flag2 = 1
        IST = pytz.timezone('Asia/Kolkata')
        time_now = pd.to_datetime(datetime.now(IST).strftime('%Y-%m-%d %H:%M'))
        time_now = time_now - timedelta(minutes = 5)
        #print(time_now)

  
        if (crossover(self.sma1, self.sma6) and (flag == 1) and (flag1 == 1) and (flag2 == 1) and (flag3 == 1) and (flag5 == 1) and  (flag6 == 1) ) or (crossover(self.sma1, self.sma2) and (self.sma1 > self.sma6) and (flag1 == 1) and (flag == 1) and (flag2 == 1) and (flag3 == 1) and (flag5 == 1) and (flag6 == 1)):  
            #self.position.close()
            self.buy(sl = .96 * price)
            if ( time_now <= current_date ):
                print("BUY")
                #SL = (price/100) * 4
                buying_cap = 5000
                number_of_shares = int(buying_cap / price)
                
                if number_of_shares > 10:
                    number_of_shares = 10  
                print(number_of_shares)
                buy(tickker,number_of_shares)

        
        try:
            e_p = self.trades[0].entry_price
            if  crossover(self.sma6, self.sma1) and (price >= e_p) and (flag4 == 1):
                self.position.close()
                if ( time_now <= current_date ):
                    sell(tickker)
                    print("SELL")
        except:
            pass

ticker = [
    "DIXON.NS",
    "JINDALSTEL.NS",
    "FEDERALBNK.NS",
    "HINDZINC.NS",
    "SCHAEFFLER.NS",
    "AIAENG.NS"
          ]
def follow():
    for i in range(len(ticker)): 
        data = download_transform_to_numpy(ticker = ticker[i])
        data.index = pd.to_datetime(data.index.strftime('%Y-%m-%d %H:%M'))
        data["ticker"] = ticker[i]
        #print(data.tail())
        bt = Backtest(data, SmaCross, cash=10_0000, commission=.002)
        stats = bt.run()

schedule.every(10).minutes.do(follow)
while True:
        schedule.run_pending()
        time.sleep(1)      

