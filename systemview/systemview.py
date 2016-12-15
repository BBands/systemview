#!/usr/bin/env python
"""
DESCRIPTION
    SystemView: Dispaly trading system metrics

AUTHOR
    SystemView: John Bollinger <BBands@BollingerBands.com>

TODO
    Please see the TODO file
"""

# do division as expected and use 3.n print formatting
from __future__ import (division, print_function)

# import external libraries
import sys                                          # system functions
import datetime                                     # date functions
import numpy as np                                  # numpy
import matplotlib.pyplot as plt                     # pyplot
import matplotlib.dates as mdates                   # dates for pyplot
from matplotlib.ticker import FormatStrFormatter    # format graph axes
from dateutil.relativedelta import relativedelta    # date math
try:                                                # Tkinter for Python2
    import Tkinter as tk
except ImportError:                                 # tkinter for Python3
    import tkinter as tk
# import our system variables from parameters.py
import parameters as param

# version number
__author__ = "John Bollinger"
__version__ = "0.1"

# range/xrange patch for python 2 and 3 compatibility
if sys.version_info >= (3, 0):
    def xrange(*args, **kwargs):
        return iter(range(*args, **kwargs))

def yahoo_to_iso_date(date):
    """Convert Yahoo!'s date to datetime object."""
    date = date.split('-')
    day = int(date[0])
    month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug',
             'Sep', 'Oct', 'Nov', 'Dec'].index(date[1]) + 1
    if int(date[2]) > 20:
        year = int(date[2]) + 1900
    else:
        year = int(date[2]) + 2000
    return datetime.date(year, month, day)

def string_to_date(date):
    """Convert yyyy-mm-dd string to datetime object."""
    date = date.split('-')
    return datetime.date(int(date[0]), int(date[1]), int(date[2]))

