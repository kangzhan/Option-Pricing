import scipy.stats as ss
import matplotlib.pyplot as plt
import numpy
import random
from WindPy import w


class Option:
    def __init__(self, underlying_code, underlying_price, expiration_time, risk_free, his_vol, structure='base',
                 sample_num=1000, frequency=2):
        self.underlying_code = underlying_code
        self.underlying_price = underlying_price
        self.expiration_time = expiration_time * frequency
        self.risk_free = risk_free / 252 / frequency
        self.structure = structure
        self.sample_num = sample_num
        self.buy_commission = 0.0000487 + 0.00002
        self.sell_commission = 0.001 + 0.0000487 + 0.00002
        self.delta_risk_tol = 0.05
        self.interest = 0
        self.money_cost = None
        self.option_pnl = None
        self.hedge_pnl = None
        self.commission = None
        self.money_occupied = None
        self.initial_equity = None
        self.delta_risk = None
        self.his_vol = numpy.array([his_vol] * self.sample_num)
        self.frequency = 1

    def set_delta_risk(self, r):
        self.delta_risk_tol = r

    def set_his_vol(self, date):
        c_series = numpy.array(w.wsd(self.underlying_code, "close", "ED-{}TD".format(self.expiration_time+252), date, "Fill=Previous;PriceAdj=F").Data[0])
        r_series = numpy.log(c_series[1:]) - numpy.log(c_series[:-1])
        self.his_vol = numpy.array([numpy.std(r_series[i:i+self.expiration_time]) for i in range(251)]) * numpy.sqrt(252)
        return c_series[-1]

    def reset(self, his_vol):
        self.his_vol = numpy.array([his_vol] * self.sample_num)

    def price(self, t, implied_vol, p):
        return p

    def delta(self, t, implied_vol, p):
        return p / p

    def path_generator(self, real_vol):
        path_ratio = numpy.exp(numpy.cumsum(self.risk_free - real_vol * real_vol / 2 + real_vol *
                                            ss.norm.rvs(size=[self.expiration_time + 1, self.sample_num]), axis=0))
        return self.underlying_price * path_ratio / path_ratio[0]

    def underlying_hedge_return(self, implied_vol):
        # option_pnl期权头寸亏损
        # underlying_pnl标的头寸收益
        # cash_interest占用资金利率
        # commission交易手续费
        # occupied_money占用资金
        implied_vol /= numpy.sqrt(252 * self.frequency)
        real_vol = self.sample_his_vol() / numpy.sqrt(252 * self.frequency)
        option_pnl = numpy.array([[0. for index in range(self.sample_num)] for t in range(self.expiration_time + 1)])
        underlying_pnl = numpy.array([[0. for index in range(self.sample_num)] for t in range(self.expiration_time + 1)])
        cash_interest = numpy.array([[0. for index in range(self.sample_num)] for t in range(self.expiration_time + 1)])
        commission = numpy.array([[0. for index in range(self.sample_num)] for t in range(self.expiration_time + 1)])
        money_occupied = numpy.array([[0. for index in range(self.sample_num)] for t in range(self.expiration_time + 1)])
        delta_risk = numpy.array([[0. for index in range(self.sample_num)] for t in range(self.expiration_time + 1)])
        delta = numpy.array([[0. for index in range(self.sample_num)] for t in range(self.expiration_time + 1)])
        last_underlying_price = numpy.array([self.underlying_price for index in range(self.sample_num)])
        last_option_price = self.price(0, implied_vol, last_underlying_price)
        last_underlying_position = numpy.array([0. for index in range(self.sample_num)])
        initial_equity = numpy.array([0. for index in range(self.sample_num)])
        initialized = False
        price_path = self.path_generator(real_vol)
        commission[0] = last_underlying_position * last_underlying_price * self.buy_commission
        for t in range(self.expiration_time):
            underlying_price = price_path[t]
            option_price = self.price(t, implied_vol, underlying_price)
            delta = self.delta(t, implied_vol, underlying_price)
            if not initialized:
                initial_equity = underlying_price * delta * (delta > 0.3) + underlying_price * 0.3 * (delta < 0.3)
                initialized = True
            position_change = (numpy.abs(delta - last_underlying_position) > self.delta_risk_tol) \
                              * (delta - last_underlying_position)
            underlying_position = last_underlying_position + position_change
            delta_risk[t] = numpy.abs(delta - last_underlying_position - position_change)
            option_pnl[t] = option_price - last_option_price
            underlying_pnl[t] = (underlying_price - last_underlying_price) * last_underlying_position
            commission[t + 1] = position_change * (position_change > 0) * self.buy_commission * underlying_price - \
                                position_change * (position_change < 0) * self.sell_commission * underlying_price
            if not t:
                money_occupied[t] = position_change * (position_change > 0) * (1 + self.buy_commission) * underlying_price + \
                              position_change * (position_change < 0) * (1 - self.sell_commission) * underlying_price
            else:
                money_occupied[t] = position_change * (position_change > 0) * (1 + self.buy_commission) * underlying_price + \
                              position_change * (position_change < 0) * (1 - self.sell_commission) * underlying_price + money_occupied[t - 1]
            cash_interest[t] = money_occupied[t] * self.interest
            last_underlying_price = underlying_price
            last_option_price = option_price
            last_underlying_position = underlying_position
        t = self.expiration_time - 1
        underlying_price = price_path[t]
        option_price = self.price(t, implied_vol, underlying_price)
        option_pnl[t] = option_price - last_option_price
        underlying_pnl[t] = (underlying_price - last_underlying_price) * last_underlying_position
        commission[t + 1] = last_underlying_position * underlying_price * self.sell_commission
        self.commission = commission
        self.option_pnl = option_pnl
        self.hedge_pnl = underlying_pnl
        self.money_cost = cash_interest
        self.money_occupied = money_occupied
        self.initial_equity = initial_equity
        self.delta_risk = delta_risk
        return real_vol

    def show_sim_result(self):
        plt.figure(1)
        plt.subplot(221)
        plt.hist(numpy.sum(-self.option_pnl, axis=0) + numpy.sum(-self.hedge_pnl, axis=0) + numpy.sum(-self.commission,
                                                                                                      axis=0), 10,
                 normed=True)
        plt.subplot(221).set_title('total earn')
        plt.subplot(222)
        plt.hist(numpy.min(numpy.cumsum(-self.option_pnl + self.hedge_pnl + self.commission[:-1], axis=0), axis=0), 10,
                 normed=True)
        plt.subplot(222).set_title('max loss')
        plt.subplot(223)
        plt.hist(numpy.max(self.money_occupied, axis=0), 10, normed=True)
        plt.subplot(223).set_title('max occupied cash')
        re = (-numpy.sum(self.option_pnl, axis=0) + numpy.sum(self.hedge_pnl, axis=0) - numpy.sum(self.commission,
                                                                                                   axis=0)) / numpy.max(
            self.money_occupied, axis=0)
        plt.subplot(224)
        plt.hist(re, 10, normed=True)
        plt.subplot(224).set_title('earn over occupied cash')
        plt.show()

    def sample_his_vol(self, recent=21):
        return numpy.array([self.his_vol[-1-random.randrange(recent)] for index in range(self.sample_num)])

    def pricing(self, equity_ratio=1.2, tolerance=0.1, message_box=None):
        current_implied_vol = self.his_vol[-1] + tolerance * (max(self.his_vol) - min(self.his_vol))
        while True:
            his_vol_sample = self.underlying_hedge_return(current_implied_vol)
            re = numpy.mean((-numpy.sum(self.option_pnl, axis=0) + numpy.sum(self.hedge_pnl, axis=0) +
                -numpy.sum(self.commission, axis=0)) / self.initial_equity) / equity_ratio
            p_win = sum((-numpy.sum(self.option_pnl, axis=0) + numpy.sum(self.hedge_pnl, axis=0) +
                numpy.sum(self.commission, axis=0)) > 0 ) / self.sample_num
            if re * 252 / self.expiration_time > 0.08 and p_win > 0.75:
                break
            current_implied_vol += 0.01
        plt.figure()
        plt.subplot(1,2,1)
        plt.hist((-numpy.sum(self.option_pnl, axis=0) + numpy.sum(self.hedge_pnl, axis=0) +
                -numpy.sum(self.commission, axis=0)) * 252 / self.expiration_time / self.initial_equity / equity_ratio , 100, normed=True)
        plt.title('distribution of return')
        plt.subplot(1,2,2)
        plt.hist(numpy.max(self.money_occupied, axis=0) / self.initial_equity, 100, normed=True)
        plt.title('distribution of money occupied')
        if message_box:
            message_box.showinfo('Pricing Result', 'Price:{}\nHV:{}\nIV:{}\nRisk Ratio:{}\nMax Risk:{}\nAverage Return:{}\nWinning Rate:{}\n80% Money Occupied Percentile:{}'.format(self.price(0,
            current_implied_vol , self.underlying_price), numpy.mean(his_vol_sample),
            current_implied_vol, equity_ratio, numpy.max(self.delta_risk), re * 252 / self.expiration_time, p_win, numpy.percentile(numpy.max(self.money_occupied, axis=0) / self.initial_equity, 80)))
            print('Pricing Result',
                                 'Price:{}\nHV:{}\nIV:{}\nRisk Ratio:{}\nMax Risk:{}\nAverage Return:{}\nWinning Rate:{}\n80% Money Occupied Percentile:{}'.format(
                                     self.price(0,
                                                current_implied_vol, self.underlying_price), numpy.mean(his_vol_sample),
                                     current_implied_vol, equity_ratio, numpy.max(self.delta_risk),
                                     re * 252 / self.expiration_time, p_win,
                                     numpy.percentile(numpy.max(self.money_occupied, axis=0) / self.initial_equity,
                                                      80)))
        plt.show()


