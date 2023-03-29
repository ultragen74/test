import pandas as pd
from datetime import date, datetime
import time
import schedule
import yfinance as yf
import os

import logging
from kiteconnect import KiteConnect

#create connection 


from selenium import webdriver
#chrome options class is used to manipulate various properties of Chrome driver
from selenium.webdriver.chrome.options import Options
#waits till the content loads
from selenium.webdriver.support.ui import WebDriverWait
#finds that content
from selenium.webdriver.support import expected_conditions as EC
#find the above condition/conntent by the xpath, id etc.
from selenium.webdriver.common.by import By

#zerodha
from kiteconnect import KiteConnect
from time import sleep
import urllib.parse as urlparse
import pandas as pd

from webdriver_manager.chrome import ChromeDriverManager

import pandas as pd
from datetime import date, datetime
import time
import schedule
import yfinance as yf
import os
import pyotp
import socket
from nsetools import Nse



##  LOGIN  ##
#############
def kite_login():
    #credentials
    api_key = 'obth19en9avgy8g4'
    api_secret = 'nyo1cq15ztpnaseh71kb9ic445n3xy4i'
    account_username = 'BRZ323'
    account_password = 'Ashyashy@34'
    account_two_fa = '002299'

    kite = KiteConnect(api_key=api_key)

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(ChromeDriverManager().install())

    driver.get(kite.login_url())

    #//tagname[@attribute='value']
    #tagname = div,

    #identify login section
    #form = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//div[@class="login-form"]')))
    sleep(5)
    #enter the ID
    driver.find_element("xpath","//input[@type='text']").send_keys(account_username)

    sleep(1)
    #enter the password
    driver.find_element("xpath","//input[@type='password']").send_keys(account_password)
    sleep(5)
    #submit
    driver.find_element("xpath","//button[@type='submit']").click()
    #driver.find_element_by_xpath("//input[@type='submit']").click()


    #sleep for a second so that the page can submit and proceed to upcoming question (2fa) CjUKFIoTARwXkQ%2B
    sleep(1)
    #form = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//div[@class="login-form"]//form')))

    #identify login section for 2fa
    #enter the 2fa code
    #driver.find_element_by_id("pin").send_keys(account_two_fa)


    totp_key = "CAK3ASQDUZOYS2APFIZD6YCU5AGWURVG" 
                #VPXDESRSP7NFEWFRZ5FARZ45XWQ3NOSU
    totp = WebDriverWait(driver, 1).until(lambda x: x.find_element("xpath","//input[@type='text']"))
    authkey = pyotp.TOTP(totp_key)
    totp.send_keys(authkey.now())


    sleep(5)
    #submit
    driver.find_element("xpath","//button[@type='submit']").click()
    #driver.find_element_by_xpath("//input[@type='submit']").click()
    sleep(5)
    current_url = driver.current_url



    driver.close()
    print(current_url)
    parsed = urlparse.urlparse(current_url)
    print("parsed")
    print(parsed)
    request_token = urlparse.parse_qs(parsed.query)['request_token'][0]
    sleep(0)

    data = kite.generate_session(request_token=request_token,api_secret=api_secret)

    kite.set_access_token(data["access_token"])


    print(kite.login_url())
    return kite
##  END LOGIN  ##
#################

##  BUY  ##
#############

def buy(symbol,number_of_shares):
        # Place an order
    try:
        if len(kite.profile()) >0:
            print("session exist")
    except:
        print("Creating New Session.............")
        kite = kite_login()


    try:
        order_id = kite.place_order(tradingsymbol = symbol,
                             exchange  = "NSE",
                             transaction_type = "BUY",
                             quantity = number_of_shares,
                             order_type = "MARKET",
                             variety = "regular",
                             product = "CNC")

        logging.info("Order placed. ID is: {}".format(order_id))
    except Exception as e:
        logging.info("Order placement failed: {}".format(e))
    
    ds = kite.orders()
    df = pd.DataFrame(ds)
    df.drop(df[df['transaction_type'] == 'SELL'].index, inplace = True)
    df["tradingsymbol"] = df['tradingsymbol'].astype(str) + ".NS" 
    df = df[["tradingsymbol","exchange","quantity","average_price","order_timestamp","average_price"]]
    df["flag"] = 1
    df["selling_price"] = 0
    h = df['order_timestamp'].dt.hour
    df = df[h.eq(h.max())]
    print("Just purchased")
    print (df)
    #writing a data into a single file
    analysis_file  =  base_URL + '/test2.csv'

    with open(analysis_file,'a') as f:
        f.write('\n')    
    df.to_csv(analysis_file, mode='a', index=False, header=False, line_terminator='\n')

