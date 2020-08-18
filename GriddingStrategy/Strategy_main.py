"""
运行策略入口文件，本策略运行bitmex XBT 跟 ETH交易对
填写时交易品种 按照 XBT/USD 格式填写，如需交易其他品种 需在策略，websocket 做适配 方便管理运行
apiKey secret 填写自己的
策略运行后 直接远程查看数据库  就可观察订单状态

"""

from GriddingStrategy.bitmex_websocket._websocket import BitmexWebsocket
from GriddingStrategy.okex_websocket._okex_websocket import OKEXWebsocket
from GriddingStrategy.Quant import Transaction

if __name__ == '__main__':
    # 目前兼容 bitmex  OKEX 永续合约 交易对填写时 币本位填写BTC/USD  U本位填写BTC/USDT
    # Binance还在更新兼容中， 更新后上传
    exchange = 'bitmex'   # bitmex  OKEX
    apiKey = ''
    secret = ''
    password = ''  # OKEX需要填写 交易密码，其他交易所不需要 为空
    order_symbol = 'ETH/USD'  # 交易品种  BTC  ETH主流的兼容，按照CCXT格式填写，其他的未做兼容，可在Quant文件中自行添加兼容
    num_buy = 3  # 买网格数量   网格可以是双向，可以是单向， 单向时 另一方 设置为 0
    num_sell = 1  # 卖网格数量
    order_spread = 0.5  # 网格步长
    order_profit = 0.5  # 利润（当挂单成交后，反手挂单间隔）
    order_amonut_buy = 30  # 买单挂单数量  OKEX数量单位是 /张   Bitmex数量单位是 /美元   Binance数量单位是/token
    order_amonut_sell = 30  # 卖单挂单数量

    order_type = 'limit'  # 平仓时挂单方式 此参数为Bitmex特有，其他交易所可不填，为空

    if exchange == 'bitmex':
        bitmex_ws = BitmexWebsocket(host="wss://www.bitmex.com/realtime", ping_interval=1, key=apiKey, secret=secret,
                                    _symbol=order_symbol, db_exchange=exchange)
        bitmex_ws.start()

    if exchange == 'OKEX':
        okex_ws = OKEXWebsocket(host="wss://real.okex.com:8443/ws/v3", ping_interval=10, key=apiKey, secret=secret,
                                _symbol=order_symbol, db_exchange=exchange, password=password)
        okex_ws.start()

    start_ = Transaction(order_symbol, apiKey, secret, num_buy, num_sell, order_spread, order_profit,
                         order_amonut_buy, order_amonut_sell, exchange=exchange, password=password,
                         order_type=order_type)
    start_.start_transaction()
