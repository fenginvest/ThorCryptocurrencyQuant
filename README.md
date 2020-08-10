# ThorCryptoCurrency Strategy Library

 
<br>
<br>
<p align="center">
  <img src ="http://thorquant.com/Thor-Quant.png"/>
</p>
<br>
<br>

 * Thor Strategy Library策略可运行的数字货币交易所（其他交易所也可适配后运行）

        * BitMEX ：数字货币期货、永续合约

        * Bybit ：数字货币永续合约

        * Binance ：数字货币现货

        * Binance永续 ：数字货币永续合约

        * OKEX ：数字货币现货

        * OKEX永续 ：数字货币永续合约

        * OKEX期货 ：数字货币期货

        * Huobi ：数字货币现货

        * Huobi期货 ：数字货币期货

        * Huobi永续 ：数字货币永续 

        * Bitfinex ：数字货币现货

        * Coinbase ：数字货币现货

        * Bitstamp ：数字货币现货


## 策略介绍

- 平衡策略：
  - 策略原理： 按照当前的 BTC 的价值，保留对应价值的USDT, 假设在比特币价格 10000USDT 时持有 1BTC 和 10000USDT
  - 1. 当BTC行情下跌,用 (当前持有USDT价值 - 当前持有BTC价值 )/2 个USDT 买入 (当前持有USDT价值 - 当前持有BTC价值)/2/当前BTC价格 个BTC
  - 2. 当BTC行情上涨,卖出 (当前持有BTC价值 - 当前持有USDT价值) / 2 个BTC
  - 就这样,不管BTC是上涨还是下跌,始终动态保持账户内 USDT 和 BTC 的价值相等.如果BTC贬值了就买一些,BTC升值了,就卖一些，好像天平一样.
  - 在不断的买进和卖出过程中,只要行情有波动，就可以在波动中获取盈利！
  - 由于现货市场不管是Maker还是Taker都会有手续费.在大多数永续合约交易市场中,Maker是交易所给你手续费的！所以在永续市场中策略可以更好的展现能力.

- 网格策略：
  - <img src ="http://thorquant.com/网格交易图片.png"/>
  - 网格交易是大家非常熟知的一种策略，原理就是上面这张图，我的这套网格交易跟其他不同的是，这是用在跨期套利里面的网格交易
  - 策略原理： 

- 吃针策略：

- Boll指标策略：

- 对敲策略：

- 套利策略：



## 使用说明
- 策略库内所有代码，都会定期进行更新，以适应交易所升级与变更
- 所有策略开箱即用，填写自己的APIKey 与 Sercet，填写参数运行即可
- 每种策略有不同对应交易所，同一策略根据命名区分交易所，运行时注意查看
- 主流交易所借助CCXT实现，非主流交易所也适配封装了所有公有私有API，可直接运行
- 非主流交易所数据格式返回与CCXT数据格式一致，方便数据分析
- 运行环境Python3,CCXT需自行安装（pip install ccxt）
- Python建议使用linux系统，借助tmux可以较方便的监控策略运行
- JavaScript策略基于FMZ运行（原botvs）



## 贡献代码

ThorCryptoCurrency Strategy Library接受第三方策略开源:

- 因交易策略的特殊性，不进行直接提交PR方式，如有朋友也想开源自己的交易策略，请加我的微信号：3404034
- 在经过对策略的验证之后由我上传添加到开源库当中，并且会根据作者意愿对作者进行展示！




## 项目捐赠

过去2年中在国内的社区有偿无偿帮助很多用户写过数字货币策略，最近打算把这两年中的积累开源放出来，并在后续进行更新维护，非常感谢用户的认可与肯定并进行捐赠，
所有捐赠都会投入到策略库的完善之中，用于支持与壮大数字货币量化的发展！

先强调一下：**本项目里面的策略都是开源的，可以无偿免费使用，并没有强制捐赠的要求！！！**

捐赠方式：
- 支付宝：block@163.com（*裕峰）
- Bitcoin wallet：1CPY1sUgLxYYNYMWy3ChpW5pmveiBnFMus
- Ethereum wallet：0x545fbfbbc943adf29005aff1dfe39a91e282dcb7


我们会长期维护捐赠清单，请在捐赠时备注项目名称与捐赠人姓名


## 版权说明

MIT