##  END BUY  ##
###############

##  SELL  ##
#############

def sell(symbol,number_of_stocks):

    try:
        if len(kite.profile()) >0:
            print("session exist")
    except:
        print("Creating New Session.............")
        kite = kite_login()

    # Place an order
    symbol= symbol[:-3]
    try:
        order_id =  kite.place_order(tradingsymbol = symbol,
                             exchange  = "NSE",
                      transaction_type = "SELL",
                              quantity = number_of_stocks,
                            order_type = "MARKET",
                               variety = "regular",
                               product = "CNC")
        logging.info("Order placed. ID is: {}".format(order_id))
    except Exception as e:
        logging.info("Order placement failed: {}".format(e))
    
    ds = kite.orders()
    df = pd.DataFrame(ds)

    df.drop(df[df['transaction_type'] == 'BUY'].index, inplace = True)
    df["tradingsymbol"] = df['tradingsymbol'].astype(str) + ".NS" 
    df = df[["tradingsymbol","exchange","quantity","average_price","order_timestamp","average_price"]]
    df["flag"] = 0
    df["selling_price"] = 0
    h = df['order_timestamp'].dt.hour
    df = df[h.eq(h.max())]
    print("Just Sold")
    print (df)
    #writing a data into a single file
    analysis_file  =  base_URL + '/test2.csv'

    with open(analysis_file,'a') as f:
        f.write('\n')    
    df.to_csv(analysis_file, mode='a', index=False, header=False, line_terminator='\n')


def nse_price(Ticker):
        Ticker = Ticker[:-3]
        nse = Nse()
        # getting quote of the sbin
        current_price = nse.get_quote(Ticker)['lastPrice']
        # printing company name
        print(current_price)
        return current_price

 
def current_price_value(Ticker):
    try:

        stock = yf.Ticker(Ticker) #100
        current_price = stock.info['regularMarketPrice']
        print("current_price")
        print(current_price)
        if current_price == None:
            current_price = nse_price(Ticker)
        return current_price
    
    except:
        Ticker = Ticker[:-3]
        nse = Nse()
        # getting quote of the sbin
        current_price = nse.get_quote(Ticker)['lastPrice']
        # printing company name
        print(current_price)
        return current_price


##  END SELL  ##
############### 

##  FOLLOW ##
#############

