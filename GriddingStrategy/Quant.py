"""
    策略会调用本地的Mongodb数据库，在运行前配置数据库
    数据库的作用是记录订单状态
    配置数据库位置在 38 行
"""
import ccxt
import time
import pymongo
import json


class Transaction(object):
    # 初始化策略参数
    def __init__(self, order_symbol, apikey, secret, num_buy, num_sell, order_spread, order_profit,
                 order_amonut_buy,
                 order_amonut_sell, exchange, password=None, order_type=None):
        self.order_symbol = order_symbol
        self.apiKey = apikey
        self.secret = secret
        self.order_type = order_type
        self.num_buy = num_buy
        self.num_sell = num_sell
        self.order_spread = order_spread
        self.order_profit = order_profit
        self.order_amonut_buy = order_amonut_buy
        self.order_amonut_sell = order_amonut_sell
        self.exchanges = exchange
        self.password = password

        # 初始化交易所
        if self.exchanges == 'bitmex':
            if self.order_symbol == 'BTC/USD':
                self._symbol = 'XBTUSD'
            elif self.order_symbol == 'ETH/USD':
                self._symbol = 'ETHUSD'
            else:
                self._symbol = self.order_symbol
            self.exchange = ccxt.bitmex({"apiKey": self.apiKey, "secret": self.secret})
            client = pymongo.MongoClient('localhost', port=27017)  # 连接数据库
            db = client['bitmex']
            self.col = db[self._symbol]

        if self.exchanges == 'OKEX':
            if self.order_symbol == 'BTC/USD':
                self._symbol = 'BTC-USD-SWAP'
            elif self.order_symbol == 'ETH/USD':
                self._symbol = 'BTC-USD-SWAP'
            elif self.order_symbol == 'BTC/USDT':
                self._symbol = 'BTC-USDT-SWAP'
            elif self.order_symbol == 'ETH/USDT':
                self._symbol = 'BTC-USDT-SWAP'
            self.exchange = ccxt.okex({"apiKey": self.apiKey, "secret": self.secret, 'password': self.password})
            client = pymongo.MongoClient('localhost', port=27017)  # 连接数据库
            db = client['OKEX']
            self.col = db[self._symbol]

        if self.exchanges == 'Binance':
            self.exchange = ccxt.binance({"apiKey": self.apiKey, "secret": self.secret})
            client = pymongo.MongoClient('localhost', port=27017)  # 连接数据库
            db = client['Binance']
            self.col = db[self.order_symbol]

        # client = pymongo.MongoClient('localhost', port=27017)  # 连接数据库
        # db = client['bitmex']
        # self.col = db[self.order_symbol]

    # 策略主要交易逻辑
    def start_transaction(self):
        try:
            if self.exchanges == 'bitmex':
                # 撤销所有订单
                data_ = self.exchange.privateDeleteOrderAll({"symbol": self._symbol})
                for i in data_:
                    print(i)
            if self.exchanges == 'OKEX':
                data_Order = self.exchange.swap_get_orders_instrument_id({'instrument_id': self._symbol, 'state': '0'})
                if "order_info" in data_Order:
                    for i in range(len(data_Order['order_info'])):
                        data_ = self.exchange.swap_post_cancel_order_instrument_id_order_id(
                            {'instrument_id': self._symbol, 'order_id': data_Order['order_info'][i]['order_id']})
                        print(data_)

        except ccxt.NetworkError as e:
            print(self.exchange.id, 'network error:', str(e))
            exit()
        except ccxt.ExchangeError as e:
            print(self.exchange.id, 'exchange error:', str(e))
            exit()
        except Exception as e:
            print(self.exchange.id, str(e))
            exit()
        global base_price
        if self.exchanges == 'bitmex':
            base_price = self.exchange.fetch_ticker(self.order_symbol)['last']
        if self.exchanges == 'OKEX':
            base_price = self.exchange.swapGetInstrumentsInstrumentIdTicker({'instrument_id': self._symbol})['last']
        print(base_price)

        order_price_buy = base_price - self.order_spread
        order_price_sell = base_price + self.order_spread
        print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        time.sleep(0.03)

        balance = self.exchange.fetch_balance()
        print(balance['free']['BTC'])
        print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        time.sleep(0.03)

        orders = []  # 第一次下单使用批量下单
        if self.exchanges == 'bitmex':
            while self.num_buy > 0:
                orders.append(
                    {'symbol': self._symbol, 'side': 'Buy', 'orderQty': self.order_amonut_buy,
                     'price': order_price_buy})
                self.num_buy -= 1
                order_price_buy -= self.order_spread
            while self.num_sell > 0:
                orders.append(
                    {'symbol': self._symbol, 'side': 'Sell', 'orderQty': self.order_amonut_sell,
                     'price': order_price_sell})
                self.num_sell -= 1
                order_price_sell += self.order_spread
            Bulk_order = self.exchange.private_post_order_bulk({'orders': json.dumps(orders)})
            if Bulk_order:
                for i in Bulk_order:
                    dict = {"order_id": i['orderID'], "order_side": i['side'], "order_price": i['price'],
                            "order_status": i['ordStatus']}
                    self.col.insert_one(dict)
                    print(dict)

        if self.exchanges == 'OKEX':
            while self.num_buy > 0:
                orders.append(
                    {"type": "1", 'size': self.order_amonut_buy, "price": order_price_buy, "match_price": "0"})
                self.num_buy -= 1
                order_price_buy -= self.order_spread
            while self.num_sell > 0:
                orders.append(
                    {"type": "2", 'size': self.order_amonut_sell, "price": order_price_sell, "match_price": "0"})
                self.num_sell -= 1
                order_price_sell += self.order_spread
            Bulk_order = self.exchange.swap_post_orders(
                {"instrument_id": self._symbol, "order_data": json.dumps(orders)})
            if Bulk_order:
                for i in range(len(Bulk_order['order_info'])):
                    orders_info = self.exchange.swapGetOrdersInstrumentIdOrderId(
                        {"instrument_id": self._symbol, "order_id": Bulk_order['order_info'][i]['order_id']})
                    dict = {"order_id": Bulk_order['order_info'][i]['order_id'], "order_side": orders_info['type'],
                            "order_price": orders_info['price'],
                            "order_status": orders_info['state']}
                    self.col.insert_one(dict)
                    print(dict)

        # 循环检查订单状态 订单成交或者取消 重新挂单
        while True:
            try:
                for y in self.col.find():
                    take_order_id = y['order_id']
                    take_order_side = y['order_side']
                    take_order_price = y['order_price']
                    take_order_status = y['order_status']
                    time.sleep(0.03)

                    if self.exchanges == 'bitmex':
                        if take_order_status == "Filled" and take_order_side == "Buy":
                            take_sell_order = self.exchange.create_order(symbol=self.order_symbol, type=self.order_type,
                                                                         side='sell',
                                                                         amount=self.order_amonut_sell,
                                                                         price=take_order_price + self.order_profit)
                            if "id" in take_sell_order:
                                if len(take_sell_order['id']) > 28:
                                    myquery = {"order_id": take_order_id}
                                    self.col.delete_one(myquery)
                                    dict = {"order_id": take_sell_order['id'],
                                            "order_side": take_sell_order['info']['side'],
                                            "order_price": take_sell_order['price'],
                                            "order_status": take_sell_order['info']['ordStatus']}
                                    self.col.insert_one(dict)
                                    print(dict)

                        elif take_order_status == "Filled" and take_order_side == "Sell":
                            take_buy_order = self.exchange.create_order(symbol=self.order_symbol, type=self.order_type,
                                                                        side='buy',
                                                                        amount=self.order_amonut_buy,
                                                                        price=take_order_price - self.order_profit)
                            if "id" in take_buy_order:
                                if len(take_buy_order['id']) > 28:
                                    myquery = {"order_id": take_order_id}
                                    self.col.delete_one(myquery)
                                    dict = {"order_id": take_buy_order['id'],
                                            "order_side": take_buy_order['info']['side'],
                                            "order_price": take_buy_order['price'],
                                            "order_status": take_buy_order['info']['ordStatus']}
                                    self.col.insert_one(dict)
                                    print(dict)

                        elif take_order_status == "Canceled" and take_order_side == "Buy":
                            take_buy_order = self.exchange.create_order(symbol=self.order_symbol, type=self.order_type,
                                                                        side='buy',
                                                                        amount=self.order_amonut_buy,
                                                                        price=take_order_price)

                            if "id" in take_buy_order:
                                if len(take_buy_order['id']) > 28:
                                    myquery = {"order_id": take_order_id}
                                    self.col.delete_one(myquery)
                                    dict = {"order_id": take_buy_order['id'],
                                            "order_side": take_buy_order['info']['side'],
                                            "order_price": take_buy_order['price'],
                                            "order_status": take_buy_order['info']['ordStatus']}
                                    self.col.insert_one(dict)
                                    print(dict)

                        elif take_order_status == "Canceled" and take_order_side == "Sell":
                            take_sell_order = self.exchange.create_order(symbol=self.order_symbol, type=self.order_type,
                                                                         side='sell',
                                                                         amount=self.order_amonut_sell,
                                                                         price=take_order_price)

                            if "id" in take_sell_order:
                                if len(take_sell_order['id']) > 28:
                                    myquery = {"order_id": take_order_id}
                                    self.col.delete_one(myquery)
                                    dict = {"order_id": take_sell_order['id'],
                                            "order_side": take_sell_order['info']['side'],
                                            "order_price": take_sell_order['price'],
                                            "order_status": take_sell_order['info']['ordStatus']}
                                    self.col.insert_one(dict)
                                    print(dict)

                    if self.exchanges == 'OKEX':
                        if take_order_status == "2" and take_order_side == "1":
                            take_sell_order = self.exchange.swap_post_order(
                                {"instrument_id": self._symbol, "match_price": "0", "type": '2',
                                 "size": self.order_amonut_sell,
                                 "price": take_order_price + self.order_profit})
                            if "order_id" in take_sell_order:
                                if take_sell_order['order_id'] != -1:
                                    myquery = {"order_id": take_order_id}
                                    self.col.delete_one(myquery)
                                    orders_info = self.exchange.swapGetOrdersInstrumentIdOrderId(
                                        {"instrument_id": self._symbol, "order_id": take_sell_order['order_id']})
                                    dict = {"order_id": orders_info['order_id'],
                                            "order_side": orders_info['type'],
                                            "order_price": orders_info['price'],
                                            "order_status": orders_info['state']}
                                    self.col.insert_one(dict)
                                    print(dict)

                        elif take_order_status == "2" and take_order_side == "2":
                            take_buy_order = self.exchange.swap_post_order(
                                {"instrument_id": self._symbol, "match_price": "0", "type": '1',
                                 "size": self.order_amonut_buy,
                                 "price": take_order_price - self.order_profit})
                            if "order_id" in take_buy_order:
                                if take_buy_order['order_id'] != -1:
                                    myquery = {"order_id": take_order_id}
                                    self.col.delete_one(myquery)
                                    orders_info = self.exchange.swapGetOrdersInstrumentIdOrderId(
                                        {"instrument_id": self._symbol, "order_id": take_buy_order['order_id']})
                                    dict = {"order_id": orders_info['order_id'],
                                            "order_side": orders_info['type'],
                                            "order_price": orders_info['price'],
                                            "order_status": orders_info['state']}
                                    self.col.insert_one(dict)
                                    print(dict)

                        elif take_order_status == "-1" and take_order_side == "1":
                            take_sell_order = self.exchange.swap_post_order(
                                {"instrument_id": self._symbol, "match_price": "0", "type": '2',
                                 "size": self.order_amonut_sell,
                                 "price": take_order_price + self.order_profit})
                            if "order_id" in take_sell_order:
                                if take_sell_order['order_id'] != -1:
                                    myquery = {"order_id": take_order_id}
                                    self.col.delete_one(myquery)
                                    orders_info = self.exchange.swapGetOrdersInstrumentIdOrderId(
                                        {"instrument_id": self._symbol, "order_id": take_sell_order['order_id']})
                                    dict = {"order_id": orders_info['order_id'],
                                            "order_side": orders_info['type'],
                                            "order_price": orders_info['price'],
                                            "order_status": orders_info['state']}
                                    self.col.insert_one(dict)
                                    print(dict)

                        elif take_order_status == "-1" and take_order_side == "2":
                            take_buy_order = self.exchange.swap_post_order(
                                {"instrument_id": self._symbol, "match_price": "0", "type": '1',
                                 "size": self.order_amonut_buy,
                                 "price": take_order_price - self.order_profit})
                            if "order_id" in take_buy_order:
                                if take_buy_order['order_id'] != -1:
                                    myquery = {"order_id": take_order_id}
                                    self.col.delete_one(myquery)
                                    orders_info = self.exchange.swapGetOrdersInstrumentIdOrderId(
                                        {"instrument_id": self._symbol, "order_id": take_buy_order['order_id']})
                                    dict = {"order_id": orders_info['order_id'],
                                            "order_side": orders_info['type'],
                                            "order_price": orders_info['price'],
                                            "order_status": orders_info['state']}
                                    self.col.insert_one(dict)
                                    print(dict)

            except ccxt.NetworkError as e:
                print(self.exchange.id, 'network error:', str(e))
            except ccxt.ExchangeError as e:
                print(self.exchange.id, 'exchange error:', str(e))
            except Exception as e:
                print(self.exchange.id, str(e))
