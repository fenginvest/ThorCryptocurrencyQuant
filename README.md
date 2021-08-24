# ThorCryptoCurrency Strategy Library

 
<br>
<br>
<br>
<br>


 * 策略在运行之前将文件名改为英文,为了方便大家理解我特意改成的中文
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
- 策略优化方案, 思路讨论或者遇到问题请提交Issues




## 联系方式

微信/QQ : 3404034


## 版权说明

MIT