def selling_price_val(Ticker):
    
    set_val = 1.5
    current_price = current_price_value(Ticker)
    print("current_price")
    print(current_price) #100
    #++Load file with purchase price
    analysis_file  =  base_URL + '/test2.csv'
    df_data  =  pd.read_csv(analysis_file,delimiter=",", encoding='utf-8')
    print("Reading historical data")
    lst = [Ticker]
    df_data_ticker = df_data.loc[df_data['tradingsymbol'].isin(lst)] 
    if (df_data_ticker.flag == 0).any():
        return
    df_data_ticker['authorised_date'] = pd.to_datetime(df_data_ticker.authorised_date)
    df_data_ticker = df_data_ticker.sort_values(by=['authorised_date'], ascending=False)
    print("Decending order dataframe")
    print(df_data_ticker)
    def listToString(s):
        # initialize an empty string
        str1 = "" 
        # return string  
        return (str1.join(s))

    Ticker = listToString(Ticker)
    print(Ticker)
    purchase_price_1 = df_data_ticker.iloc[[0]]
    print("Most updated row for the ticker")
    print(purchase_price_1)
    #purchase_price= purchase_price_1["average_price"]
    t1_quantity = int(purchase_price_1["t1_quantity"].iloc[0])
    #if df_data_ticker.empty == True:
    #     selling_price =  purchase_price - set_val
    if df_data_ticker.empty == False:
        purchase_value = df_data_ticker['average_price'].iloc[0]
        print("purchased price")
        print(purchase_value)
        if current_price == purchase_value:
            current_pr_lo = 0
        else:
            current_pr_lo  =  current_price - purchase_value #0
        print("difference")
        print(current_pr_lo)
    selling_price = purchase_price_1["selling_price"].iloc[0]
    current_selling_price = purchase_price_1["selling_price"].iloc[0]
       # SET VALUE from percentage 
    set_val_0_50 = (purchase_value/100) * 0.50
    set_val_0_75 = (purchase_value/100) * 0.75
    set_val_0_95 = (purchase_value/100) * 0.95
    set_val_1 =    (purchase_value/100) * 1
    set_val_1_25 = (purchase_value/100) * 1.25
    set_val_1_50 = (purchase_value/100) * 1.50
    set_val_1_75 = (purchase_value/100) * 1.75
    set_val_2 =    (purchase_value/100) * 2  
    set_val_2_25 = (purchase_value/100) * 2.25
    set_val_2_50 = (purchase_value/100) * 2.50
    set_val_2_75 = (purchase_value/100) * 2.75
    set_val_3 =    (purchase_value/100) * 3  
    set_val_3_25 = (purchase_value/100) * 3.25

    if selling_price >= current_price :
        sell(Ticker,t1_quantity)
    else:
        if  current_pr_lo <= 0:
            selling_price = purchase_value - set_val_2 # I am out of loss 2%of PV

        if  (0 < current_pr_lo) and (current_pr_lo <= set_val_0_75) :
            selling_price = purchase_value - set_val_2 # I am out of loss 2%of PV
        
        if  (set_val_0_75 < current_pr_lo) and (current_pr_lo <= set_val_1) :
            selling_price = purchase_value + set_val_0_50 # I am out of loss 2%of PV

        if  (set_val_1 < current_pr_lo) and (current_pr_lo <= set_val_1_25):
            selling_price = purchase_value + set_val_0_75 # I am out of loss %of PV

        if  (set_val_1_25 < current_pr_lo) and (current_pr_lo <= set_val_1_50 ):
            selling_price = purchase_value + set_val_1 # I am in the profit

        if  (set_val_1_50 < current_pr_lo) and (current_pr_lo <= set_val_1_75):
            selling_price = purchase_value + set_val_1_25 # I am in the profit

        if  (set_val_1_75 < current_pr_lo) and (current_pr_lo <= set_val_2):
            selling_price = purchase_value + set_val_1_50 # I am out of profit

        if  (set_val_2 < current_pr_lo) and (current_pr_lo <= set_val_2_25):
            selling_price = purchase_value + set_val_1_75 # I am out of profit

        if  (set_val_2_25 < current_pr_lo) and (current_pr_lo <= set_val_2_50):
            selling_price = purchase_value + set_val_2 # I am out of profit 

        if  (set_val_2_50 < current_pr_lo) and (current_pr_lo <= set_val_2_75):
            selling_price = purchase_value + set_val_2_25 # I am out of profit 

        if  (set_val_2_75 < current_pr_lo) and (current_pr_lo <= set_val_3):
            selling_price = purchase_value + set_val_2_50 # I am out of profit  

        if  (set_val_3 < current_pr_lo) and (current_pr_lo <= set_val_3_25):
            selling_price = purchase_value + set_val_2_75 # I am out of profit 

        if  set_val_3_25 <  current_pr_lo:           #  I am in the profit
            sell(Ticker,t1_quantity)

        if  current_selling_price >= selling_price:
            selling_price = current_selling_price



    ts = time.time()
    last_price = current_price
    authorised_date= datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')   
    tradingsymbol = Ticker
    average_price = purchase_value
    exchange = df_data_ticker['exchange'].iloc[0]
    t1_quantity = df_data_ticker['t1_quantity'].iloc[0]

    lst1 =  [[tradingsymbol,exchange,t1_quantity,average_price,authorised_date,last_price,1,selling_price]]
    print(lst1)
    #df = pd.DataFrame(date_time,Tickers[ticker],purchase_price[ticker],current_price,selling_price,number_of_stocks,columns=['current_time', 'ticker', 'purchase_price','curremt_price','selling_price','number_of_stocks'])
    df = pd.DataFrame(lst1)
    print("dataframe detail",df)
    with open(analysis_file,'a') as f:
        f.write('\n')    
    df.to_csv(analysis_file, mode='a', index=False, header=False, line_terminator='\n')

    
