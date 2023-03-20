#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 19 15:43:39 2021

@author: Celeste
"""
import importNew
import pandas as pd
import numpy as np
from datetime import datetime
import json
import itertools
from requests import request
import os
import nextFundingRate

importNew.get_newdata()

#%%

#連續數
def consecutive(y):
    return((y.groupby((y != y.shift()).cumsum()).cumcount() + 1).iat[-1])

def freq(y):
    return((y.groupby((y != y.shift()).cumsum()).cumcount() + 1).value_counts().iat[0])

#年化連續報酬
def consecutive_return(r):
    y = np.sign(r)
    consecutive = (y.groupby((y != y.shift()).cumsum()).cumcount() + 1).iat[-1]
    return(r[-1*consecutive:].sum()*8760/consecutive)

#年化報酬
def total_return(r):
    return(r.sum()*8760/r.count())

def month_return(r):
    return(r[-720:].sum()*8760/720)

#%%
#讀取保證金幣種
margin = pd.read_csv('可當保證金幣種.csv')
margin['Future']=margin['Future'].apply(lambda x: x+'-PERP')
margin.set_index('Future',inplace=True)

#讀取history json
rateList = []
limit_list = []
with open(os.getcwd()+'/funding_rate_2021.json') as f:
    for jsonObj in f:
        Dict = json.loads(jsonObj)
        rateList.extend(eval(Dict))
    
result = list(itertools.chain.from_iterable(rateList))
    
history_df = pd.DataFrame(result)
    
history_df['time'] = history_df['time'].apply(lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S%z'))
    
history_df['rate_sign'] = np.sign(history_df.rate)
    
    #合併
consecutive_df = history_df.groupby('future').rate_sign.agg(['last',
                                                             lambda y: consecutive(y),
                                                             lambda y: freq(y)])
    
stat_df = history_df.groupby('future').rate.agg(['last',
                                                 lambda r: total_return(r),
                                                 lambda r: consecutive_return(r),
                                                 lambda r: month_return(r)]).rename(columns={'<lambda_0>': '年化報酬率', '<lambda_1>': '連續年化','<lambda_2>': '近一個月年化報酬率'})
    
#正負時數
history_counts = history_df.groupby('future').rate_sign.value_counts().unstack().drop(0,axis=1)
history_counts = pd.concat([history_counts,history_counts.sum(axis=1)],axis=1).rename(columns={-1: '負', 1: '正',0:'總時數'})
history_counts['正％'] = history_counts['正']/history_counts['總時數']
history_counts['負％'] = history_counts['負']/history_counts['總時數']
    
    
stat_df['正連續'] = consecutive_df[consecutive_df['last']>0]['<lambda_0>']
stat_df['負連續'] = consecutive_df[consecutive_df['last']<0]['<lambda_0>']
stat_df['換手頻率'] = consecutive_df['<lambda_1>']

stat_df = stat_df.merge(margin['可當保證金'],how='left',right_index=True,left_index=True).fillna(0)
stat_df.loc[stat_df[stat_df['可當保證金']==0].index.tolist(),'年化報酬率']=stat_df['年化報酬率']/2
stat_df.loc[stat_df[stat_df['可當保證金']==0].index.tolist(),'連續年化']=stat_df['連續年化']/2
stat_df.loc[stat_df[stat_df['可當保證金']==0].index.tolist(),'近一個月年化報酬率']=stat_df['近一個月年化報酬率']/2
stat_df['可當保證金'] = stat_df['可當保證金'].replace(0, False)


for future_name in stat_df.index:
        #成交量
    url = 'https://ftx.com/api/markets/{}'.format(future_name)
    response = request("GET", url)
    future_data = eval(response.text.replace('true','True').replace('false','False').replace('null','None').encode('utf8'))['result']
        #是否有現貨
    url = 'https://ftx.com/api/markets/{}'.format(future_name[:-5]+'/USDT')
    response = request("GET", url)
    spot_bool1 = eval(response.text.replace('true','True').replace('false','False').replace('null','None').encode('utf8'))['success']
    
    url = 'https://ftx.com/api/markets/{}'.format(future_name[:-5]+'/USD')
    response = request("GET", url)
    spot_bool2 = eval(response.text.replace('true','True').replace('false','False').replace('null','None').encode('utf8'))['success']
    
    try:
        limit_list.append({'future':future_name,'volume':future_data['volumeUsd24h'],'有USDT現貨交易對':spot_bool1,'有USD現貨交易對':spot_bool2})
    except KeyError:
        limit_list.append({'future':future_name,'volume':0,'有USDT現貨交易對':spot_bool1,'有USD現貨交易對':spot_bool2})

        
limit_df = pd.DataFrame(limit_list).set_index('future')
rate_df = pd.DataFrame(nextFundingRate.nextrate_for_stat()).set_index('future')
    #合併
total_df = pd.concat([stat_df,history_counts,limit_df,rate_df],axis = 1).fillna(0)
total_df['換手頻率/總時數'] = total_df['換手頻率']/total_df['總時數']


if __name__ == '__main__':

    total_df.to_excel(os.getcwd()+'/FTX永續資金費率.xlsx',encoding = 'UTF-8')
    
