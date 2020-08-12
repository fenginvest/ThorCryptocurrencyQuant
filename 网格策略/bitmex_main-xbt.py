"""
运行策略入口文件，本策略运行bitmex XBT 跟 ETH交易对
填写时交易品种 按照 XBT/USD 格式填写，如需交易其他品种 需在策略，websocket 做适配 方便管理运行
apiKey secret 填写自己的
策略运行后 直接远程查看数据库  就可观察订单状态

"""

from bitmex_websocket._websocket import BitmexWebsocket
from Quant import Bitmextransaction

if __name__ == '__main__':

    exchange = 'bitmex'
    apiKey = ''
    secret = ''
    order_symbol = 'ETH/USD'  # 交易品种
    order_type = 'limit'  # 平仓时挂单方式
    num_buy = 3  # 买网格数量
    num_sell = 1  # 卖网格数量
    order_spread = 0.5  # 网格步长
    order_profit = 0.5  # 利润
    order_amonut_buy = 30  # 买单挂单数量
    order_amonut_sell = 30  # 卖单挂单数量

    bitmex_ws = BitmexWebsocket(host="wss://www.bitmex.com/realtime", ping_interval=1, key=apiKey, secret=secret,
                                _symbol=order_symbol, db_exchange=exchange)
    bitmex_ws.start()
    start_ = Bitmextransaction(order_symbol, order_type, apiKey, secret, num_buy, num_sell, order_spread, order_profit,
                               order_amonut_buy, order_amonut_sell, exchange=exchange)
    start_.start_transaction()