class EuroCall(Option):
    def __init__(self, underlying_code, underlying_price, expiration_time, risk_free, his_vol, strike, structure='EuroCall',
                 sample_num=1000, frequency=2):
        Option.__init__(self, underlying_code, underlying_price, expiration_time, risk_free, his_vol, structure, sample_num, frequency)
        self.strike = strike

    def price(self, t, implied_vol, p):
        if t != self.expiration_time:
            nd1 = ss.norm.cdf((numpy.log((p / self.strike)) + (self.risk_free + implied_vol * implied_vol / 2) *
                               (self.expiration_time - t)) / implied_vol / numpy.sqrt(self.expiration_time - t))
            nd2 = ss.norm.cdf((numpy.log((p / self.strike)) + (self.risk_free - implied_vol * implied_vol / 2) *
                               (self.expiration_time - t)) / implied_vol / numpy.sqrt(self.expiration_time - t))
        else:
            nd1 = nd2 = numpy.int(p > self.strike)
        return nd1 * p - nd2 * numpy.exp((self.expiration_time - t) * self.risk_free) * self.strike

    def delta(self, t, implied_vol, p):
        if t != self.expiration_time:
            nd1 = ss.norm.cdf((numpy.log((p / self.strike)) + (self.risk_free + implied_vol * implied_vol / 2) *
                               (self.expiration_time - t)) / implied_vol / numpy.sqrt(self.expiration_time - t))
            nd2 = ss.norm.cdf((numpy.log((p / self.strike)) + (self.risk_free - implied_vol * implied_vol / 2) *
                               (self.expiration_time - t)) / implied_vol / numpy.sqrt(self.expiration_time - t))
        else:
            nd1 = nd2 = numpy.int(p > self.strike)
        return nd1


