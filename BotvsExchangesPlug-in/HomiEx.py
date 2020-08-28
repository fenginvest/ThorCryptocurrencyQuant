# -*- coding: utf-8 -*-
"""
运行地址：http://127.0.0.1:6688，端口可指定
"""
import ssl
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import json
import time
from broker.client import BrokerContractClient
from broker.exceptions import BrokerRequestException, BrokerApiException
ssl._create_default_https_context = ssl._create_unverified_context


class MyExchange:
    market_url = "https://api.homiex.com"
    tread_url = "https://api.homiex.io/openapi"

    @staticmethod
    def GetTicker(sym):
        url = MyExchange.market_url + '/openapi/quote/v1/ticker/24hr?symbol=' + sym
        raw_data = requests.get(url).json()
        ret_data = {"data": {"buy": raw_data['bestBidPrice'],
                             "sell": raw_data['bestAskPrice'], "last": raw_data['lastPrice'],
                             "high": raw_data['highPrice'], "low": raw_data['lowPrice'],
                             "vol": raw_data['volume']}}
        return ret_data

    @staticmethod
    def GetDepth(api_key, api_secret, symbol):
        homiex = BrokerContractClient(entry_point=MyExchange.tread_url,
                                      api_key=api_key,
                                      secret=api_secret)

        raw_data = homiex.depth(symbol)
        ret_data = {"data": {"time": raw_data['time'], "asks": [], "bids": []}}
        for i in range(len(raw_data['bids'])):
            ret_data['data']['bids'].append([raw_data['bids'][i][0], raw_data['bids'][i][1]])
        for i in range(len(raw_data['asks'])):
            ret_data['data']['asks'].append([raw_data['asks'][i][0], raw_data['asks'][i][1]])
        return ret_data

    @staticmethod
    def GetAccount(api_key, api_secret):
        homiex = BrokerContractClient(entry_point=MyExchange.tread_url,
                                      api_key=api_key,
                                      secret=api_secret)
        raw_data = homiex.account()
        ret_data = {"data": []}
        if "USDT" in raw_data.keys():
            ret_data["data"].append({"currency": raw_data["USDT"]['tokenId'],
                                     "availableMargin": raw_data["USDT"]['availableMargin'],
                                     "positionMargin": raw_data["USDT"]['positionMargin'],
                                     "total": raw_data["USDT"]['total'],
                                     "orderMargin": raw_data["USDT"]['orderMargin']})
        if "BTC" in raw_data.keys():
            ret_data["data"].append({"currency": raw_data["BTC"]['tokenId'],
                                     "availableMargin": raw_data["BTC"]['availableMargin'],
                                     "positionMargin": raw_data["BTC"]['positionMargin'],
                                     "total": raw_data["BTC"]['total'],
                                     "orderMargin": raw_data["BTC"]['orderMargin']})
        ret_data["raw"] = raw_data
        return ret_data


    @staticmethod
    def GetOrders(api_key, api_secret, order_type='LIMIT'):
        homiex = BrokerContractClient(entry_point=MyExchange.tread_url,
                                      api_key=api_key,
                                      secret=api_secret)
        raw_data = homiex.open_orders(order_type=order_type)

        ret_data = {"data": []}
        if len(raw_data) > 0:
            for i in range(len(raw_data)):
                ret_data["data"].append(
                    {
                        "id": raw_data[i]['orderId'],
                        "amount": raw_data[i]['origQty'],
                        "price": raw_data[i]['price'],
                        "status": raw_data[i]['status'],
                        "type": raw_data[i]['side'],
                    }
                )
            ret_data['raw'] = raw_data
        return ret_data

    @staticmethod
    def GetOrder(api_key, api_secret, orders_id):

        homiex = BrokerContractClient(entry_point=MyExchange.tread_url,
                                      api_key=api_key,
                                      secret=api_secret)
        raw_data = homiex.get_order('LIMIT', order_id=orders_id)

        if 'error' in raw_data.keys():
            return {'error': json.dumps(raw_data['error'], encoding="utf8", ensure_ascii=False)}
        if 'orderId' in raw_data:
            ret_data = {"data": {
                "id": raw_data['orderId'],
                "amount": raw_data['origQty'],
                "price": raw_data['price'],
                "status": raw_data['status'],
                "type": raw_data['side'],
            }, 'raw': raw_data}
        else:
            ret_data = {"data": {}}

        return ret_data

    @staticmethod
    def CancelOrder(api_key, api_secret, orders_id):
        homiex = BrokerContractClient(entry_point=MyExchange.tread_url,
                                      api_key=api_key,
                                      secret=api_secret)
        raw_data = homiex.order_cancel(order_id=orders_id)

        ret_data = {"data": True}
        try:
            result = raw_data['result'].encode('utf8')
        except:
            ret_data = {"data": False}
        ret_data['raw'] = raw_data
        return raw_data

    @staticmethod
    def IO(api_key, api_secret, path, params):
        homiex = BrokerContractClient(entry_point=MyExchange.tread_url,
                                      api_key=api_key,
                                      secret=api_secret)
        ret_data = {'data': {}}
        if path == '1':
            raw_data = homiex.get_positions()
            ret_data = {'data': raw_data}
        if path == '2':
            raw_data = homiex.order_new(symbol=params['sym'], clientOrderId=int(time.time()), side=params['order_type'],
                                        orderType='LIMIT', priceType='MARKET',
                                        quantity=params['amt'], price=params['rat'], leverage=params['lever'], timeInForce='GTC',
                                        triggerPrice=None)
            if 'orderId' in raw_data:
                ret_data = {"data": {'id': raw_data['orderId']}}
            else:
                ret_data = raw_data
        return ret_data


class Server(BaseHTTPRequestHandler):

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_POST(self):

        self.data_string = self.rfile.read(int(self.headers['Content-Length']))
        data = json.loads(self.data_string.replace(b"'", b'"'))
        print(data)
        print(self.data_string)
        sent_data = {}
        if data['method'] == "ticker":
            symbol = data['params']['symbol'].upper()
            sent_data = MyExchange.GetTicker(symbol)
        elif data['method'] == "depth":
            access_key = data["access_key"]
            secret_key = data["secret_key"]
            symbol = data['params']['symbol'].upper()
            sent_data = MyExchange.GetDepth(access_key, secret_key, symbol)
        elif data['method'] == "accounts":
            access_key = data["access_key"]
            secret_key = data["secret_key"]
            sent_data = MyExchange.GetAccount(access_key, secret_key)
        elif data['method'] == "cancel":
            access_key = data["access_key"]
            secret_key = data["secret_key"]
            orders_id = data['params']['id']
            sent_data = MyExchange.CancelOrder(access_key, secret_key, orders_id)
        elif data['method'] == "order":
            access_key = data["access_key"]
            secret_key = data["secret_key"]
            orders_id = data['params']['id']
            sent_data = MyExchange.GetOrder(access_key, secret_key, orders_id)
        elif data['method'] == "orders":
            access_key = data["access_key"]
            secret_key = data["secret_key"]
            sent_data = MyExchange.GetOrders(access_key, secret_key)
        elif data['method'][:2] == "__":
            access_key = data["access_key"]
            secret_key = data["secret_key"]
            path = data["method"].split('_')[-1]
            print(path)
            print(type(path))
            params = data["params"]
            sent_data = MyExchange.IO(access_key, secret_key, path, params)

        self.do_HEAD()

        self.wfile.write(bytes(json.dumps(sent_data), encoding='utf8'))


def run(server_class=HTTPServer, handler_class=Server, port=6667):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print('Starting http server...')
    httpd.serve_forever()


if __name__ == "__main__":
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()



