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
    context.highs = {}
    context.lows = {}
    context.K = {}
    context.full_K = {}

# Will be called on every trade event for the securities you specify.
def handle_data(context, data):
     # %K = (Current Close - Lowest Low)/(Highest High - Lowest Low) * 100
    # %D = 3-day SMA of %K
    # Lowest Low = lowest low for the look-back period
    # Highest High = highest high for the look-back period
    # %K is multiplied by 100 to move the decimal point two places
    #
    # Full %K = Fast %K smoothed with X-period SMA
    # Full %D = X-period SMA of Full %K
    #
    # Input 14, 3
    # Returns [full %K, full %D]
    acc_full_K=0
    acc_full_D=0

    for stock in context.sids:
        if stock not in context.highs:
            context.highs[stock] = []
        if stock not in context.lows:
            context.lows[stock] = []
        if stock not in context.K:
            context.K[stock] = []
        if stock not in context.full_K:
            context.full_K[stock] = []

        context.highs[stock].append(data[stock].high)
        context.lows[stock].append(data[stock].low)
        try:
            K = (data[stock].price - min(context.lows[stock][-14:-1])) / (max(context.highs[stock][-14:-1]) - min(context.lows[stock][-14:-1])) * 100
        except:
            K = 0
        context.K[stock].append(K)

        full_K = pandas.stats.moments.ewma(pandas.Series(context.K[stock]), span=5).values[-1]
        context.full_K[stock].append(full_K)
        full_D = pandas.stats.moments.ewma(pandas.Series(context.full_K[stock]), span=3).values[-1]

        acc_full_K += full_K
        acc_full_D += full_D

        notional = context.portfolio.positions[stock].amount * data[stock].price

        if stock not in context.long and stock not in context.short and notional < context.max_notional and notional > context.min_notional:
            if full_K < 20 and full_D < 20:
                order(stock, 100)
                log.info("Long %f, %s" %(data[stock].price, stock))
                context.long[stock] = data[stock].price
            elif full_K > 80 and full_D > 80:
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

    record(FullK5=acc_full_K/10, FullD3=acc_full_D/10)
# acc