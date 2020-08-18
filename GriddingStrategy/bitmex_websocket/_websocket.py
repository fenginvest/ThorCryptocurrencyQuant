"""
    Bitmex Websocket
    Websocket 会调用本地的Mongodb数据库，在运行前配置数据库
    数据库的作用是更改订单状态，如果订单状态改变会第一时间更改订单状态
    配置数据库位置在 199 行
"""

import json
import sys
import traceback
import socket
from datetime import datetime
from time import sleep
from threading import Lock, Thread
import websocket
import time
import hashlib
import hmac
import pymongo
import pprint


class BitmexWebsocket(object):
    """
        Websocket API
        创建Websocket client对象后，需要调用Start的方法去启动workder和ping线程
        1. Worker线程会自动重连.
        2. 使用stop方法去停止断开和销毁websocket client,
        3. 四个回调方法..
        * on_open
        * on_close
        * on_msg
        * on_error
        start()方法调用后，ping线程每隔60秒回自动调用一次。
    """

    def __init__(self, host=None, ping_interval=20, key=None, secret=None, _symbol=None, db_exchange=None):
        """Constructor"""
        self.key = key
        self.secret = secret
        self.host = host
        self.ping_interval = ping_interval
        self.symbol = _symbol
        self.db_exchange = db_exchange

        self._ws_lock = Lock()
        self._ws = None

        self._worker_thread = None
        self._ping_thread = None
        self._active = False  # 开启启动websocket的开关。

        # debug需要..
        self._last_sent_text = None
        self._last_received_text = None

    def start(self):
        """
        客户端连接成功后，调用 on_open这个方法
        on_open 方法调用后，才可以向服务器发送消息的方法.
        """

        self._active = True
        self._worker_thread = Thread(target=self._run)
        self._worker_thread.start()

        self._ping_thread = Thread(target=self._run_ping)
        self._ping_thread.start()

    def stop(self):
        """
        停止客户端.
        """
        self._active = False
        self._disconnect()

    def join(self):
        """
        Wait till all threads finish.
        This function cannot be called from worker thread or callback function.
        """
        self._ping_thread.join()
        self._worker_thread.join()

    def send_msg(self, msg: dict):
        """
        向服务器发送数据.
        如果你想发送非json数据，可以重写该方法.
        """
        text = json.dumps(msg)
        self._record_last_sent_text(text)
        return self._send_text(text)

    def _send_text(self, text: str):
        """
        发送文本数据到服务器.
        """
        ws = self._ws
        if ws:
            ws.send(text, opcode=websocket.ABNF.OPCODE_TEXT)

    def _ensure_connection(self):
        """"""
        triggered = False
        with self._ws_lock:
            if self._ws is None:
                self._ws = websocket.create_connection(self.host)

                triggered = True
        if triggered:
            self.on_open()

    def _disconnect(self):
        """
        """
        triggered = False
        with self._ws_lock:
            if self._ws:
                ws: websocket.WebSocket = self._ws
                self._ws = None

                triggered = True
        if triggered:
            ws.close()
            self.on_close()

    def _run(self):
        """
        保持运行，直到调用stop方法
        """
        try:
            while self._active:
                try:
                    self._ensure_connection()
                    ws = self._ws
                    if ws:
                        text = ws.recv()

                        if not text:
                            self._disconnect()
                            continue

                        self._record_last_received_text(text)

                        self.on_msg(text)

                except (websocket.WebSocketConnectionClosedException, socket.error):
                    self._disconnect()
                except:
                    et, ev, tb = sys.exc_info()
                    self.on_error(et, ev, tb)
                    self._disconnect()  #
        except:
            et, ev, tb = sys.exc_info()
            self.on_error(et, ev, tb)

        self._disconnect()

    def _run_ping(self):
        while self._active:
            try:
                self._ping()
            except:  # noqa
                et, ev, tb = sys.exc_info()
                self.on_error(et, ev, tb)
                sleep(1)

            for i in range(self.ping_interval):
                if not self._active:
                    break
                sleep(1)

    def _ping(self):
        ws = self._ws
        if ws:
            ws.send("ping", websocket.ABNF.OPCODE_PING)

    def on_open(self):
        print("on open")
        self.authenticate()

    def authenticate(self):
        expires = int(time.time())
        method = "GET"
        path = "/realtime"
        msg = method + path + str(expires)
        signature = hmac.new(self.secret.encode("utf-8"), msg.encode("utf-8"), digestmod=hashlib.sha256).hexdigest()
        data = {"op": "authKey", "args": [self.key, expires, signature]}
        self.send_msg(data)

    def on_close(self):
        """"""

    def on_msg(self, data: str):
        msg = json.loads(data)
        client = pymongo.MongoClient('localhost', port=27017)  # 连接数据库
        db = client[self.db_exchange]
        col = db[self.symbol]

        if "data" in msg:
            data = msg["data"]
            for i in data:
                if 'ordStatus' in i:
                    if i['ordStatus'] == 'Filled' or i['ordStatus'] == 'Canceled':
                        pprint.pprint(i)
                        myquery = {"order_id": i['orderID']}
                        mydoc = col.find(myquery)
                        if mydoc:
                            if 'ordStatus' in i:
                                newvalues = {"$set": {"order_status": i['ordStatus']}}
                                col.update_one(myquery, newvalues)
                            elif "order_side" in i:
                                newvalues = {"$set": {"order_status": i['order_side']}}
                                col.update_one(myquery, newvalues)
                            elif "order_price" in i:
                                newvalues = {"$set": {"order_status": i['order_price']}}
                                col.update_one(myquery, newvalues)
        # 如果登录成功，就定义账户相关的信息..
        if "request" in msg:
            req = msg["request"]
            success = msg["success"]
            if success:
                if req["op"] == 'authKey':
                    self.subscribe_private_data()

    def subscribe_private_data(self):
        # print(self.symbol)
        if self.symbol == 'BTC/USD':
            _orders_symbol = 'XBTUSD'
        elif self.symbol == 'ETH/USD':
            _orders_symbol = 'ETHUSD'
        else:
            _orders_symbol = self.symbol
        data = {"op": "subscribe", "args": ["order:" + _orders_symbol]}
        # print(data)
        self.send_msg(data)

    def on_error(self, exception_type, exception_value: Exception, tb):
        """
        Callback when exception raised.
        """
        sys.stderr.write(
            self.exception_detail(exception_type, exception_value, tb)
        )

        return sys.excepthook(exception_type, exception_value, tb)

    def exception_detail(
            self, exception_type: type, exception_value: Exception, tb
    ):
        """
        Print detailed exception information.
        """
        text = "[{}]: Unhandled WebSocket Error:{}\n".format(
            datetime.now().isoformat(), exception_type
        )
        text += "LastSentText:\n{}\n".format(self._last_sent_text)
        text += "LastReceivedText:\n{}\n".format(self._last_received_text)
        text += "Exception trace: \n"
        text += "".join(
            traceback.format_exception(exception_type, exception_value, tb)
        )
        return text

    def _record_last_sent_text(self, text: str):
        """
        Record last sent text for debug purpose.
        """
        self._last_sent_text = text[:1000]

    def _record_last_received_text(self, text: str):
        """
        Record last received text for debug purpose.
        """
        self._last_received_text = text[:1000]
