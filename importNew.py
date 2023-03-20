#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 19 14:04:59 2021

@author: Celeste
"""
import time
from datetime import datetime
from requests import request
import json
import os

#%% api authentication

def get_history(i,firsttime):
            
    url = 'https://ftx.com/api/funding_rates'
            
    params = {'start_time': firsttime+3600*i+1,
              'end_time': firsttime+3600*(i+1)+1}
        
    response = request("GET", url, params = params)
    return(eval(response.text.replace('true','True').encode('utf8'))['result'])
        
def get_newdata():
    
    now = time.time()
        
    with open(os.getcwd()+'/lastTime.json') as f:
        firsttime = json.load(f)
            
    firsttime = time.mktime(datetime.strptime(firsttime, '%Y-%m-%dT%H:%M:%S%z').timetuple())+28800
    input_times = int((now-firsttime)/3600)
    
    if input_times!=0:
        
        #加入資料至檔案
        
        new_list = [get_history(i,firsttime) for i in range(input_times)]
            
        with open(os.getcwd()+'/funding_rate_2021.json', 'a', encoding='utf-8') as f:
            f.write('\n')
            json.dump(json.dumps(new_list), f, ensure_ascii=False, indent=4)
            
        with open(os.getcwd()+'/lastTime.json', 'w', encoding='utf-8') as f:
            json.dump(new_list[-1][0]['time'], f, ensure_ascii=False, indent=4)




