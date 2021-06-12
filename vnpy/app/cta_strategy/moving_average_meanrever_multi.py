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
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, VARCHAR, TIMESTAMP
from datetime import datetime
class MVA_Meanrever_mul(CtaTemplate):
    """"""

    author = "Allen"

    mva_1 = 10
    mva_2 = 70
    fixed_size = 1
    trailing_percent_long_loose = 20
    trailing_percent_short_loose = 15
    short_quantile = 95
    buy_quantile = 5
    mean_rever_range = 100

    intra_trade_high = 0
    intra_trade_low = 0

    parameters = [
        "mva_1",
        "mva_2",
        "fixed_size",
        "trailing_percent_long_loose",
        "trailing_percent_short_loose",
        "short_quantile",
        "buy_quantile",
        "mean_rever_range"
    ]

    variables = [
        "intra_trade_high",
        "intra_trade_low"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()

        engine = create_engine('')
        self.signal = pd.read_sql(f"SELECT * FROM `dbbardata` WHERE `symbol` = \'Bond_price\';", engine)  # 从数据库调取标的所有数据
        self.signal['datetime'] = self.signal['datetime'].apply(lambda x: x.to_pydatetime().date())
        self.signal = self.signal.reset_index(drop=True)

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

        signal_m = self.signal[self.signal['datetime'] <= bar.datetime.date()]['close_price']

        #均线开仓
        if self.pos == 0:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price
            if signal_m[-self.mva_1-1:-1].mean() > signal_m[-self.mva_2-1:-1].mean():
                self.buy(bar.close_price + 500, self.fixed_size)
            elif signal_m[-self.mva_1-1:-1].mean() < signal_m[-self.mva_2-1:-1].mean():
                self.short(bar.close_price - 500, self.fixed_size)
            else:
                pass

        elif self.pos > 0:
            if signal_m[-self.mva_1-1:-1].mean() < signal_m[-self.mva_2-1:-1].mean():
                self.sell(bar.close_price - 500, self.fixed_size)
                self.short(bar.close_price - 500, self.fixed_size)

            else:
                pass

        elif self.pos < 0:
            if signal_m[-self.mva_1-1:-1].mean() > signal_m[-self.mva_2-1:-1].mean():
                self.cover(bar.close_price + 500, self.fixed_size)
                self.buy(bar.close_price + 500, self.fixed_size)

            else:
                pass
        else:
            pass

        #止损条件
        if self.pos > 0:
            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)

            long_stop_loose = self.intra_trade_high * \
                (1 - self.trailing_percent_long_loose / 1000)
            self.sell(long_stop_loose, abs(self.pos), stop=True)

        elif self.pos < 0:
            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)

            short_stop_loose = self.intra_trade_low * \
                (1 + self.trailing_percent_short_loose / 1000)
            self.cover(short_stop_loose, abs(self.pos), stop=True)

        else:
            pass

        #均值回归策略
        if signal_m[-self.mean_rever_range:].mean() > np.quantile(signal_m[:], self.short_quantile/100):
            if self.pos > 0:
                self.cancel_all()
                self.sell(bar.close_price - 500, self.fixed_size)
            elif self.pos == 0:
                self.cancel_all()
                self.short(bar.close_price - 500, self.fixed_size)
            else:
                pass
        elif signal_m[-self.mean_rever_range:].mean() < np.quantile(signal_m[:], self.buy_quantile/100):
            if self.pos < 0:
                self.cancel_all()
                self.cover(bar.close_price + 500, self.fixed_size)
            elif self.pos == 0:
                self.cancel_all()
                self.buy(bar.close_price + 500, self.fixed_size)
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
