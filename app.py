from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi('GXazNC0tG1jQL4x1XWHDVr9oyBWGun+S/U2G5C2ARZzWafBYpXVRorljyyG4A7WvCa5XBboJw0AfrwwKzQzVRboi15UxTRgk1ULb/Xe6j6VFSMFDljL4XjQLClyT5LvsZu77VhW/5gzGLoHj3ua6QAdB04t89/1O/w1cDnyilFU=')
# Channel Secret
handler = WebhookHandler('374fc7fec74b20818c0d5c143c1b38d1')

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print("本次訊息:"+str(event))

    if( event.message.text.lower()=="help" ):
        message = TextSendMessage(text= "使用方法：\n1. 輸入數字即可紀錄花費\n如：100\n\n2. 如果不小心打錯了，請輸入該金額負數(負號要半形)\n如：-100\n\n3. 輸入日期可以查詢當天的總消費金額(年份請使用西元)，若是沒有輸入年分則自動套用當年年分\n如： 2021/01/01、04/05\n\n4. 輸入月份可以查詢該月份總消費金額(年份請使用西元)\n如：2021/01\n\n5. 如果在查詢時加入 detail 則可以查看每一筆詳細資訊\n如：2021/03 detail\n    2021/05/05 Detail\n\n6. 如果想要補紀錄，請輸入日期+空格+金額\n如:03/01 500")
        line_bot_api.reply_message(event.reply_token, message)
        return

    import time
    import pygsheets
    import pandas as pd
    from datetime import datetime

    #變數
    Date = [31,28,31,30,31,30,31,31,30,31,30,31]
    default_year = "2021"
    DateStartTime = ""
    DateEndTime = ""
    money = 0
    short = False
    Detail = False
    MakeUpMoney = False

    if( "detail" in event.message.text):
        Detail = True
        event.message.text = event.message.text.replace("detail","")
        event.message.text = event.message.text.replace(" ","")
    if( "Detail" in event.message.text):
        Detail = True
        event.message.text = event.message.text.replace("Detail","")
        event.message.text = event.message.text.replace(" ","")

    try:
        if len(event.message.text.split(' '))==2:
            print(str(len(event.message.text.split(' ')))+"格 有可能是要補交作業")
            money = int(event.message.text.split(' ')[1])
            event.message.text = event.message.text.split(' ')[0]
            MakeUpMoney = True
    except:
        message = TextSendMessage(text= "請不要亂打")
        line_bot_api.reply_message(event.reply_token, message)
        return
    #先看是不是純數字
    try:
        money = int(event.message.text)
        #message = TextSendMessage(text= "金額紀錄:"+str(money))
        #line_bot_api.reply_message(event.reply_token,  message)

        #加入資料表
        #驗證檔案
        gc = pygsheets.authorize(service_account_file='./JuanLineBot-28aafef90740.json')

        #sheet網址
        survey_url = 'https://docs.google.com/spreadsheets/d/1coon61mhEBu5O74caQc6ruYyKJ4uckUfJpqq7vTiUvk/'
        sh = gc.open_by_url(survey_url)
        
        # #選擇資料表
        ws = sh.worksheet_by_title('juan')

        # #加入的東C
        df1 = pd.DataFrame({'User':[event.source.user_id], 'TimeStamp':[event.timestamp], 'Money':[money]})
        print("加入用df成功"+str(df1))

        # #加入
        start ="A"+str(len(ws.get_all_values(include_tailing_empty_rows=False))+1)

        ws.set_dataframe(df1, start, copy_head=False)
        
        
        print("加入成功")

    #不是再判斷能不能轉日期
    except:
        DateList = event.message.text.split('/')
        if(len(DateList)==3):
            try:
                if( int(DateList[0])>=1970 and int(DateList[0])<2262 ) and ( int(DateList[1]) >= 1 and int(DateList[1]) <= 12 ):
                    if( int(DateList[2]) >= 1 and int(DateList[2]) <= Date[int(DateList[1])-1] ):
                        DateStartTime = DateList[0]+"/"+DateList[1]+"/"+DateList[2]+" 00:00:00"
                        DateEndTime = DateList[0]+"/"+DateList[1]+"/"+DateList[2]+" 23:59:59"
                        Finaltext = "搜尋"+DateStartTime.split(' ')[0]+"的紀錄\n"
                        short = True
            except:
                message = TextSendMessage(text= "請不要亂打")
                line_bot_api.reply_message(event.reply_token, message)
                return
        elif(len(DateList)==2):
            try:
                if( int(DateList[0]) >= 1 and int(DateList[0]) <= 12 ):
                    if( int(DateList[1]) >= 1 and int(DateList[1]) <= Date[int(DateList[0])-1] ):
                        DateStartTime = default_year+"/"+DateList[0]+"/"+DateList[1]+" 00:00:00"
                        DateEndTime = default_year+"/"+DateList[0]+"/"+DateList[1]+" 23:59:59"
                        Finaltext = "搜尋"+DateStartTime.split(' ')[0]+"的紀錄\n"
                        short = True
                elif( int(DateList[0]) >= 1970 and int(DateList[0]) < 2262 ) and ( int(DateList[1]) >= 1 and int(DateList[1]) <= 12 ):
                    DateStartTime = DateList[0]+"/"+DateList[1]+"/"+"01"+" 00:00:00"
                    DateEndTime = DateList[0]+"/"+DateList[1]+"/"+str(Date[ int(DateList[1])-1 ])+" 23:59:59"
                    Finaltext = "搜尋"+DateStartTime.split(' ')[0]+"～"+DateEndTime.split(' ')[0]+"的紀錄\n"
            except:
                message = TextSendMessage(text= "請不要亂打")
                line_bot_api.reply_message(event.reply_token, message)
                return
        else:
            message = TextSendMessage(text= "請不要亂打") 
            line_bot_api.reply_message(event.reply_token, message)
            return

        if(DateStartTime != ""):
            StartTimeStamp = int(time.mktime(time.strptime(DateStartTime, "%Y/%m/%d %H:%M:%S"))) - 28800 # 轉成時間戳
            EndTimeStamp = int(time.mktime(time.strptime(DateEndTime, "%Y/%m/%d %H:%M:%S"))) - 28800 # 轉成時間戳
            #驗證檔案
            gc = pygsheets.authorize(service_account_file='./JuanLineBot-28aafef90740.json')

            #sheet網址
            survey_url = 'https://docs.google.com/spreadsheets/d/1coon61mhEBu5O74caQc6ruYyKJ4uckUfJpqq7vTiUvk/'
            sh = gc.open_by_url(survey_url)
            
            # #選擇資料表
            ws = sh.worksheet_by_title('juan')

            #補交金額
            if MakeUpMoney:
                # #加入的東C
                df1 = pd.DataFrame({'User':[event.source.user_id], 'TimeStamp':[StartTimeStamp*1000], 'Money':[money]})
                print("加入用df成功"+str(df1))

                # #加入
                start ="A"+str(len(ws.get_all_values(include_tailing_empty_rows=False))+1)

                ws.set_dataframe(df1, start, copy_head=False)

                Finaltext = str(money)+"補紀錄成功"
                print("加入成功")

            #沒有補交 一般查詢
            else:
                FindMoneyDf = pd.DataFrame(ws.get_all_values(include_tailing_empty_rows=False,include_tailing_empty=False))
                FindMoneyDf[1] = FindMoneyDf[1].astype(int)/1000
                FindMoneyDf[2] = FindMoneyDf[2].astype(int)
                FindMoneyDf = FindMoneyDf[ (FindMoneyDf[1]>=StartTimeStamp) & (FindMoneyDf[1]<=EndTimeStamp) & (FindMoneyDf[0]==event.source.user_id)]
                FindMoneyDf = FindMoneyDf.sort_values(by=[1])
                Total = int(FindMoneyDf[2].sum())
                Finaltext += "總支出為: "+str(Total)
                # 顯示當天
                if Detail and short:
                    for i in range(len(FindMoneyDf)):
                        Finaltext+="\n"+str(datetime.fromtimestamp( int( FindMoneyDf.iloc[i,1] )+28800 ) ).split(' ')[1]+": "+str(FindMoneyDf.iloc[i,2])
                # 顯示當月
                elif Detail and not short:
                    Month = int(DateList[1])
                    for i in range( Date[Month-1] ):
                        DayStartTimeStamp = StartTimeStamp + (86400*i)
                        DayEndTimeStamp = StartTimeStamp + (86400*i) + 86400
                        TodayMoneyDf = FindMoneyDf[ (FindMoneyDf[1]>=DayStartTimeStamp) & (FindMoneyDf[1]<DayEndTimeStamp) ]
                        DayTotal = int(TodayMoneyDf[2].sum())
                        if DayTotal>0:
                            Finaltext+="\n"+str(Month)+"/"+str(i+1)+" : "+str(DayTotal)

            message = TextSendMessage(text= Finaltext)

        line_bot_api.reply_message(event.reply_token, message)

            
    # message = TextSendMessage(text=event.message.text + "測試拉" +str(event) + "ID type:" + str(type(event.message.id)))
    # line_bot_api.reply_message(event.reply_token, message)

import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
