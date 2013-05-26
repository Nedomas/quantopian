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

# Will be called on every trade event for the securities you specify.
def handle_data(context, data):
    acc_middle_bb=0
    acc_upper_bb=0
    acc_lower_bb=0
    acc_price=0

    for stock in context.sids:
        middle_bb = data[stock].mavg(20)
        bb_stddev = data[stock].stddev(20)
        if middle_bb == None or bb_stddev == None:
            return

        bb_stddev = data[stock].stddev(20)
        upper_bb = middle_bb + 2*bb_stddev
        lower_bb = middle_bb - 2*bb_stddev

        acc_middle_bb += middle_bb
        acc_upper_bb += upper_bb
        acc_lower_bb += lower_bb
        acc_price += data[stock].price

        # record(MiddleBB=middle_bb, UpperBB=upper_bb, LowerBB=lower_bb)

        notional = context.portfolio.positions[stock].amount * data[stock].price

        if stock not in context.long and stock not in context.short and notional < context.max_notional and notional > context.min_notional:
            if data[stock].price > upper_bb:
                order(stock, 100)
                log.info("Long %f, %s" %(data[stock].price, stock))
                context.long[stock] = data[stock].price
            elif data[stock].price < lower_bb:
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

    record(MiddleBB=acc_middle_bb/10, UpperBB=acc_upper_bb/10, LowerBB=acc_lower_bb/10, Price=acc_price/10)

@batch_transform(window_length=30)
def get_EMA(datapanel):
    global Current_stock
    prices=datapanel['price']
    EMA = pandas.stats.moments.ewma(prices, span=20)
    return EMA[Current_stock][29]