class View(object):
    """Display trading statistics as charts instead of tables."""
    def __init__(self):
        self.myData = []        # main data structure
        self.trades = []        # trade list
        self.wins = []          # list of winning trades
        self.losses = []        # list of losing trades
        self.winPct = 0         # # wins / # losses
        self.prftFact = 0       # size of winners versus losers
        self.averages = []      # average win and loss
        self.expectancy = 0     # average win and loss
        self.gains = []         # total and annual gains
        self.drawdowns = []     # list of drawdowns
        self.regret = 0         # regret is the % of time in drawdown
        self.mae = []           # list of Maximum Adverse Excursions
        self.efficiency = []    # list of efficiencies
        self.inTradeVol = []    # list of in-trade volatilties

    def getData(self, fileName):
        """Load the data from a csv file."""
        # open the file
        source = open(fileName, 'r')
        # dump the first line
        source.readline()
        # put the data in our list
        for line in source:
            line.strip() # get rid of the new line
            data = line.split(',')
            # 0 = date, 1 = open, 2 = high, 3 = low, 4 = close, 5 = volume,
            # 6 = indicator 1, 7 = indicator 2, 8 = signal and 9 = equity curve
            # 10 = TimeInDD
            self.myData.append([string_to_date(data[0]), float(data[1]), float(data[2]),\
                float(data[3]), float(data[4]), int(data[5]), 0, 0, 0, 1, 0])
        # Reverse if data is in reverse order
        if self.myData[0][0] > self.myData[1][0]:
            self.myData.reverse()
        # TODO Allow for import of indicator and/or signals

    def calcIndicator(self, indLength):
        """Calculate an indicator to be used for decision making."""
        # TODO allow for import of external indicator
        # simple moving average
        for i in xrange(indLength - 1, len(self.myData)):
            indSum = 0
            for j in xrange(0, indLength):
                indSum += self.myData[i-j][4]
            self.myData[i][6] = indSum / indLength

    def calcSignals(self, indLength):
        """Calculate the signals from the indicator.
        1 for buy, 0 for no action -1 for sell or short."""
        # moving average changes in direction
        # TODO Exit logic
        for i in xrange(indLength + 2, len(self.myData)):
            if self.myData[i-2][6] > self.myData[i-1][6] and self.myData[i-1][6] < self.myData[i][6]:
                self.myData[i][8] = 1
            elif self.myData[i-2][6] < self.myData[i-1][6] and self.myData[i-1][6] > self.myData[i][6]:
                self.myData[i][8] = -1

    def calcTrades(self, indLength):
        """Calculate the trades and drawdowns from the signals."""
        for i in xrange(indLength + 2, len(self.myData)):
            if self.myData[i][8] == 1:
                entry = self.myData[i][4] # entry price
                drawdown = sys.maxint # a large number
                for j in xrange(i, len(self.myData)):
                    if self.myData[j][4] < entry: # drawdown
                        drawdown = self.myData[j][4]
                    if self.myData[j][8] == -1: # exit
                        trade = self.myData[j][4] / self.myData[i][4] - 1
                        self.trades.append([self.myData[i][0], trade, j - i])
                        if trade > 0.0:
                            self.wins.append(trade)
                        else:
                            self.losses.append(trade)
                        if drawdown < entry:
                            self.drawdowns.append([self.myData[i][0], drawdown/entry-1])
                        else:
                            self.drawdowns.append([self.myData[i][0], 0.0])
                        break

    def calcEquityCurve(self):
        """Calculate the equity curve.
        Compound the value of an initial dollar."""
        longPosition = False
        for i in xrange(0, len(self.myData) - 1):
            if self.myData[i][8] == 1:
                longPosition = True
            elif self.myData[i][8] == -1:
                longPosition = False
            delta = self.myData[i+1][4] / self.myData[i][4]
            if longPosition:
                self.myData[i+1][9] = delta * self.myData[i][9]
            else:
                self.myData[i+1][9] = self.myData[i][9]

    def calcTimeInDrawdown(self):
        """Calculate time spent in draw down."""
        maximum = 0
        count = 0
        for i in xrange(1, len(self.myData)):
            if self.myData[i][9] < maximum:
                self.myData[i][10] = self.myData[i-1][10] + 1
                count += 1
            else:
                maximum = self.myData[i][9]
        self.regret = count / (len(self.myData) - 1)

    def calcSummaryData(self):
        """Calculate the summary statistics."""
        self.winPct = len(self.wins) / len(self.trades)
        avgWin = sum(self.wins) / len(self.wins)
        avgLoss = abs(sum(self.losses) / len(self.losses))
        self.prftFact = avgWin / avgLoss
        self.expectancy = self.winPct * self.prftFact - (1-self.winPct)

    def calcReturns(self):
        """Calculate returns from trades."""
        avgWin = sum(self.wins) / len(self.wins)
        avgLoss = sum(self.losses) / len(self.losses)
        self.averages.append([avgWin, avgLoss])
        gain = 1
        for i in xrange(0, len(self.trades)):
            gain = gain * (1 + self.trades[i][1])
        gain -= 1
        annGain = (1 + gain)**(1/(relativedelta(self.myData[-1][0], self.myData[1][0]).years)) - 1
        self.gains.append([gain, annGain])

    def calcMAE(self, indLength):
        """Calculate Maximum Adverse Excursions.
        Bollinger's implementation of John Sweeny idea."""
        for i in xrange(indLength + 2, len(self.myData)):
            if self.myData[i][8] == 1:
                mae, maximum = 0, 0
                for j in xrange(i, len(self.myData)):
                    if self.myData[j][4] > maximum:
                        maximum = self.myData[j][4]
                    elif self.myData[j][4] / maximum - 1 < mae:
                        mae = self.myData[j][4] / maximum - 1
                    if self.myData[j][8] == -1: # exit
                        self.mae.append([self.myData[i][0], mae])
                        break

    def calcEfficiency(self, indLength):
        """Calculate Efficiencies.
        Distance traveled versus gain/loss."""
        # TODO Should we calcualte ink instead of distance or both?
        for i in xrange(indLength + 2, len(self.myData)):
            if self.myData[i][8] == 1:
                dist = 0
                for j in xrange(i + 1, len(self.myData)):
                    dist += abs(self.myData[j][4] - self.myData[j-1][4])
                    if self.myData[j][8] == -1: # exit
                        eff = dist / (j - i) / self.myData[i][4]
                        self.efficiency.append([self.myData[i][0], eff])
                        break

    def calcVolatility(self, indLength):
        """Calculate in-trade volatility using
         the absolute value of average single-period return."""
        for i in xrange(indLength + 2, len(self.myData)):
            if self.myData[i][8] == 1:
                vol = 0
                count = 0
                for j in xrange(i + 1, len(self.myData)):
                    vol += abs(self.myData[j][4] / self.myData[j-1][4] - 1)
                    count += 1
                    if self.myData[j][8] == -1: # exit
                        self.inTradeVol.append([self.myData[i][0], vol / count])
                        break

    def displayPriceGraph(self):
        """Display a graph of price."""
        curve = [row[4] for row in self.myData] # extract data to be plotted
        dates = [row[0] for row in self.myData]
        fig, ax = plt.subplots()
        fig.suptitle("John Bollinger's Trade Visualization")
        ax.set_ylabel("price (log-scale)")
        ax.semilogy(dates, curve)
        # minor tick labels for log y-axis
        ax.yaxis.set_major_formatter(FormatStrFormatter("%d "))
        ax.yaxis.set_minor_formatter(FormatStrFormatter("%d "))
        ax.set_ylim(top=np.max(curve))
        ax.set_ylim(bottom=np.min(curve))
        ax.grid(True)
        ax.xaxis.set_major_locator(mdates.YearLocator(5)) # every 5 years
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        fig.autofmt_xdate()
        plt.show()

    def displayPriceTradesGraph(self, distance):
        """Display a graph of price."""
        curve = [row[4] for row in self.myData] # extract data to be plotted
        dates = [row[0] for row in self.myData] # extract dates to be plotted
        trades = [row[8] for row in self.myData] # extract trades to be plotted
        upper = [x * (1 + distance) for x in curve] # anchor for sell markers
        lower = [x / (1 + distance) for x in curve] # anchor for buy markers
        buys, sells = [], [] # lists of buys and sells
        i = 0
        for b in trades: # parse trades into indexed buys and sells
            if b == 1:
                buys.append(i)
            elif b == -1:
                sells.append(i)
            i += 1
        fig, ax = plt.subplots()
        fig.suptitle("John Bollinger's Trade Visualization")
        ax.set_ylabel("price with trade markers (log-scale)")
        ax.semilogy(dates, curve)
        ax.semilogy(dates, lower, 'g^', markevery=buys)
        ax.semilogy(dates, upper, 'rv', markevery=sells)
        # minor tick labels for log y-axis
        ax.yaxis.set_major_formatter(FormatStrFormatter("%d "))
        ax.yaxis.set_minor_formatter(FormatStrFormatter("%d "))
        ax.set_ylim(top=np.max(curve) * (1 + distance))
        ax.set_ylim(bottom=np.min(curve) / (1 + distance))
        ax.grid(True)
        ax.xaxis.set_major_locator(mdates.YearLocator(5)) # every 5 years
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        fig.autofmt_xdate()
        plt.show()

    def displayTradeGraph(self):
        """Display a graph of the trades."""
        y = [row[1] for row in self.trades] # extract data to be plotted
        x = xrange(0, len(self.trades), 1) # values for x-axis
        fig, ax = plt.subplots()
        fig.suptitle("John Bollinger's Trade Visualization")
        ax.set_xlabel("trades")
        ax.set_ylabel("returns")
        ax.vlines(x, 0, y, color='blue')
        ax.grid(True)
        ax.set_xlim([0, len(self.trades)]) # don't leave extra space
        ax.set_ylim(top=np.max(y) + 0.01) # use almost the whole plot space
        ax.set_ylim(bottom=np.min(y) - 0.01)
        plt.show()

    def displayTradesVersusTime(self):
        """Display an x-y of returns versus time."""
        x = [row[2] for row in self.trades] # extract data to be plotted
        y = [row[1] for row in self.trades]
        fig, ax = plt.subplots()
        fig.suptitle("John Bollinger's Trade Visualization")
        ax.set_xlabel('trading days')
        ax.set_ylabel('returns')
        ax.scatter(x, y, color='red', alpha=0.4)
        ax.set_ylim(top=max(y) + 0.01) # don't leave extra space
        ax.set_ylim(bottom=np.min(y) - 0.01)
        ax.set_xlim(right=np.max(x) + 2)
        ax.set_xlim(left=np.min(x) - 2)
        ax.grid(True)
        plt.show()

    def displayEquityCurveLog(self):
        """Display the equity curve with semi-log scaling."""
        curve = [row[9] for row in self.myData] # extract data to be plotted
        dates = [row[0] for row in self.myData]
        fig, ax = plt.subplots()
        fig.suptitle("John Bollinger's Trade Visualization")
        ax.set_ylabel("equity curve (log)")
        ax.semilogy(dates, curve)
        # minor tick labels for log y-axis
        ax.yaxis.set_major_formatter(FormatStrFormatter("%d "))
        ax.yaxis.set_minor_formatter(FormatStrFormatter("%d "))
        ax.set_ylim(top=np.max(curve))
        ax.set_ylim(bottom=np.min(curve))
        ax.grid(True)
        ax.xaxis.set_major_locator(mdates.YearLocator(5)) # every 5 years
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        fig.autofmt_xdate()
        plt.show()

    def displayEquityCurve(self):
        """Display the equity curve."""
        curve = [row[9] for row in self.myData] # extract data to be plotted
        dates = [row[0] for row in self.myData]
        fig, ax = plt.subplots()
        fig.suptitle("John Bollinger's Trade Visualization")
        ax.set_ylabel("equity curve")
        ax.plot(dates, curve)
        ax.set_ylim(top=np.max(curve))
        ax.set_ylim(bottom=np.min(curve))
        ax.grid(True)
        ax.xaxis.set_major_locator(mdates.YearLocator(5)) # every 5 years
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        fig.autofmt_xdate()
        plt.show()

    def displayDistribution(self):
        """Display a graph of the distribution of returns."""
        y = [row[1] for row in self.trades] # extract data to be plotted
        fig, ax = plt.subplots()
        fig.suptitle("John Bollinger's Trade Visualization")
        ax.set_ylabel("count")
        ax.set_xlabel("returns")
        ax.grid(True)
        binwidth = 0.005 # bins one half percent wide
        binspec = np.arange(min(y), max(y) + binwidth, binwidth)
        # split into positive and negative lists
        pos = [n for n in y if n >= 0.0]
        neg = [n for n in y if n < 0.0]
        ax.hist(pos, bins = binspec, color = 'green')
        ax.hist(neg, bins = binspec, color = 'red')
        plt.show()

    def displayTimeInDrawDown(self):
        """Display the time spent in drawdown."""
        dd = [row[10] for row in self.myData] # extract data to be plotted
        dates = [row[0] for row in self.myData]
        fig, ax = plt.subplots()
        fig.suptitle("John Bollinger's Trade Visualization")
        ax.set_ylabel("time in drawdown")
        ax.plot(dates, dd)
        ax.grid(True)
        ax.set_ylim(top=np.max(dd) + 0.01)
        ax.xaxis.set_major_locator(mdates.YearLocator(5)) # every 5 years
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        fig.autofmt_xdate()
        plt.show()

    def displayDrawdownGraph(self):
        """Display a graph of the drawdowns."""
        y = [row[1] for row in self.drawdowns] # extract data to be plotted
        x = xrange(0, len(self.drawdowns), 1) # values for x-axis
        fig, ax = plt.subplots()
        fig.suptitle("John Bollinger's Trade Visualization")
        ax.set_xlabel("trades")
        ax.set_ylabel("drawdowns")
        ax.vlines(x, 0, y, color='blue')
        ax.grid(True)
        ax.set_xlim([0, len(self.drawdowns)]) # don't leave extra space
        ax.set_ylim(top = 0)
        ax.set_ylim(bottom=np.min(y) - 0.01)
        plt.show()

    def displayMAE(self):
        """Display a graph of the Maximum Adverse Excursions."""
        y = [row[1] for row in self.mae] # extract data to be plotted
        x = xrange(0, len(self.mae), 1) # values for x-axis
        fig, ax = plt.subplots()
        fig.suptitle("John Bollinger's Trade Visualization")
        ax.set_xlabel("trades")
        ax.set_ylabel("maximum adverse excursion")
        ax.vlines(x, 0, y, color='blue')
        ax.grid(True)
        ax.set_xlim([0, len(self.mae)]) # don't leave extra space
        ax.set_ylim(top = 0)
        ax.set_ylim(bottom=np.min(y) - 0.01)
        plt.show()

    def displayEfficiency(self):
        """Display a graph of the trade efficiencies."""
        y = [row[1] for row in self.efficiency] # extract data to be plotted
        x = xrange(0, len(self.mae), 1) # values for x-axis
        fig, ax = plt.subplots()
        fig.suptitle("John Bollinger's Trade Visualization")
        ax.set_xlabel("trades")
        ax.set_ylabel("efficiency")
        ax.vlines(x, 0, y, color='blue')
        ax.grid(True)
        ax.set_xlim([0, len(self.mae)]) # don't leave extra space
        ax.set_ylim(top=np.max(y) + 0.01)
        ax.set_ylim(bottom = 0)
        plt.show()

    def displayInTradeVol(self):
        """Display a graph of in-trade volatilities."""
        y = [row[1] for row in self.inTradeVol] # extract data to be plotted
        x = xrange(0, len(self.inTradeVol), 1) # values for x-axis
        fig, ax = plt.subplots()
        fig.suptitle("John Bollinger's Trade Visualization")
        ax.set_xlabel("trades")
        ax.set_ylabel("in-trade volatility")
        ax.vlines(x, 0, y, color='blue')
        ax.grid(True)
        ax.set_xlim([0, len(self.inTradeVol)]) # don't leave extra space
        ax.set_ylim(top=np.max(y) + 0.01)
        ax.set_ylim(bottom = 0)
        plt.show()

    def printResults(self):
        """Print a table of summary results."""
        print
        print("There were {0} trades.".format(len(self.trades)))
        print("There were {0} winners.".format(len(self.wins)))
        print("There were {0} losers.".format(len(self.losses)))
        print("Winning % =      {0:.2f}%".format(self.winPct*100))
        print("Average win =    {0:.2f}%".format(self.averages[0][0]*100))
        print("Average loss =   {0:.2f}%".format(self.averages[0][1]*100))
        print("Profit factor =  {0:.2f}".format(self.prftFact))
        print("Expectancy =     {0:.2f}".format(self.expectancy))
        print("Total gain =     {0:.2f}%".format(self.gains[0][0]*100))
        print("Annual gain =    {0:.2f}%".format(self.gains[0][1]*100))
        print("Regret =         {0:.2f}%".format(self.regret*100))
        print

    def printResultsTk(self):
        """Print a table of summary results to a Tkinter window."""
        root = tk.Tk()
        root.title("SystemView")
        TextBox = tk.Text(root, height = 13, width = 30)
        TextBox.pack()
        class writeTk(object):
            def write(self, s):
                TextBox.insert(tk.END, s)
        backup = sys.stdout
        sys.stdout = writeTk()
        print("First trade {0}, {1:.2f}%".format(a.trades[1][0].isoformat(), a.trades[1][1] * 100))
        print("Last trade  {0}, {1:.2f}%".format(a.trades[-1][0].isoformat(), a.trades[-1][1] * 100))
        print("There were {0} trades.".format(len(self.trades)))
        print("There were {0} winners.".format(len(self.wins)))
        print("There were {0} losers.".format(len(self.losses)))
        print("Winning % =      {0:.2f}%".format(self.winPct*100))
        print("Average win =    {0:.2f}%".format(self.averages[0][0]*100))
        print("Average loss =   {0:.2f}%".format(self.averages[0][1]*100))
        print("Profit factor =  {0:.2f}".format(self.prftFact))
        print("Expectancy =     {0:.2f}".format(self.expectancy))
        print("Total gain =     {0:.2f}%".format(self.gains[0][0]*100))
        print("Annual gain =    {0:.2f}%".format(self.gains[0][1]*100))
        print("Regret =         {0:.2f}%".format(self.regret*100))
        sys.stdout = backup
        TextBox.mainloop()

