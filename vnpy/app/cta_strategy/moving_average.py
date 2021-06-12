from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)


class MVA(CtaTemplate):
    """"""

    author = "Allen"

    mva_1 = 20
    mva_2 = 60
    fixed_size = 1


    parameters = [
        "mva_1",
        "mva_2",
        "fixed_size"
    ]
    variables = [
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(10)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.cancel_all()

        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return
        print(bar.close_price)
        if self.pos == 0:
            if self.am.close_array[-self.mva_1-1:-1].mean() > self.am.close_array[-self.mva_2-1:-1].mean():
                self.buy(bar.close_price + 1, self.fixed_size)
            elif self.am.close_array[-self.mva_1-1:-1].mean() < self.am.close_array[-self.mva_2-1:-1].mean():
                self.short(bar.close_price - 1, self.fixed_size)
            else:
                pass

        elif self.pos > 0:
            if self.am.close_array[-self.mva_1-1:-1].mean() < self.am.close_array[-self.mva_2-1:-1].mean():
                self.sell(bar.close_price - 1, self.fixed_size)
            else:
                pass

        elif self.pos < 0:
            if self.am.close_array[-self.mva_1-1:-1].mean() > self.am.close_array[-self.mva_2-1:-1].mean():
                self.cover(bar.close_price + 1, self.fixed_size)
            else:
                pass

        else:
            pass

        self.put_event()

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass
