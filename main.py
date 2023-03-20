#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 17 10:23:51 2021

@author: Celeste
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QAbstractTableModel, Qt
from form import Ui_Form

import orders
import nextFundingRate

import pandas as pd
import os
import time
import json

#%%

#df顯示在table上
class pandasModel(QAbstractTableModel):

    def __init__(self, data):
        QAbstractTableModel.__init__(self)
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parnet=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[col]
        return None
    
    
class MyMainForm(QMainWindow, Ui_Form):
    def __init__(self, parent=None):
        self.now = time.time()
        
        super(MyMainForm, self).__init__(parent)
        self.setupUi(self)

        self.returnButton.clicked.connect(self.strategy)
        self.cryptoButtom.clicked.connect(self.strategy2)
        #self.orderButton.clicked.connect(self.place_order)
        self.orderButton_2.clicked.connect(self.place_order2)
        
        self.df = pd.read_excel(os.getcwd()+'/FTX永續資金費率.xlsx').set_index('future')
        rate_df = pd.DataFrame(nextFundingRate.nextrate_for_stat()).set_index('future')
        self.df['next_rate']=rate_df
        self.df['volume'] = self.df['volume'].astype(float)
        
        self.spread_dict = []
    
    def strategy(self):
    
        try:
            if self.returnInput.currentText()=="中位數":
                limit_return = abs(self.df['年化報酬率']).median()
            else:
                limit_return = float(self.returnInput.currentText())
            
            condition1 = self.df['換手頻率/總時數']<self.df['換手頻率/總時數'].median()
            condition2 = self.df['總時數']>self.df['總時數'].quantile(0.25)
            condition3 = (self.df['年化報酬率']>limit_return) & (self.df['年化報酬率']>0)
            condition4 = self.df['volume']>=1000000
            condition5 = (self.df['有USDT現貨交易對']|self.df['有USD現貨交易對'])==True
            condition6 = self.df['next_rate']>=0
            
                        
            self.result = list(self.df[condition3 & condition4 & condition5 & condition6].index)
            
            self.stat = self.df.loc[self.result,:].sort_values(by=self.comboBox_2.currentText(), ascending=False)
        
            for var in ['last','next_rate']:
                self.stat[var] = self.stat[var].map(lambda x:format(x,'.4%'))
                    
            for var in ['年化報酬率','連續年化','近一個月年化報酬率','正％','負％','換手頻率/總時數']:
                self.stat[var] = self.stat[var].map(lambda x:format(x,'.2%'))
                    
            self.stat['volume'] = self.stat['volume'].map(lambda x:format(x,',.0f'))
            
            self.textBrowser.setText('篩選標的：{}\n個數：{}'.format(self.result,len(self.result)))
            model = pandasModel(self.stat.reset_index())
            self.tableView.setModel(model)
            
        except ValueError:
            
            self.textBrowser.setText("年化報酬限制 is not a float.")
    
    def strategy2(self):
        
        try:
            select = self.cryptoInput.toPlainText()
            self.result2 = select+'-PERP'
            details2 = self.df.loc[self.result2].copy()
            for var in ['last','next_rate']:
                details2.loc[var] = format(details2.loc[var],'.4%')
                    
            for var in ['年化報酬率','連續年化','近一個月年化報酬率','正％','負％','換手頻率/總時數']:
                details2.loc[var] = format(details2.loc[var],'.2%')
                    
            details2['volume'] = format(details2['volume'],',.0f')
            model = pandasModel(details2.reset_index())
            self.tableView.setModel(model)
            
        except:

            self.textBrowser.setText("標的名稱錯誤或無此標的.")
    """
    def place_order(self):
        
        now = time.time()
        result = self.result
        
        wealth = float(self.wealthInput.toPlainText())
        self.currency = '/'+self.comboBox.currentText()
        leverage = float(self.leverageInput.currentText())
        orders.set_leverage(leverage)
    
        error_list = []
        
        for future_name in result:
            #價格
            try:
                future_price = orders.get_mid_price(future_name)
                spot_price = orders.get_mid_price(future_name[:-5]+self.currency)
                
            except KeyError:
                
                error_list.append(future_name)
                continue
            
            #下單
            
            
            try:

                future_result = orders.order(market=future_name,
                                             side='sell',
                                             size=wealth/spot_price/2,
                                             price=future_price,
                                             type1='limit')
                    
                spot_result = orders.order(market=future_name[:-5]+self.currency,
                                             side='buy',
                                             size=wealth/spot_price/2,
                                             price=spot_price,
                                             type1='limit')
                    
                if (future_result['success']==False) | (spot_result['success']==False):
                    orders.delete_order()
                    done = '下單失敗,請手動檢查下單系統,失敗原因查看log檔'
                    self.textBrowser.setText(done)
                    break

            except:
                error_list.append(future_name)
                continue

        #掛單則修改訂單價格，直到沒有掛單
        #order<10
        while True:
            time.sleep(30)
            open_dict = orders.open_order(result)
            
            if len(open_dict)>10:
                done = "掛單大於10筆,請檢查程式是否有錯"
                self.textBrowser.setText(done)
                break
            
            elif open_dict == {}:
                if (future_result['success']==False) | (spot_result['success']==False):
                    break
                else:
                    spread_dict = orders.filled_orders(start_time=now)
                    with open(os.getcwd()+'/下單資料.json', 'a', encoding='utf-8') as f:
                        json.dump(spread_dict, f, ensure_ascii=False, indent=4)
                        
                    done = "無現貨部位之標的：{}\n其餘下單完成!".format(error_list)
                    self.textBrowser.setText(done)
                    break
            else:
                orders.modify_order(open_dict)

    """   
    def place_order2(self):
        
        if self.df.loc[self.result2,'有{}現貨交易對'.format(self.comboBox.currentText())]==True:
            
            now = time.time()
            future_name = self.result2 
            
            wealth = float(self.wealthInput.toPlainText())
            self.currency = '/'+self.comboBox.currentText()
            leverage = float(self.leverageInput.currentText())
            orders.set_leverage(leverage)
        
            error_list = []
            
            #價格
            try:
                    
                future_price = orders.get_mid_price(future_name)
                spot_price = orders.get_mid_price(future_name[:-5]+self.currency)
                    
            except KeyError:
                
                error_list.append(future_name)
                
            #下單
            try:
                future_result = orders.order(market=future_name,
                                             side='sell',
                                             size=wealth/spot_price/2,
                                             price=future_price,
                                             type1='limit')
                
                spot_result = orders.order(market=future_name[:-5]+self.currency,
                                           side='buy',
                                           size=wealth/spot_price/2,
                                           price=spot_price,
                                           type1='limit')
                        
                if (future_result['success']==False) | (spot_result['success']==False):
                    orders.delete_order()
                    done = '下單失敗,請手動檢查下單系統,失敗原因查看log檔'
                    self.textBrowser.setText(done)
                   
                        
            except:
                error_list.append(future_name)
                
            #掛單則修改訂單價格，直到沒有掛單
            #order<10
            while True:
                time.sleep(30)
                open_dict = orders.open_order(future_name,self.currency)
                
                if len(open_dict)>10:
                    orders.delete_order()
                    done = "掛單大於10筆,請檢查程式是否有錯"
                    self.textBrowser.setText(done)
                    break
                
                elif open_dict == {}:
                    if (future_result['success']==False) | (spot_result['success']==False):
                        break
                    else:
                        spread_dict = orders.filled_orders(start_time=now)
                        with open(os.getcwd()+'/下單資料.json', 'a', encoding='utf-8') as f:
                            json.dump(spread_dict, f, ensure_ascii=False, indent=4)
                            
                        done = "無現貨部位之標的：{}\n其餘下單完成!".format(error_list)
                        self.textBrowser.setText(done)
                        break
                    
                else:
                    self.textBrowser.setText('重新掛單')
                    orders.modify_order(open_dict)
                    
        else:
            self.textBrowser.setText("此標的無{}現貨交易對,請重新選擇.".format(self.comboBox.currentText()))
            
            
if __name__ == "__main__":
    
    #固定的，PyQt5程序都需要QApplication对象。sys.argv是命令行参数列表，确保程序可以双击运行
    app = QApplication(sys.argv)
    #初始化
    myWin = MyMainForm()
    #将窗口控件显示在屏幕上
    myWin.show()
    #程序运行，sys.exit方法确保程序完整退出。
    sys.exit(app.exec_())


