# -*- coding: utf-8 -*-
"""
Created on Thu Oct 28 14:20:23 2021

@author: celeste
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QAbstractTableModel,Qt
from PyQt5 import QtCore, QtWidgets
from rebalance_form import Ui_dialog

import matplotlib
matplotlib.use("Qt5Agg")  # 聲明使用QT5
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates

import time
import pandas as pd
import os
import json
from datetime import datetime

import orders

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

class MyFigure(FigureCanvas):
    def __init__(self,width=4, height=8, dpi=100):
        #第一步：創建一個創建Figure
        self.fig = Figure(figsize=(width, height), dpi=dpi,constrained_layout=True)

        #第二步：在父類中激活Figure窗口
        super(MyFigure,self).__init__(self.fig) #此句必不可少，否則不能顯示圖形
        self.ax = self.fig.add_subplot(1,1,1)
        
    def plot(self,spread_list,market):
    
        df = pd.DataFrame(spread_list[market]).set_index('time')
        try:
            self.ax.plot(df)
            self.ax.set_title(market)
            self.ax.axhline(df.mean().item(),color='r')
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        except ValueError:
            pass
                 

class MyMainForm(QMainWindow, Ui_dialog):
    def __init__(self, parent=None):
        super(MyMainForm, self).__init__(parent)
        self.setupUi(self)

        self.pushButton.clicked.connect(self.place_order)
        self.pushButton_2.clicked.connect(self.renew_df)
        
        self.future_position = orders.position()
        position_df = pd.DataFrame(self.future_position)
        model = pandasModel(position_df)
        self.tableView.setModel(model)
        
        market_list = orders.position(market=True)
        spread_list = {market:[{'time':datetime.strptime(f['startTime'], '%Y-%m-%dT%H:%M:%S%z'),
                                'spread':f['close']-s['close']} for f,s in zip(orders.get_close_history(market+'-PERP'),orders.get_close_history(market+'/USD'))] for market in market_list}


        
        for market in spread_list:    
                #第五步：定義MyFigure類的一個實例
            self.F = MyFigure(width=4, height=8, dpi=100)
            self.F.plot(spread_list,market)
                
            self.groupBox = QtWidgets.QGroupBox(self.scrollAreaWidgetContents)
            self.groupBox.setMinimumSize(QtCore.QSize(100, 250))
            self.gridlayout = QtWidgets.QGridLayout(self.groupBox)  # 繼承容器groupBox
            self.gridlayout.addWidget(self.F,0,1)
            self.verticalLayout.addWidget(self.groupBox)

        
    def place_order(self):
        
        now = time.time()
        future_name = self.cryptoInput.toPlainText()
        
        self.currency = '/'+self.comboBox.currentText()

            
        if [d for d in self.future_position if d['market']==future_name]==[]:
            self.textBrowser.setText('沒有此標的部位,或輸入名稱錯誤!\n請輸入大寫,舉例:BTC')
        else:
            if self.quantityInput.currentText()=="All":
                quantity = float([d['size'] for d in self.future_position if d['market']==future_name][0])
            else:
                quantity = float(self.quantityInput.currentText())
                
            try:
                #價格
                future_price = orders.get_mid_price(future_name+'-PERP')
                spot_price = orders.get_mid_price(future_name+self.currency)    
                
                #下單
                future_result = orders.order(market=future_name+'-PERP',
                                     side='buy',
                                     size=quantity,
                                     price=future_price,
                                     type1='limit')
                    
                spot_result = orders.order(market=future_name+self.currency,
                                     side='sell',
                                     size=quantity,
                                     price=spot_price,
                                     type1='limit')
                        
                if (future_result['success']==False) | (spot_result['success']==False):
                    orders.delete_order()
                    self.textBrowser.setText('下單失敗,請手動檢查下單系統,失敗原因查看log檔')
                #掛單則修改訂單價格，直到沒有掛單
                while True:
                                
                    time.sleep(30)
                    open_dict = orders.open_order(future_name+'-PERP',self.currency)
                    
                    if len(open_dict)>10:
                        orders.delete_order()
                        self.textBrowser.setText("掛單大於10筆,請檢查程式是否有錯")
                        break
                    
                    elif open_dict == {}:
    
                        spread_dict = orders.filled_orders(start_time=now)
                        with open(os.getcwd()+'/平倉資料.json', 'a', encoding='utf-8') as f:
                            json.dump(spread_dict, f, ensure_ascii=False, indent=4)
                                
                        self.textBrowser.setText('{}單位{},結束平倉'.format(quantity,future_name))
                        break
                        
                    else:
                        self.textBrowser.setText('重新掛單')
                        print('重新掛單')
                        orders.modify_order(open_dict)
                        
            except KeyError:
                self.textBrowser.setText('無{}交易對,請重新選擇'.format(future_name+self.currency))

    def renew_df(self):
        try:
            self.future_position = orders.position()
            position_df = pd.DataFrame(self.future_position)
            model = pandasModel(position_df)
            self.tableView.setModel(model)
        except:
            self.textBrowser.setText('當前無部位')
if __name__ == "__main__":
    
    #固定的，PyQt5程序都需要QApplication对象。sys.argv是命令行参数列表，确保程序可以双击运行
    app = QApplication(sys.argv)
    #初始化
    myWin = MyMainForm()
    #将窗口控件显示在屏幕上
    myWin.show()
    #程序运行，sys.exit方法确保程序完整退出。
    sys.exit(app.exec_())
    