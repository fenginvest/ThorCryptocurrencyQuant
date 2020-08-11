import ccxt
import time
import pymongo
import json


class Bitmextransaction(object):

    def __init__(self, order_symbol, order_type, apikey, secret, num_buy, num_sell, order_spread, order_profit, order_amonut_buy,
                 order_amonut_sell, exchange):
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
        if self.order_symbol == 'BTC/USD':
            self._symbol = 'XBTUSD'
        elif self.order_symbol == 'ETH/USD':
            self._symbol = 'ETHUSD'
        else:
            self._symbol = self.order_symbol
        # 初始化交易所
        if exchange == 'bitmex':
            self.exchange = ccxt.bitmex({"apiKey": self.apiKey, "secret": self.secret})

        client = pymongo.MongoClient('localhost', port=27017)  # 连接数据库
        # user_name = 'root'
        # user_pwd = 'NZ6*|QDh-qZF'
        # dbn = client.admin
        # dbn.authenticate(user_name, user_pwd)
        db = client['bitmex']

        self.col = db[self.order_symbol]

    def start_transaction(self):
        try:
            data_ = self.exchange.privateDeleteOrderAll({"symbol": self._symbol})
            for i in data_:
                print(i)

        except ccxt.NetworkError as e:
            print(self.exchange.id, 'network error:', str(e))
            exit()
        except ccxt.ExchangeError as e:
            print(self.exchange.id, 'exchange error:', str(e))
            exit()
        except Exception as e:
            print(self.exchange.id, str(e))
            exit()

        base_price = self.exchange.fetch_ticker(self.order_symbol)['last']
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
        while self.num_buy > 0:
            orders.append(
                {'symbol': self._symbol, 'side': 'Buy', 'orderQty': self.order_amonut_buy, 'price': order_price_buy})
            self.num_buy -= 1
            order_price_buy -= self.order_spread
        while self.num_sell > 0:
            orders.append(
                {'symbol': self._symbol, 'side': 'Sell', 'orderQty': self.order_amonut_sell, 'price': order_price_sell})
            self.num_sell -= 1
            order_price_sell += self.order_spread
        Bulk_order = self.exchange.private_post_order_bulk({'orders': json.dumps(orders)})
        if Bulk_order:
            for i in Bulk_order:
                dict = {"order_id": i['orderID'], "order_side": i['side'], "order_price": i['price'],
                        "order_status": i['ordStatus']}
                self.col.insert_one(dict)
                print(dict)

        while True:
            try:
                for y in self.col.find():
                    take_order_id = y['order_id']
                    take_order_side = y['order_side']
                    take_order_price = y['order_price']
                    take_order_status = y['order_status']
                    time.sleep(0.03)
                    if take_order_status == "Filled" and take_order_side == "Buy":
                        take_sell_order = self.exchange.create_order(symbol=self.order_symbol, type=self.order_type,
                                                              side='sell',
                                                              amount=self.order_amonut_sell,
                                                              price=take_order_price + self.order_profit)
                        if "id" in take_sell_order:
                            if len(take_sell_order['id']) > 28:
                                myquery = {"order_id": take_order_id}
                                self.col.delete_one(myquery)
                                dict = {"order_id": take_sell_order['id'], "order_side": take_sell_order['info']['side'],
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
                                dict = {"order_id": take_buy_order['id'], "order_side": take_buy_order['info']['side'],
                                        "order_price": take_buy_order['price'],
                                        "order_status": take_buy_order['info']['ordStatus']}
                                self.col.insert_one(dict)
                                print(dict)

                    elif take_order_status == "Canceled" and take_order_side == "Buy":
                        take_buy_order = self.exchange.create_order(symbol=self.order_symbol, type=self.order_type,
                                                             side='buy',
                                                             amount=self.order_amonut_buy, price=take_order_price)

                        if "id" in take_buy_order:
                            if len(take_buy_order['id']) > 28:
                                myquery = {"order_id": take_order_id}
                                self.col.delete_one(myquery)
                                dict = {"order_id": take_buy_order['id'], "order_side": take_buy_order['info']['side'],
                                        "order_price": take_buy_order['price'],
                                        "order_status": take_buy_order['info']['ordStatus']}
                                self.col.insert_one(dict)
                                print(dict)

                    elif take_order_status == "Canceled" and take_order_side == "Sell":
                        take_sell_order = self.exchange.create_order(symbol=self.order_symbol, type=self.order_type,
                                                              side='sell',
                                                              amount=self.order_amonut_sell, price=take_order_price)

                        if "id" in take_sell_order:
                            if len(take_sell_order['id']) > 28:
                                myquery = {"order_id": take_order_id}
                                self.col.delete_one(myquery)
                                dict = {"order_id": take_sell_order['id'], "order_side": take_sell_order['info']['side'],
                                        "order_price": take_sell_order['price'],
                                        "order_status": take_sell_order['info']['ordStatus']}
                                self.col.insert_one(dict)
                                print(dict)

            except ccxt.NetworkError as e:
                print(self.exchange.id, 'network error:', str(e))
            except ccxt.ExchangeError as e:
                print(self.exchange.id, 'exchange error:', str(e))
            except Exception as e:
                print(self.exchange.id, str(e))
