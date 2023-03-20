#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 31 10:16:01 2021

@author: Celeste
"""

import pandas as pd
from requests import post
import os
import sys

import orders


#%%

#LINE
def lineNotifyMessage(token, msg):
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {
        'message': msg
    }
    r = post("https://notify-api.line.me/api/notify",
                      headers=headers, params=payload)
    # print(r.status_code)
    return r.status_code

token = 'token_'

limit_rate = sys.argv[1]
limit_minus = sys.argv[2]
limit_spread = sys.argv[3]


leverage = orders.get_leverage()

future_position = orders.position()

#下期統計表
df = pd.read_excel(os.getcwd()+'/FTX永續資金費率.xlsx')
df['future'] = df['future'].str[:-5]


current_price = [{'market':market_name,
                  'current_price':orders.get_current_price(market_name+'/USDT'),
                  'spread':orders.get_current_price(market_name+'-PERP') - orders.get_current_price(market_name+'/USDT')}for market_name in [position['market'] for position in future_position]]
for position in future_position:
    position.update({'current_price':orders.get_current_price(position['market']+'/USDT'),
                     'spread':orders.get_current_price(position['market']+'-PERP') - orders.get_current_price(position['market']+'/USDT')})
            

total_df = pd.DataFrame(future_position)
total_df = total_df.merge(right=df,left_on='market',right_on='future')
        
#平倉條件
condition1 = total_df['next_rate']<float(limit_rate) #費率過小
condition2 = (total_df['current_price']>=total_df['entry_price']*(1+0.9/float(leverage))) & (total_df['可當保證金']==False) #爆倉風險
condition3 = total_df['負連續']>=float(limit_minus) #負連續過大
condition4 = total_df['spread']<float(limit_spread) #基差過小
        
        
if total_df[condition1 | condition2 | condition3 | condition4]['market'].empty:
    print('FTX_Eric_無觸發平倉條件')
        
else:
    for future_name in total_df[condition1 | condition2 | condition3 | condition4]['market']:
        
        string = 'FTX_Eric_{}觸發平倉條件\n\n原因:\n'.format(future_name)
        
        if future_name in total_df[condition3]['market'].tolist():
            string = string+'負連續({})達到或是超過{}次\n'.format(int(total_df[total_df['market']==future_name]['負連續']),limit_minus)
        if future_name in total_df[condition2]['market'].tolist():
            string = string+'此標的現貨不可當保證金,目前有爆倉風險\n'
        if future_name in total_df[condition1]['market'].tolist():
            string = string+'預計下期資金費率({})<{}\n'.format(format(float(total_df[total_df['market']==future_name]['next_rate']),'.5f'),limit_rate)
        if future_name in total_df[condition4]['market'].tolist():
            string = string+'目前期現基差({})<{}\n'.format(format(float(total_df[total_df['market']==future_name]['spread']),'.5f'),limit_spread)
        lineNotifyMessage(token, string) 





    