class EuroPut(Option):
    def __init__(self, underlying_code, underlying_price, expiration_time, risk_free, his_vol, strike, structure='EuroCall',
                 sample_num=1000, frequency=2):
        Option.__init__(self, underlying_code, underlying_price, expiration_time, risk_free, his_vol, structure, sample_num, frequency)
        self.strike = strike

    def price(self, t, implied_vol, p):
        if t != self.expiration_time:
            nd1 = ss.norm.cdf(-(numpy.log((p / self.strike)) + (self.risk_free + implied_vol * implied_vol / 2) *
                               (self.expiration_time - t)) / implied_vol / numpy.sqrt(self.expiration_time - t))
            nd2 = ss.norm.cdf(-(numpy.log((p / self.strike)) + (self.risk_free - implied_vol * implied_vol / 2) *
                               (self.expiration_time - t)) / implied_vol / numpy.sqrt(self.expiration_time - t))
        else:
            nd1 = nd2 = -numpy.int(p > self.strike)
        return -nd1 * p + nd2 * numpy.exp((self.expiration_time - t) * self.risk_free) * self.strike

    def delta(self, t, implied_vol, p):
        if t != self.expiration_time:
            nd1 = ss.norm.cdf(-(numpy.log((p / self.strike)) + (self.risk_free + implied_vol * implied_vol / 2) *
                               (self.expiration_time - t)) / implied_vol / numpy.sqrt(self.expiration_time - t))
            nd2 = ss.norm.cdf(-(numpy.log((p / self.strike)) + (self.risk_free - implied_vol * implied_vol / 2) *
                               (self.expiration_time - t)) / implied_vol / numpy.sqrt(self.expiration_time - t))
        else:
            nd1 = nd2 = -numpy.int(p > self.strike)
        return nd1
