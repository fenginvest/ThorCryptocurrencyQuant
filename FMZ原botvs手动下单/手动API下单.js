
var kaiduo = false; 
var kaikong = false;
var pingduo = false;
var pingkong = false;
var quxiao = false;
var price = 0;                          
var amount = 0;                         

function get_Command(){                                                       
    var keyValue = 0;                                                         
    var way = null;                                                           
    var cmd = GetCommand();                                                   
    if (cmd) {
        Log("按下了按钮：",cmd);                                               
        arrStr = cmd.split(":");                                                                                                     
        if(arrStr.length === 2){                                              
            jsonObjStr = '{' + '"' + arrStr[0] + '"' + ':' + arrStr[1] + '}';                                                                               
            jsonObj = JSON.parse(jsonObjStr);                                 
            for(var key in jsonObj){                                          
                keyValue = jsonObj[key];
            }                                      
            if(arrStr[0] == "价格"){                                   
                way = 0;
            }
            if(arrStr[0] == "数量"){
                way = 1;
            }
        } else if (arrStr.length === 1){                                        
            if(cmd == "买入开多"){ 
                way = 2;
            }
            if(cmd == "卖出开空"){
                way = 3;
            }
            if(cmd == "买入平空"){
                way = 4;
            }
            if(cmd == "卖出平多"){
                way = 5;
            }
            if(cmd == "取消挂单"){
                way = 6;
            }
        }else{
            throw "error:" + cmd + "--" + arrStr;
        }
        switch(way){                                                          
            case 0:                                                          
                price = keyValue; 
                break;
            case 1:                                                           
                amount = keyValue;
                break;
            case 2:                                                           
                kaiduo = true;
                break;
            case 3:
                kaikong = true;
                break;
            case 4:
                pingkong = true;
                break;
            case 5:
                pingduo = true;
                break;
            case 6:
                quxiao = true;
                break;
            default: break;
        }
    }
}
function main(){
    while(true){
        var positions = _C(exchange.GetPosition);
        var account = _C(exchange.GetAccount);
        var orders = _C(exchange.GetOrders);
        var table = {
        type : "table",
        title : "持仓详情",
        cols : ["当前合约","持仓方向","持仓数量","持仓均价","浮动盈亏","可用保证金"],
        rows : [],
        }
        var table1 = {
        type : "table",
        title : "挂单详情",
        cols : ["当前合约","挂单方向","挂单数量","挂单价格"],
        rows : [],
        }
        for (var i = 0; i < positions.length; i++){
            table.rows.push([positions[i].ContractType, (positions[i].Type > 0?"卖空 #FF0000 ":"开多 #4D4DFF ") ,positions[i].Amount ,_N(positions[i].Price) ,_N(positions[i].Profit) ,_N(account.Stocks,4)])
        }
        for (var i = 0; i < orders.length; i++){
            table1.rows.push([orders[i].ContractType, (orders[i].Type > 0?"卖空 #FF0000 ":"开多 #4D4DFF ") ,orders[i].Amount ,_N(orders[i].Price)])
        }                  
        LogStatus("当前时间:", _D(), "\n", '`' + JSON.stringify(table) + '`' ,"\n" + '`' + JSON.stringify(table1) + '`' ,"\n");
        Sleep(10000) 

        exchange.SetContractType(["XBTUSD", "XBTM19", "XBTU19", "ETHUSD"][ContractTypeIdx]);
        exchange.SetMarginLevel([0 , 5 , 10 , 15][MarginLevelIdx]);
        get_Command();
        if(beidong){                                                                     
            if(kaiduo === true){
                exchange.SetDirection("buy"); 
                var id =exchange.IO("api", "POST", "/api/v1/order", "symbol="+ (["XBTUSD", "XBTM19", "XBTU19", "ETHUSD"][ContractTypeIdx]) +"&side=Buy&execInst=ParticipateDoNotInitiate&price=" + price +"&orderQty=" + amount);
                exchange.Log( LOG_TYPE_BUY , id.orderID ,id.price ,id.orderQty ,id.workingIndicator?"挂单成功":"挂单未成功")
                kaiduo = false;
                Sleep(2000);                                                                   
            }
            if(kaikong === true){
                exchange.SetDirection("sell"); 
                var id =exchange.IO("api", "POST", "/api/v1/order", "symbol="+ (["XBTUSD", "XBTM19", "XBTU19", "ETHUSD"][ContractTypeIdx]) +"&side=Sell&execInst=ParticipateDoNotInitiate&price=" + price +"&orderQty=" + amount);
                exchange.Log( LOG_TYPE_BUY , id.orderID ,id.price ,id.orderQty ,id.workingIndicator?"挂单成功":"挂单未成功")
                kaikong = false;
                Sleep(2000);                                                                    
            }
            if(pingduo === true){
                exchange.SetDirection("closebuy"); 
                var id =exchange.IO("api", "POST", "/api/v1/order", "symbol="+ (["XBTUSD", "XBTM19", "XBTU19", "ETHUSD"][ContractTypeIdx]) +"&side=Sell&execInst=ParticipateDoNotInitiate&price=" + price +"&orderQty=" + amount);
                exchange.Log( LOG_TYPE_BUY , id.orderID ,id.price ,id.orderQty ,id.workingIndicator?"挂单成功":"挂单未成功")
                pingduo = false;
                Sleep(2000);                                                                    
            }
            if(pingkong === true){
                exchange.SetDirection("closesell"); 
                var id =exchange.IO("api", "POST", "/api/v1/order", "symbol="+ (["XBTUSD", "XBTM19", "XBTU19", "ETHUSD"][ContractTypeIdx]) +"&side=Buy&execInst=ParticipateDoNotInitiate&price=" + price +"&orderQty=" + amount);
                exchange.Log( LOG_TYPE_BUY , id.orderID ,id.price ,id.orderQty ,id.workingIndicator?"挂单成功":"挂单未成功")
                pingkong = false;
                Sleep(2000);                                                                    
            }
        } else {
            if(kaiduo === true){
                exchange.SetDirection("buy"); 
                exchange.Buy(price, amount);
                kaiduo = false;
                Sleep(2000)                                                                   
            }
            if(kaikong === true){
                exchange.SetDirection("sell"); 
                exchange.Sell(price, amount);
                kaikong = false;
                Sleep(2000);                                                                    
            }
            if(pingduo === true){
                exchange.SetDirection("closebuy"); 
                exchange.Sell(price, amount);
                pingduo = false;
                Sleep(2000);                                                                    
            }
            if(pingkong === true){
                exchange.SetDirection("closesell"); 
                exchange.Buy(price, amount);
                pingkong = false;
                Sleep(2000);                                                                    
            }
        }
        if(quxiao === true){

            for (var j = 0; j < orders.length; j++) {
                exchange.CancelOrder(orders[j].Id ,"已撤销");
            }
            quxiao = false;
            Sleep(2000);
        } 
    }
}