if __name__ == '__main__':
    # create an instance of our class
    a = View()
    # fetch data
    # expecting comma separated data
    # 2016-01-01, open, high, low, close, volume
    a.getData(param.file1)
    # debug print first and last record
    if param.verbose:
        print("First record {0}, {1:0.2f}".format(a.myData[1][0].isoformat(), a.myData[1][1]))
        print("Last record  {0}, {1:0.2f}".format(a.myData[-1][0].isoformat(), a.myData[-1][1]))
    # calculate indicator
    a.calcIndicator(param.maLength)
    # calculate signals
    a.calcSignals(param.maLength)
    # get a list of trades
    a.calcTrades(param.maLength)
    # calculate returns
    a.calcReturns()
    # calculate equity curve
    a.calcEquityCurve()
    # calculate time to recover peak asset value
    a.calcTimeInDrawdown()
    # calcuate Maximum Adverse Excursion
    a.calcMAE(param.maLength)
    # calculate efficiency
    a.calcEfficiency(param.maLength)
    # calculate in-trade volatility
    a.calcVolatility(param.maLength)
    # calculate summary data
    a.calcSummaryData()
    # print some summary data
    if param.resultsTk:
        a.printResultsTk()
    # results to sommand line interface
    a.printResults()
    # debug print first and last trade
    if param.verbose:
        print("First trade {0}, {1:.2f}%".format(a.trades[1][0].isoformat(), a.trades[1][1] * 100))
        print("Last trade  {0}, {1:.2f}%".format(a.trades[-1][0].isoformat(), a.trades[-1][1] * 100))
    # show a plot of price with trade markers
    if param.displayPriceGraph:
        a.displayPriceGraph()
    if param.displayPriceTradesGraph:
        a.displayPriceTradesGraph(param.distance)
    # show a plot of all trades
    if param.displayTradeGraph:
        a.displayTradeGraph()
    # show a plot of trades versus time
    if param.displayTradesVersusTime:
        a.displayTradesVersusTime()
    # show a plot of the equity curve
    if param.displayEquityCurve:
        a.displayEquityCurve()
    # show a log plot of the equity curve
    if param.displayEquityCurveLog:
        a.displayEquityCurveLog()
    # show a graph of the distribution of returns
    if param.displayDistribution:
        a.displayDistribution()
    # show a graph of drawdowns
    if param.displayDrawdownGraph:
        a.displayDrawdownGraph()
    # show a graph of time in drawdown
    if param.displayTimeInDrawDown:
        a.displayTimeInDrawDown()
    # show an MAE graph
    if param.displayMAE:
        a.displayMAE()
    # show an Efficiency graph
    if param.displayEfficiency:
        a.displayEfficiency()
    # show a graph of in-trade volatility
    if param.displayInTradeVol:
        a.displayInTradeVol()

# That's all folks!