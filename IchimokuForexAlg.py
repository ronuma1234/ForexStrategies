# By Robert Onuma
from AlgorithmImports import *

class IchimokuForexAlg(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2010, 1, 1)
        self.SetEndDate(2020, 1, 1)
        self.SetCash(10000)
        self.pair = self.AddForex("EURUSD", Resolution.Hour, Market.Oanda).Symbol
        
        self.ichimoku = self.ICHIMOKU(self.pair,9, 26, 23, 52, 26, 26, Resolution.Daily)
        
        ichimokuPlot = Chart('ichimokuPlot')
        
        #ichimokuPlot.AddSeries(Series('Tenkan', SeriesType.Line, "", Color.Blue))
        ichimokuPlot.AddSeries(Series('Tenkan', SeriesType.Line, "", Color.Red))
        ichimokuPlot.AddSeries(Series('Kijun', SeriesType.Line, "", Color.Purple))
        #ichimokuPlot.AddSeries(Series('KijunCal', SeriesType.Line, "", Color.Green))
        ichimokuPlot.AddSeries(Series('SenkouA', SeriesType.Line, "", Color.Orange))
        ichimokuPlot.AddSeries(Series('SenkouB', SeriesType.Line, "", Color.Yellow))
        #ichimokuPlot.AddSeries(Series('SenkouACal', SeriesType.Line, "", Color.Yellow))
        #ichimokuPlot.AddSeries(Series('SenkouBCal', SeriesType.Line, "", Color.White))
        #ichimokuPlot.AddSeries(Series('Chikou', SeriesType.Line, "", Color.Pink))
        ichimokuPlot.AddSeries(Series('Price', SeriesType.Line, "", Color.Gray))
        ichimokuPlot.AddSeries(Series('Buy', SeriesType.Scatter, '$', Color.Green, ScatterMarkerSymbol.Triangle))
        ichimokuPlot.AddSeries(Series('Sell', SeriesType.Scatter, '$', Color.Red, ScatterMarkerSymbol.TriangleDown))
        ichimokuPlot.AddSeries(Series('Liquidate', SeriesType.Scatter, '$', Color.Blue, ScatterMarkerSymbol.Circle))
        
        self.AddChart(ichimokuPlot)
        
        self.highestPrice = 0
        self.entryPrice = 0
        
        self.rwPrice = RollingWindow[float](26)
        self.rwKijun = RollingWindow[float](26)
        self.rwTenkan = RollingWindow[float](26)
        self.rwSenkouA = RollingWindow[float](26)
        self.rwSenkouB = RollingWindow[float](26)
        self.rwHigh = RollingWindow[float](52)
        self.rwLow = RollingWindow[float](52)
        self.rwSenkouBCal = RollingWindow[float](28) 
        self.rwSenkouACal = RollingWindow[float](26)  
        

        


    def OnData(self,data):
        if data[self.pair] is None: 
            return
        
        self.lastClose = data[self.pair].Close
        self.lastHigh = data[self.pair].High
        self.lastLow = data[self.pair].Low
        
        #if self.IsWarmingUp: 
        #   return
    
        if self.ichimoku.IsReady: 
            self.rwPrice.Add(self.lastClose)
            self.rwKijun.Add(self.ichimoku.Kijun.Current.Value)
            self.rwTenkan.Add(self.ichimoku.Tenkan.Current.Value)
            self.rwSenkouA.Add(self.ichimoku.SenkouA.Current.Value)
            self.rwSenkouB.Add(self.ichimoku.SenkouB.Current.Value)
            self.rwHigh.Add(self.lastHigh)
            self.rwLow.Add(self.lastLow)
            


            
            if self.rwKijun.IsReady and self.rwPrice.IsReady and self.rwTenkan.IsReady and self.rwSenkouA.IsReady and self.rwSenkouB.IsReady  and self.rwLow.IsReady and self.rwHigh.IsReady:
                
                lowestLow  = min(list(self.rwHigh))
                highestHigh = max(list(self.rwHigh))

                self.SenkouBCal= (self.ichimoku.SenkouBMaximum.Current.Value + self.ichimoku.SenkouBMinimum.Current.Value) / 2

                self.rwSenkouBCal.Add(self.SenkouBCal)
                
                
                self.SenkouACal = ( self.ichimoku.Tenkan.Current.Value + self.ichimoku.Kijun.Current.Value) / 2 
                self.rwSenkouACal.Add(self.SenkouACal)
                
                if self.rwSenkouBCal.IsReady and self.rwSenkouACal.IsReady: 
                    
                    # plot
                    self.Plot("ichimokuPlot", "Tenkan", self.ichimoku.Tenkan.Current.Value)
                    self.Plot("ichimokuPlot", "Kijun", self.ichimoku.Kijun.Current.Value)
                    self.Plot("ichimokuPlot", "Price", self.lastClose)
                    #self.Plot("ichimokuPlot", "Chikou", self.ichimoku.Chikou.Current.Value)
                    self.Plot("ichimokuPlot", "SenkouA", self.ichimoku.SenkouA.Current.Value)
                    self.Plot("ichimokuPlot", "SenkouB", self.ichimoku.SenkouB.Current.Value)
                    #self.Plot("ichimokuPlot", "SenkouBCal", self.rwSenkouBCal[self.rwSenkouBCal.Count-1])
                    #self.Plot("ichimokuPlot", "SenkouACal", self.rwSenkouACal[self.rwSenkouACal.Count-1])
                    
                    
                    # BUY strategy: 
                    # price is above cloud

                    # Chikou is higher than price below it and the cloud. 
                    if self.lastClose > self.rwPrice[25] :
                        
                        # check if there is a shadow. 
                        self.isThereShadow = False
                        i = 0
                        while i <= 25:
                            # if any of the prices from the last 26 days are inside the cloud (shadow) stop 
                            # if the price is lower than senkou A or B there is a cloud. then return
                            if self.rwPrice[i] < self.ichimoku.SenkouA.Current.Value or self.rwPrice[i] < self.ichimoku.SenkouB.Current.Value:
                                self.isThereShadow = True
                                break
                            i += 1
                            
                        # if no shadow
                        if not self.isThereShadow: 
                            
                            # is tenkan higher than kijun?
                            if self.ichimoku.Tenkan.Current.Value > self.ichimoku.Kijun.Current.Value:
                                # is tenkan is moving up?
                                if self.ichimoku.Tenkan.Current.Value > self.rwTenkan[1]:
                                
                                    # is future cloud is green (preferebly thick)
                                    
                                    if self.ichimoku.SenkouA > self.ichimoku.SenkouB:
                                    #if self.SenkouACal > self.SenkouBCal: 
                                    
                                        #if not invested buy
                                        if not self.Portfolio.Invested:  
                                            self.SetHoldings(self.pair, 1)
                                            self.Plot("ichimokuPlot", "Buy", self.lastClose)   
                                            self.entryPrice = self.lastClose
                                            

                    #Sell
                    #Chikou is lower than price above it
                    elif self.lastClose < self.rwPrice[25] :
                        
                        # check if there is shade. 
                        self.isThereShade = False
                        i = 0
                        while i <= 25:
                            # if any of the prices from the last 26 days are inside the cloud (shadow) stop 
                            # if the price is higher than senkou A or B there is a cloud. then return
                            if self.rwPrice[i] > self.ichimoku.SenkouA.Current.Value or self.rwPrice[i] > self.ichimoku.SenkouB.Current.Value:
                                self.isThereShade = True
                                break
                            i += 1
                            
                        # if no shade
                        if not self.isThereShade: 
                            
                            # is tenkan lower than kijun?
                            if self.ichimoku.Tenkan.Current.Value < self.ichimoku.Kijun.Current.Value:
                                # is tenkan is moving down?
                                if self.ichimoku.Tenkan.Current.Value < self.rwTenkan[1]:
                                
                                    # is future cloud is red (preferebly thick)
                                    
                                    if self.ichimoku.SenkouA < self.ichimoku.SenkouB:
                                    #if self.SenkouACal < self.SenkouBCal: 
                                    
                                        #if not invested buy
                                        if not self.Portfolio.Invested:  
                                            self.SetHoldings(self.pair, -1)
                                            self.Plot("ichimokuPlot", "Sell", self.lastClose)   
                                            self.entryPrice = self.lastClose
                                            
                
                
                #Liquidate
                #Making sure there is a high risk to reward each trade
                if self.entryPrice * 1.03 < self.lastClose or self.entryPrice * 0.99 > self.lastClose:
                    if self.Portfolio.Invested:
                        self.Liquidate()
                        self.Plot("ichimokuPlot", "Liquidate", self.lastClose)


                