import pandas as pd
import numpy as np
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


    sleep(0)
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
    print(request_token)
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
    symbol_ns = symbol
    df = pd.read_csv("C:/Users/ultragen74/Desktop/HH/test.csv")
    try:

        Active_flag = df.loc[df["tradingsymbol"] ==  symbol, "flag"].iloc[0] 
        if Active_flag == 1:
            return 0
    except:
        pass
    try:
        if len(kite.profile()) >0:
            print("session exist")
    except:
        print("Creating New Session.............")
        kite = kite_login()

    symbol= symbol[:-3]
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
    df["tradingsymbol"] = symbol_ns 
    df = df[["tradingsymbol","exchange","quantity","average_price","order_timestamp"]]
    df["flag"] = 1
    df["selling_price"] = (df["average_price"]/100) * 96
    h = df['order_timestamp'].dt.hour
    df = df[h.eq(h.max())]
    print("Just purchased")
    print (df)
    #writing a data into a single file
    analysis_file  = "C:/Users/ultragen74/Desktop/HH/test.csv"

    with open(analysis_file,'a') as f:
        f.write('\n')    
    df.to_csv(analysis_file, mode='a', index=False, header=False, line_terminator='\n')

    
##  END BUY  ##
###############

##  SELL  ##
#############

def sell(symbol):
    symbol_ns = symbol
    df = pd.read_csv("C:/Users/ultragen74/Desktop/HH/test.csv")
    number_of_stocks = df.loc[df["tradingsymbol"] ==  symbol, "quantity"].iloc[0] 
    Active_flag = df.loc[df["tradingsymbol"] ==  symbol, "flag"].iloc[0] 
    symbol= symbol[:-3]
    if Active_flag == 1:
        try:
            if len(kite.profile()) >0:
                print("session exist")
        except:
            print("Creating New Session.............")
            kite = kite_login()

        # Place an order

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


        df.drop(df[df['tradingsymbol'] == symbol_ns].index, inplace = True)
        analysis_file  = "C:/Users/ultragen74/Desktop/HH/test.csv"
        with open(analysis_file,'w') as f:
            f.write('\n')    
        df.to_csv(analysis_file, mode='w', index=False, header=True, line_terminator='\n')

#tradingsymbol,exchange,quantity,average_price,order_timestamp,flag,selling_price 
#sell("HINDZINC.NS")