## END FOLLOW ##
################


def is_connected(hostname):
  
  try:
    # see if we can resolve the host name -- tells us if there is
    # a DNS listening
    host = socket.gethostbyname(hostname)
    # connect to the host -- tells us if the host is actually reachable
    s = socket.create_connection((host, 80), 2)
    s.close()
    print("Internet connected")
    return True
  except Exception:
      print("Internet Not working ........")
      pass # we ignore any errors, returning False
  return False

def follow(New_Tickers):    
    REMOTE_SERVER = "one.one.one.one"
    conn_status = is_connected(REMOTE_SERVER)
    while conn_status == False:
        conn_status = is_connected(REMOTE_SERVER)
    #number_of_stocks = 5
    #if number_of_stocks > len(New_Tickers):
    #    main_engine()

    for ticker in range(len(New_Tickers)): 
        print(New_Tickers[ticker]) #GOOG
        selling_price_val(New_Tickers[ticker])


##  MAIN ENGINE ##
##################

if __name__ == '__main__':
    base_URL = os.path.dirname(os.path.realpath(__file__))
    
    def main_engine():
        number_of_stocks = 5
        analysis_file  =  base_URL + '/test2.csv'
        df_data  =  pd.read_csv(analysis_file,delimiter=",", encoding='utf-8')
        Tickers = ["IDFCFIRSTB.NS","NHPC.NS","PRESTIGE.NS","BANDHANBNK.NS"]
        #Tickers = ["SKIPPER.NS"]
        if df_data.empty:
            New_Tickers = Tickers[:number_of_stocks]
            lst_of_symbol_purchased = []
        else:
            df_data_sold = df_data[(df_data['flag'] == 0)]
            lst_of_symbol = df_data_sold['tradingsymbol'].tolist()
            lst_of_symbol = list(set(lst_of_symbol))
            len_lst_of_symbol = len(lst_of_symbol)
            number_of_stocks = number_of_stocks + len_lst_of_symbol
            Tickers = Tickers[:number_of_stocks]
            New_Tickers = list(set(lst_of_symbol)^set(Tickers))
            print(New_Tickers)
            df_data_purchased = df_data[(df_data['flag'] == 1)]
            lst_of_symbol_1 = df_data_purchased['tradingsymbol'].tolist()
            lst_of_symbol_purchased = list(set(lst_of_symbol_1))
            print(lst_of_symbol_purchased)


        #purchase_price=[]
        i = 0
        for w in New_Tickers: # --
            if w not in lst_of_symbol_purchased:
                print(w)
                purchase_price = current_price_value(w)
                print(purchase_price)
                buying_cap = 1000
                number_of_shares = int(buying_cap / purchase_price)
                i = i + 1 
                if number_of_shares > 20:
                    number_of_stocks = 20  
                print(number_of_shares)
                w = w[:-3]
                buy(w,number_of_shares)
        
    ##  END MAIN ENGINE ##
    ######################

        follow(New_Tickers)

    ##  SCHEDULER ##
    ################
        #now = datetime.now()
        #if 9 <= now.hour and 16 >= now.hour:

        schedule.every(2).minutes.do(follow, New_Tickers)
        while True:
            schedule.run_pending()
            time.sleep(1)
               

    main_engine()
    

