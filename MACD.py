import pandas

Current_stock = 0
# Put any initialization logic here.  The context object will be passed to
# the other methods in your algorithm.
def initialize(context):
    context.sids = [sid(8655), sid(5923), sid(7797), sid(8229), sid(5484), sid(7488), sid(3136), sid(438), sid(3806), sid(3499)]
    context.long = {}
    context.short = {}
    context.stop_loss = 1
    context.take_profit = 3
    context.max_notional = 10000.1
    context.min_notional = -10000.0
    set_commission(commission.PerTrade(cost=7))
    context.database = {}

# Will be called on every trade event for the securities you specify.
def handle_data(context, data):
    acc_fast_ema=0
    acc_slow_ema=0
    acc_MACD=0

    for stock in context.sids:
        global Current_stock
        Current_stock = int(str(stock)[9:-1])

        if Current_stock not in context.database:
            context.database[Current_stock] = {'ema12': [], 'ema26': []}

        fast_ema = get_EMA12(data)
        slow_ema = get_EMA26(data)

        if slow_ema == None:
            return
        context.database[stock]['ema12'].append(fast_ema)
        context.database[stock]['ema26'].append(slow_ema)
        diffs = map(get_diff, context.database[stock]['ema26'][-20:-1], context.database[stock]['ema12'][-20:-1])

        series = pandas.Series(diffs)
        signal = pandas.stats.moments.ewma(series, span=9, min_periods=9).values
        try:
            signal = signal[-1]
        except:
            return
        # signal = signal[-1]

        acc_fast_ema += fast_ema
        acc_slow_ema += slow_ema
        acc_MACD += signal
        # record(EMA12=fast_ema, EMA26=slow_ema)

        notional = context.portfolio.positions[stock].amount * data[stock].price

        if stock not in context.long and stock not in context.short and notional < context.max_notional and notional > context.min_notional:
            if signal > 0:
                order(stock, 100)
                log.info("Long %f, %s" %(data[stock].price, stock))
                context.long[stock] = data[stock].price
            else:
                order(stock, -100)
                log.info("Short %f, %s" %(data[stock].price, stock))
                context.short[stock] = data[stock].price

        if stock in context.long:
            if context.long[stock] - data[stock].price > context.stop_loss:
                order(stock, -100)
                log.info("LONG Stop loss at %f, %s" %(data[stock].price, stock))
                context.long.pop(stock)
            elif data[stock].price - context.long[stock] > context.take_profit:
                order(stock, -100)
                log.info("LONG Take profit at %f, %s" %(data[stock].price, stock))
                context.long.pop(stock)
        elif stock in context.short:
             if data[stock].price - context.short[stock] > context.stop_loss:
                order(stock, 100)
                log.info("SHORT Stop loss at %f, %s" %(data[stock].price, stock))
                context.short.pop(stock)
             elif context.short[stock] - data[stock].price > context.take_profit:
                order(stock, 100)
                log.info("SHORT Take profit at %f, %s" %(data[stock].price, stock))
                context.short.pop(stock)


    record(MACD=acc_MACD/10)
    # record(EMA12=acc_fast_ema/10, EMA26=acc_slow_ema/10)

@batch_transform(window_length=12)
def get_EMA12(datapanel):
    global Current_stock
    prices=datapanel['price']
    # print prices
    EMA = pandas.stats.moments.ewma(prices, span=12)
    return EMA[Current_stock][11]

@batch_transform(window_length=26)
def get_EMA26(datapanel):
    global Current_stock
    prices=datapanel['price']
    EMA = pandas.stats.moments.ewma(prices, span=26)
    return EMA[Current_stock][25]

def get_diff(slow, fast):
    if fast == None or slow == None:
        return None
    else:
        return fast - slow
