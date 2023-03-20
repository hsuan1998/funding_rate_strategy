#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 19 11:00:36 2021

@author: Celeste
"""


import time
from requests import request
import json
import os

#%%
def future_list():
    
    now = time.time()
    
    url = 'https://ftx.com/api/funding_rates'
    
    params = {'start_time': now-3600,
              'end_time': now}
    
    response = request("GET", url, params = params)
    now_list = eval(response.text.replace('true','True').encode('utf8'))['result']
    
    future_list = [item['future'] for item in now_list]
    
    return(future_list)

#%% api authentication(next funding rate)

def api_next(future_name):

    url = 'https://ftx.com/api/futures/{}/stats'.format(future_name)
    response = request("GET", url)
    return(eval(response.text.replace('true','True').encode('utf8'))['result'])

#%%寫入json

def nextrate():
    next_dict = [{'market':future_name[:-5],
                  'next_rate': api_next(future_name)['nextFundingRate'],
                  'time':api_next(future_name)['nextFundingTime']} for future_name in future_list()]
    
    return(next_dict)

def nextrate_for_stat():
    next_dict = [{'future':future_name,
                  'next_rate': api_next(future_name)['nextFundingRate']} for future_name in future_list()]
    
    return(next_dict)

if __name__ == '__main__':
    with open(os.getcwd()+'/next_funding_rate.json', 'w', encoding='utf-8') as f:
        json.dump(nextrate(), f, ensure_ascii=False, indent=4)
    

    
    