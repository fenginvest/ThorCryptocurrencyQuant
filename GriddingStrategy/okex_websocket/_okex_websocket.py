
"""
    OKEX Websocket

"""

import json
import sys
import traceback
import socket
from datetime import datetime
from time import sleep
from threading import Lock, Thread
import websocket
import zlib
import time
import hashlib
import hmac
import base64
import pprint
import pymongo


class OKEXWebsocket(object):
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

    def __init__(self, host=None, ping_interval=20, key=None, secret=None, _symbol=None, db_exchange=None, password=None):
        """Constructor"""
        self.key = key
        self.secret = secret
        self.password = password
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
        启动客户端，客户端连接成功后，会调用 on_open这个方法
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
        try:
            while self._active:
                try:
                    self._ensure_connection()
                    ws = self._ws
                    if ws:
                        text = ws.recv()

                        # ws object is closed when recv function is blocking
                        if not text:
                            self._disconnect()
                            continue

                        self._record_last_received_text(text)

                        self.on_msg(text)
                # ws is closed before recv function is called
                # For socket.error, see Issue #1608
                except (websocket.WebSocketConnectionClosedException, socket.error):
                    self._disconnect()

                # other internal exception raised in on_msg
                except:  # noqa
                    et, ev, tb = sys.exc_info()
                    self.on_error(et, ev, tb)
                    self._disconnect()  #

        except:  # noqa
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
        """on open """
        print("on open")
        key = self.key
        passphrase = self.password
        secret = self.secret
        timestamp = str(time.time())
        msg = timestamp + "GET" + "/users/self/verify"
        sign = hmac.new(secret.encode('utf-8'), msg.encode('utf-8'), digestmod=hashlib.sha256).digest()
        sign = base64.b64encode(sign).decode('utf-8')
        data = {"op": "login", "args": [key, passphrase, timestamp, sign]}

        # data = {"op": "subscribe", "args": ["swap/depth5:BTC-USD-SWAP"]}
        self.send_msg(data)

    def on_close(self):
        """
        on close websocket
        """

    def on_msg(self, data: bytes):
        """call when the msg arrive."""
        decompress = zlib.decompressobj(
            -zlib.MAX_WBITS  # see above
        )

        msg = json.loads(decompress.decompress(data))
        print(msg)
        if "event" in msg:
            if msg['event'] == 'login' and msg['success']:
                # print("登录成功。。")
                self.subscribe_topic()

        if 'table' in msg and msg['table'] == 'swap/order':
            client = pymongo.MongoClient('localhost', port=27017)  # 连接数据库
            db = client[self.db_exchange]
            col = db[self.symbol]
            if "data" in msg:
                data = msg["data"]
                for i in range(len(data)):
                    if 'state' in data[i]:
                        if data[i]['state'] == '2' or data[i]['state'] == '-1':
                            pprint.pprint(data[i])
                            myquery = {"order_id": data[i]['order_id']}
                            mydoc = col.find(myquery)
                            if mydoc:
                                if 'state' in data[i]:
                                    newvalues = {"$set": {"order_status": data[i]['state']}}
                                    col.update_one(myquery, newvalues)
                                elif "type" in i:
                                    newvalues = {"$set": {"order_side": data[i]['type']}}
                                    col.update_one(myquery, newvalues)
                                elif "price" in i:
                                    newvalues = {"$set": {"order_price": data[i]['price']}}
                                    col.update_one(myquery, newvalues)

    def subscribe_topic(self):

        if self.symbol == 'BTC/USD':
            _orders_symbol = 'BTC-USD-SWAP'
        elif self.symbol == 'ETH/USD':
            _orders_symbol = 'ETH-USD-SWAP'
        elif self.symbol == 'BTC/USDT':
            _orders_symbol = 'BTC-USDT-SWAP'
        elif self.symbol == 'ETH/USDT':
            _orders_symbol = 'ETH-USDT-SWAP'
        else:
            _orders_symbol = self.symbol
        self.send_msg({"op": "subscribe", "args": ["swap/order:" + _orders_symbol]})

    def on_error(self, exception_type: type, exception_value: Exception, tb):
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

