#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  2 16:18:12 2021

@author: Celeste
"""

import time
import hmac
from requests import Request, Session, request
import logging
from collections import defaultdict

#DC_key
API = 'account_1'
API_secret = 'account_2'
my_subaccount_nickname = 'Testing1'


logging.basicConfig(level=logging.INFO,
                        filename='下單紀錄.log',
                        filemode = 'a',
                        datefmt='%Y/%m/%d %H:%M:%S',
                        format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

def set_leverage(leverage):
    
    string = "https://ftx.com/api/account/leverage"
    ts = int((time.time()) * 1000)
    
    body = {
        'leverage' : leverage
    }
    
    request = Request('POST', string, json=body)
    prepared = request.prepare()
    
    signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode()
    if prepared.body:
        signature_payload += prepared.body
    
    signature_payload = signature_payload
    signature = hmac.new(API_secret.encode(),
                         signature_payload, 'sha256').hexdigest()
    
    prepared.headers['FTX-KEY'] = API
    prepared.headers['FTX-SIGN'] = signature
    prepared.headers['FTX-TS'] = str(ts)
    prepared.headers['FTX-SUBACCOUNT'] = my_subaccount_nickname
    session = Session()
    session.send(prepared)

def order(market,side,size,price=None,type1='market'):

    string = "https://ftx.com/api/orders"
    ts = int((time.time()) * 1000)
    
    body = {
            "market": market,
            "side": side,
            "price": price,
            "size": size,
            "type": type1,
            "reduceOnly": False,
            "ioc": False,
            "postOnly": False,
            "clientId": None
    }
    
    request = Request('POST', string, json=body)
    prepared = request.prepare()
    
    signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode()
    if prepared.body:
        signature_payload += prepared.body
    
    signature_payload = signature_payload
    signature = hmac.new(API_secret.encode(),
                         signature_payload, 'sha256').hexdigest()
    
    prepared.headers['FTX-KEY'] = API
    prepared.headers['FTX-SIGN'] = signature
    prepared.headers['FTX-TS'] = str(ts)
    prepared.headers['FTX-SUBACCOUNT'] = my_subaccount_nickname
    session = Session()
    response = session.send(prepared)
    
    result = eval(response.text.replace('true','True').replace('false','False').replace('null','None').encode('utf8'))
    
    logging.info({market:result})
    
    return(result)
        

def history(market=None, start_time=None):
    
    string = "https://ftx.com/api/orders/history"
    ts = int((time.time()) * 1000)
    
    if start_time == None:
        request = Request('GET', string)
    else:
        params={'start_time':start_time}
        request = Request('GET', string, params = params)
        
    prepared = request.prepare()
    
    signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode()
    if prepared.body:
        signature_payload += prepared.body
    
    signature_payload = signature_payload
    signature = hmac.new(API_secret.encode(),
                         signature_payload, 'sha256').hexdigest()
    
    prepared.headers['FTX-KEY'] = API
    prepared.headers['FTX-SIGN'] = signature
    prepared.headers['FTX-TS'] = str(ts)
    prepared.headers['FTX-SUBACCOUNT'] = my_subaccount_nickname
    session = Session()
    response = session.send(prepared)
    
    history_list = eval(response.text.replace('true','True').replace('false','False').replace('null','None').encode('utf8'))['result']
    history_list = list(filter(lambda i: i['avgFillPrice'] != None, history_list))

    
    if market == 'spot':
        spot_history = list(filter(lambda i: i['future'] == None, history_list))
        spot_position = [{'market':order['market'].split('/')[0],
                          'spot_price':order['avgFillPrice'],
                          'spot_size':order['size']} for order in spot_history]
        return(spot_position)
    
    if market == 'future':
        future_history = list(filter(lambda i: i['future'] != None, history_list))
        future_position = [{'market':order['market'].split('-')[0],
                            'future_price':order['avgFillPrice'],
                            'future_size':order['size']} for order in future_history]
        return(future_position)
    
    return(history_list)

def modify_order(open_dict):
    
    from requests import request
    
    for key,value in open_dict.items():
        
        #new price
        url = 'https://ftx.com/api/markets/{}'.format(value)
        response = request("GET", url)
        data = eval(response.text.replace('true','True').replace('false','False').replace('null','None').encode('utf8'))['result']
        price = (data['ask']+data['bid'])/2
        
        #下單
        string = "https://ftx.com/api/orders/{}/modify".format(key)
        ts = int((time.time()) * 1000)
        
        body = {
            "price": price
        }
        
        request1 = Request('POST', string, json = body)
        prepared = request1.prepare()
            
        signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode()
        if prepared.body:
            signature_payload += prepared.body
            
        signature_payload = signature_payload
        signature = hmac.new(API_secret.encode(),
                                 signature_payload, 'sha256').hexdigest()
            
        prepared.headers['FTX-KEY'] = API
        prepared.headers['FTX-SIGN'] = signature
        prepared.headers['FTX-TS'] = str(ts)
        prepared.headers['FTX-SUBACCOUNT'] = my_subaccount_nickname
        session = Session()
        response = session.send(prepared)
        
        result = eval(response.text.replace('true','True').replace('false','False').replace('null','None').encode('utf8'))
        logging.info({value:result})
        
    
        
def open_order(future_name,currency):
        
    string = "https://ftx.com/api/orders"
    ts = int((time.time()) * 1000)
        
    
    request = Request('GET', string)
    prepared = request.prepare()
        
    signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode()
    if prepared.body:
        signature_payload += prepared.body
        
    signature_payload = signature_payload
    signature = hmac.new(API_secret.encode(),
                             signature_payload, 'sha256').hexdigest()
        
    prepared.headers['FTX-KEY'] = API
    prepared.headers['FTX-SIGN'] = signature
    prepared.headers['FTX-TS'] = str(ts)
    prepared.headers['FTX-SUBACCOUNT'] = my_subaccount_nickname
    session = Session()
    response = session.send(prepared)
        
    open_list = eval(response.text.replace('true','True').replace('false','False').replace('null','None').encode('utf8'))['result']

    market_list=[future_name, future_name[:-5]+currency]
    
    open_dict = {item['id']:item['market'] for item in open_list if item['market'] in market_list}
    return(open_dict)

def position(market=False):
            
    string = "https://ftx.com/api/positions"
    ts = int((time.time()) * 1000)
            
        
    request = Request('GET', string)
    prepared = request.prepare()
            
    signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode()
    if prepared.body:
        signature_payload += prepared.body
            
    signature_payload = signature_payload
    signature = hmac.new(API_secret.encode(),
                                 signature_payload, 'sha256').hexdigest()
            
    prepared.headers['FTX-KEY'] = API
    prepared.headers['FTX-SIGN'] = signature
    prepared.headers['FTX-TS'] = str(ts)
    prepared.headers['FTX-SUBACCOUNT'] = my_subaccount_nickname
    session = Session()
    response = session.send(prepared)
            
    position = eval(response.text.replace('true','True').replace('false','False').replace('null','None').encode('utf8'))['result']
    
    position = list(filter(lambda i: i['size'] != 0, position))
    
    if market == False:
        position_list = [{'market':order['future'][:-5],
                          'entry_price':order['entryPrice'],
                          'size':order['size']} for order in position]
    else:
        position_list = [order['future'][:-5] for order in position]
    
    return(position_list)

def get_leverage():
            
    string = "https://ftx.com/api/account"
    ts = int((time.time()) * 1000)
            
        
    request = Request('GET', string)
    prepared = request.prepare()
            
    signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode()
    if prepared.body:
        signature_payload += prepared.body
            
    signature_payload = signature_payload
    signature = hmac.new(API_secret.encode(),
                                 signature_payload, 'sha256').hexdigest()
            
    prepared.headers['FTX-KEY'] = API
    prepared.headers['FTX-SIGN'] = signature
    prepared.headers['FTX-TS'] = str(ts)
    prepared.headers['FTX-SUBACCOUNT'] = my_subaccount_nickname
    session = Session()
    response = session.send(prepared)
            
    leverage = eval(response.text.replace('true','True').replace('false','False').replace('null','None').encode('utf8'))['result']['leverage']
    return(leverage)

def delete_order():
    string = "https://ftx.com/api/orders"
    ts = int((time.time()) * 1000)
    
    request = Request('DELETE', string)
    prepared = request.prepare()
    
    signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode()
    if prepared.body:
        signature_payload += prepared.body
    
    signature_payload = signature_payload
    signature = hmac.new(API_secret.encode(),
                         signature_payload, 'sha256').hexdigest()
    
    prepared.headers['FTX-KEY'] = API
    prepared.headers['FTX-SIGN'] = signature
    prepared.headers['FTX-TS'] = str(ts)
    prepared.headers['FTX-SUBACCOUNT'] = my_subaccount_nickname
    session = Session()
    session.send(prepared)

def filled_orders(start_time=None):
    spot_list = history(market='spot',start_time=start_time)
    future_list = history(market='future',start_time=start_time)
    d = defaultdict(dict)
        
    for l in (spot_list, future_list):
        for elem in l:
            d[elem['market']].update(elem)
    total_list = d.values()
    for elem in total_list:
        try:
            elem.update({'spread':round(elem['future_price']-elem['spot_price'],4),
                         'time':time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(start_time))})
        except:
            pass
        
    return(list(total_list))


def get_close_history(market_name):
    now = time.time()
    string = "https://ftx.com/api/markets/{}/candles".format(market_name)
    ts = int((time.time()) * 1000)
    

    params={'resolution':3600,
            'start_time':now-2592000}
    request = Request('GET', string, params = params)
        
    prepared = request.prepare()
    
    signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode()
    if prepared.body:
        signature_payload += prepared.body
    
    signature_payload = signature_payload
    signature = hmac.new(API_secret.encode(),
                         signature_payload, 'sha256').hexdigest()
    
    prepared.headers['FTX-KEY'] = API
    prepared.headers['FTX-SIGN'] = signature
    prepared.headers['FTX-TS'] = str(ts)
    prepared.headers['FTX-SUBACCOUNT'] = my_subaccount_nickname
    session = Session()
    response = session.send(prepared)
    
    history_list = eval(response.text.replace('true','True').replace('false','False').replace('null','None').encode('utf8'))['result']
    return history_list

def get_mid_price(market_name):
    url = 'https://ftx.com/api/markets/{}'.format(market_name)
    response = request("GET", url)
    future_data = eval(response.text.replace('true','True').replace('false','False').replace('null','None').encode('utf8'))['result']
    price = (future_data['ask']+future_data['bid'])/2
    return(price)

def get_current_price(market_name):
    url = 'https://ftx.com/api/markets/{}'.format(market_name)
    response = request("GET", url)
    future_data = eval(response.text.replace('true','True').replace('false','False').replace('null','None').encode('utf8'))['result']
    price = future_data['price']
    return(price)


    
    