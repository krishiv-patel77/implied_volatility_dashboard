import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
import threading 
from datetime import datetime
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy import stats
from ibapi.contract import Contract
from src.ib_client import IBApp

import warnings
warnings.filterwarnings('ignore')

"""
This class basically houses everything; for convenience everything including all regressions are kept in one
giant class; might change after if expanding

"""

class ImpliedVolatilityDashboard():

    # The root being passed in is just tk.Tk() -> its how you initialize a tkinter app
    def __init__(self, root):

        self.root = root

        self.root.title("Implied Volatility Trading Dashboard")
        self.root.geometry("1400x1200")

        # These fields will be populated with IB data later
        self.option_data = None
        self.volatility_data = None
        self.current_implied_vol = None

        # Very convenient way to handle any requests made to the IB server for data
        self.ib_app = IBApp()
        self.connected = False

        # Set a default vol annualization -> this is for daily because there are 252 trading days in a year | would be different for weekly bars or monthly bars
        self.vol_annualization = 252

        # This function will contain all of the tkinter UI logic and will setup the entire UI
        self.setup_ui()

    
    def create_equity_contract(self, symbol):
        """ 
        Need this function because we need to make a contract in order to get its data from IB.

        Whenever the button is clicked after entering a symbol on the UI, this function is called and a contract for the 
        entered symbol is created to then query data from IB server. 
        """
        
        contract = Contract()
        contract.symbol = symbol.upper()
        contract.secType = "STK"    # Stock
        contract.exchange = "SMART" 
        contract.currency = "USD"

        return contract

    def setup_ui(self):
        
        """ Entire UI of the tkinter GUI """

        # Setup up the mainframe within the window
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))

        # Configure root to resize with expanding window
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        # Configure mainframe to resize with expanding window
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)

        """ Connection Widget Code Start """
        # Create a connection widget or frame within the mainframe and position it
        conn_frame = ttk.LabelFrame(main_frame, text="Interactive Brokers Connection", padding="5")
        conn_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0,10))

        # Within the connection frame, add a Host field to extract the Host connecting to the IB server; default is local host
        ttk.Label(conn_frame, text="Host:").grid(row=0, column=0, padx=(0,5))
        self.host_var = tk.StringVar(value="127.0.0.1")
        ttk.Entry(conn_frame, textvariable=self.host_var, width=15).grid(row=0, column=1, padx=(0,10))

        # Within the connection frame, add a Port field to specify what port to run IB server on
        ttk.Label(conn_frame, text="Port:").grid(row=0, column=2, padx=(0,5))
        self.port_var = tk.StringVar(value="7497")
        ttk.Entry(conn_frame, textvariable=self.port_var, width=15).grid(row=0, column=3, padx=(0,10))

        # Within the connection frame, create a connect button which connects to the IB server
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.connect_ib)
        self.connect_btn.grid(row=0, column=4, padx=(0,10))

        # Within the connection frame, create a disconnect button which disconnects from the IB server
        self.disconnect_btn = ttk.Button(conn_frame, text="Disconnect", command=self.disconnect_ib)
        self.disconnect_btn.grid(row=0, column=5, padx=(0,10))
        """ Connect Widget Code End """


        """ Data Widget Code Start """
        # Create a frame to query the data
        data_frame = ttk.LabelFrame(main_frame, text="Data Query", padding="5")
        data_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0,10))

        # Within the data frame, create an entry for the ticker symbol
        ttk.Label(data_frame, text="Symbol:").grid(row=0, column=0, padx=(0,5))     # Row stays the same at 0 because we are within the data frame
        self.symbol_var = tk.StringVar(value="SPY")
        ttk.Entry(data_frame, textvariable=self.symbol_var, width=15).grid(row=0, column=1, padx=(0,10))

        # Within the data frame, create an entry for the duration
        ttk.Label(data_frame, text="IV Range:").grid(row=0, column=2, padx=(0,5))       # Field in col 2
        self.iv_range_var = tk.StringVar(value="2 Y")
        ttk.Entry(data_frame, textvariable=self.iv_range_var, width=15).grid(row=0, column=3, padx=(0,10))      # Entry in col 3

        # Within the data frame, create a data query button which queries the IB server for data
        self.data_query_btn = ttk.Button(data_frame, text="Query IV Data", command=self.query_data)
        self.data_query_btn.grid(row=0, column=4, padx=(0,10))

        # Within the data frame, create a disconnect button which disconnects from the IB server
        self.analyze_btn = ttk.Button(data_frame, text="Analyze Implied Vol", command=self.analyze_volatility)
        self.analyze_btn.grid(row=0, column=5, padx=(0,10))

        """ Data Widget Code End """


        """ Volatility Widget Code Start """

        # Within the mainframe, create a frame to hold the IV data
        vol_frame = ttk.LabelFrame(main_frame, text="Current Implied Volatility", padding="5")
        vol_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.E, tk.W), pady=(0,10))

        # Within the vol frame, create a field to hold the current IV
        ttk.Label(vol_frame, text="Current IV:").grid(row=0, column=0, padx=(0,5))
        # Next to the Current IV: label, we will have another label we set to a variable so it can be updated
        self.current_vol_label = ttk.Label(vol_frame, text="No Data", font=("Arial", 12, "bold"))
        self.current_vol_label.grid(row=0, column=1, padx=(0,20))

        # Within the vol frame, create a label for stating the computation methods used in the IV calculation
        ttk.Label(vol_frame, text="Computation:").grid(row=0, column=2, padx=(0,5))
        self.vol_computation_label = ttk.Label(vol_frame, text="No Data", font=("Arial", 10))
        self.vol_computation_label.grid(row=0, column=3, padx=(0,10))

        # Within the vol frame, add a label for the computation statistics over the entered range of the IV
        ttk.Label(vol_frame, text="Vol Stats:").grid(row=0, column=4, padx=(0,5))
        self.vol_statistics_label = ttk.Label(vol_frame, text="N/A", font=("Arial", 10))
        self.vol_statistics_label.grid(row=0, column=5)

        """ Volatility Widget Code End """

        """ Vol Regime Widget Code Start """
        # Within the mainframe, create a regime frame to hold all of the regime data
        regime_frame = ttk.LabelFrame(main_frame, text="Volatility Regime Analysis", padding="5")
        regime_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Within the regime frame, add a current regime attribute that displays the current regime
        ttk.Label(regime_frame, text="Current Regime:").grid(row=0, column=0, padx=(0, 5))
        self.regime_label = ttk.Label(regime_frame, text="N/A", font=("Arial", 11, "bold"))
        self.regime_label.grid(row=0, column=1, padx=(0, 20))
        
        # Within the regime frame, add a percentile regime attribute
        ttk.Label(regime_frame, text="Percentile:").grid(row=0, column=2, padx=(0, 5))
        self.percentile_label = ttk.Label(regime_frame, text="N/A", font=("Arial", 10))
        self.percentile_label.grid(row=0, column=3, padx=(0, 20))
        
        # Within the regime frame, add a mean reversion signal
        ttk.Label(regime_frame, text="Mean Reversion Signal:").grid(row=0, column=4, padx=(0, 5))
        self.reversion_label = ttk.Label(regime_frame, text="N/A", font=("Arial", 10))
        self.reversion_label.grid(row=0, column=5)
        
        """ Vol Regime Widget Code End """

        """ Status Frame Widget Code Start """
        # Within the mainframe, create a status frame which informs the user of the current status of the application
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="5")
        status_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))     # Position in row 4
        
        # Within the status frame, add a textbox area that can scroll down
        self.status_text = scrolledtext.ScrolledText(status_frame, height=6, width=80)  # Increased height for better visibility
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E))     # Only element within status frame so row 0 and col 0 and sticky
        status_frame.columnconfigure(0, weight=1)                       # As the column expands, the status_text area will also expand

        """ Status Frame Widget Code End """

        """ Plot Frame Widget Code Start """
        # Within the mainframe, add a plot frame for holding all of the matplotlib plots
        plot_frame = ttk.LabelFrame(main_frame, text="Implied Volatility Analysis Results", padding="5")
        plot_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))     # Should cover the rest of the space in the dashboard

        # Configure the plot frame to expand as the window expands
        plot_frame.columnconfigure(0, weight=1)
        plot_frame.rowconfigure(0, weight=1)

        # Create matplotlib figure with 3 subplots
        self.fig, (self.ax1, self.ax2, self.ax3) = plt.subplots(1, 3, figsize=(20, 7))
        self.fig.subplots_adjust(left=0.06, right=0.98, top=0.92, bottom=0.12, wspace=0.3)
        self.canvas = FigureCanvasTkAgg(self.fig, plot_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        """ Plot Frame Widget Code End """

    def log_message(self, message):
        """ Function that prints to the console log and updates the status text which displays the console log to the user. """
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)

        # Update the UI immediately after a change in the status text area
        self.root.update_idletasks()

    def connect_ib(self):
        try:
            # We can get the text inputs tied to the field vars we defined above using get()
            host = self.host_var.get()
            port = int(self.port_var.get())

            self.log_message(f"Connecting to IB at {host}:{port}")

            def connect_thread():
                try:
                    self.ib_app.connect(host, port, clientId=43)
                    self.ib_app.run()
                except Exception as e:
                    self.log_message(f"Connect Error: {e}")

            # Create a thread to run the IB connection
            # The daemon attribute essentially allows the program to quit without needing for this thread to finish, and this makes sense because it is just a background thread connecting to the IB app
            thread = threading.Thread(target=connect_thread, daemon=True)
            thread.start()

            for _ in range(100):
                # If we are connected, then break
                if self.ib_app.connected:
                    break

                # if not, then sleep for a total of 5 seconds
                time.sleep(0.1)

            # Now if we do connect successfully to IB, do the following
            if self.ib_app.connected:
                self.connected = True
                self.connect_btn.config(state="disabled")       # Disable the connect button if connected
                self.disconnect_btn.config(state="normal")      # Enable the disconnect button
                self.data_query_btn.config(state="normal")      # Enable the data query button
                # Notice we didn't enable the analyze button here because we need to query the data first
                self.log_message("Successfully Connected to IB TWS")
            else:
                self.log_message("Failed to Connect to IB TWS")

        except Exception as e:
            self.log_message(f"Connection Error: {e}")
    
    def disconnect_ib(self):

        try:
            # Note that these ib_app functions are coming from the EClient class that we inherited from
            self.ib_app.disconnect()
            self.connected = False
            self.connect_btn.config(state="normal")
            self.disconnect_btn.config(state="disabled")
            self.data_query_btn.config(state="disabled")
            self.analyze_btn.config(state="disabled")

            # Reset the volatility statistics and values
            self.current_implied_vol = None
            self.update_current_vol_display()

            self.log_message("Disconnected from IB TWS")

        except Exception as e:
            self.log_message(f"Disconnect Error: {e}")

    def query_data(self):

        if not self.connected:
            # Pops up a little error window for the user to see if they are not connected to IB TWS
            messagebox.showerror("Error", "Not connected to IB TWS")

        # Get the symbol and the duration from the tk fields
        symbol = self.symbol_var.get().upper()
        vol_range = self.iv_range_var.get()

        self.log_message(f"Querying Implied Volatility for {symbol}...")

        # Clear any historical data already present within dict
        self.ib_app.historical_data.clear()

        # Create an equity contract for the entered symbol
        contract = self.create_equity_contract(symbol)

        # Request historical data
        self.ib_app.reqHistoricalData(
            reqId=1, 
            contract=contract,
            endDateTime="",
            durationStr=vol_range,
            barSizeSetting="1 day",
            whatToShow="OPTION_IMPLIED_VOLATILITY",
            useRTH=1,
            formatDate=1,
            keepUpToDate=False,
            chartOptions=[]
        )

        # Wait 15 seconds for the historical data to come
        timeout=15
        start = time.time()

        while 1 not in self.ib_app.historical_data and (time.time() - start) < timeout:
            time.sleep(0.1)

        if 1 in self.ib_app.historical_data:
            data = self.ib_app.historical_data[1]
            if len(data) > 0:
                self.equity_data = pd.DataFrame(data)
                self.equity_data['date'] = pd.to_datetime(self.equity_data['date'])
                self.equity_data.set_index('date', inplace=True)

                self.equity_data['implied_vol'] = self.equity_data['close']

                self.log_message(f"Recieved {len(self.equity_data)} implied volatility data points for {symbol}")
                self.log_message(f'Date Range: {self.equity_data.index.min()} to {self.equity_data.index.max()}')
                self.log_message(f"Note: All IV values are annulaized. ")

                self.process_implied_volatility()

                self.analyze_btn.config(state="normal")     # Once the data has been recieved, allow the user to analyze it

            else:
                self.log_message("No IV Data Recieved")
                self.equity_data = None

        else:
            self.log_message("No IV Data Recieved -> May Not Be Avaliable For Symbol")
            self.equity_data = None


    def process_implied_volatility(self):
        """ Function that executed after IV data is recieved. """

        # If there is no data, then we don't need to do anything
        if self.equity_data is None:
            return
        
        self.log_message("Processing IV Data...")
        self.log_message(f"Note: All IV values are annulaized. ")

        # Annualize the IV column
        self.equity_data['implied_vol'] = self.equity_data['close']*np.sqrt(self.vol_annualization)

        # Add IV percentile values
        self.equity_data['iv_percentile'] = self.equity_data['implied_vol'].rolling(window=252).rank(pct=True)

        # Current IV 
        self.current_implied_vol = self.equity_data['implied_vol'].iloc[-1] if len(self.equity_data) > 0 else None

        self.volatility_data = self.equity_data[["implied_vol", "iv_percentile"]].copy()
        print(f"volatility_data: \n {self.volatility_data}")

        # Update the GUI display based on the current fetched IV data
        self.update_current_vol_display()

        if self.current_implied_vol is not None:
            self.log_message(f"Current IV: {self.current_implied_vol: .4f} ({self.current_implied_vol*100: .2f}%)")
            self.log_message(f"IV Range: {self.volatility_data['implied_vol'].min(): .4f} - {self.volatility_data['implied_vol'].max(): .4f}")
        else:
            self.log_message("Failed to Process IV Data.")



    def update_current_vol_display(self):
        """ Based on the fetched implied vol data, update the GUI """

        # If we have a current implied vol extracted from data that is not None, update everything
        if self.current_implied_vol is not None:
            self.current_vol_label.config(text=f"{self.current_implied_vol: .4f} ({self.current_implied_vol*100: .2f}%)")
            self.vol_computation_label.config(text=f"Annualized Using √{self.vol_annualization} Factor")


            if self.equity_data is not None:
                avg_vol = self.volatility_data['implied_vol'].mean()
                minimum = self.volatility_data['implied_vol'].min()
                maximum = self.volatility_data['implied_vol'].max()

                vol_range_text = f"Min: {minimum: .3f} | Mean: {avg_vol: .3f} | Max: {maximum: .3f}"
            else:
                vol_range_text = "N/A"

            self.vol_statistics_label.config(text=vol_range_text)

            current_percentile = self.volatility_data["iv_percentile"].iloc[-1]

            # Configure some coloring based on if the IV is high or low; make this based on percentiles
            if current_percentile > .75:
                self.current_vol_label.config(foreground="red")
            elif current_percentile < 0.25:
                self.current_vol_label.config(foreground="green")
            else:
                self.current_vol_label.config(foreground="black")

            self.update_regime_analysis()

        else:
            # If current IV is none, disable and reset everything
            self.current_vol_label.config(text="N/A", foreground="black")
            self.vol_computation_label.config(text="None")
            self.vol_statistics_label.config(text="N/A")
            self.regime_label.config(text="N/A")
            self.percentile_label.config(text="N/A")
            self.reversion_label.config(text="N/A")

    def update_regime_analysis(self):
        # If we have no data, then there is nothing to do here, pretty redundant but still good for safe measure
        if self.current_implied_vol is None or self.volatility_data is None:
            return
        
        current_percentile = self.volatility_data["iv_percentile"].iloc[-1]

        # Basically just ranks the IV
        if current_percentile > 0.8:
            regime = "HIGH IV"
            color = "red"
        elif current_percentile > 0.6:
            regime = "ABOVE AVG IV"
            color="orange"
        elif current_percentile > 0.4:
            regime="NORMAL VOL"
            color="black"
        elif current_percentile > 0.2:
            regime="BELOW AVG IV"
            color="deep sky blue"
        else:
            regime="LOW IV"
            color="green"

        # Configure the regime tab
        self.regime_label.config(text=regime, foreground=color)
        self.percentile_label.config(text=f"{current_percentile: .1%}")

        # Now the way IV works is that it tends to be mean reverting, and ofc the mean is time variant, but it does tend to be mean reverting
        # We can express this by adding the reversion label
        if current_percentile > .8:
            reversion = "EXPECT MEAN REVERSION DOWN"
            rev_color = "red"
        elif current_percentile < .2:
            reversion = "EXPECT MEAN REVERSION UP"
            rev_color = "deep sky blue"
        else:
            reversion = "NEUTRAL"
            rev_color = "BLACK"

        self.reversion_label.config(text=reversion, foreground=rev_color)


    def analyze_volatility(self):
        
        # Again, if no data, we can't do anything so return
        if self.equity_data is None or self.volatility_data is None:
            messagebox.error("Error", "No IV Data is Avaliable for Analysis")
            return
        
        # Log the start of the analysis
        self.log_message("Analyzing IV Data...")

        # First we need a 30 day forward IV dataframe | we get this from the volatility dataframe with out IV values
        # Okay so first we compute the rolling avg over each 30 day period and then shift it back 30 days
        # This makes the avg at index 0 the avg IV over the next 30 days so it makes it forward looking in sense
        forward_vol_30d = self.volatility_data['implied_vol'].rolling(window=30, min_periods=1).mean().shift(-30)

        # Okay now from all of this data, we are going to make an analysis dataframe
        # The whole point of this is to match up the future data with the current data and see if there is any explanatory power there
        analysis_df = pd.DataFrame({
            "current_vol": self.volatility_data['implied_vol'],
            "forward_30d_vol": forward_vol_30d,
            "vol_diff": forward_vol_30d - self.volatility_data['implied_vol'],           # This works because we did min_periods=1 so we don't populate the first 0-29 indices with NaN
            "vol_percentile": self.volatility_data['iv_percentile']
        })

        analysis_df = analysis_df.dropna()

        # If we have insufficient data, log it and return -> if len of analysis df is less than 30, we have nothing to regress
        if len(analysis_df) < 30:
            self.log_message("Insufficient IV Data for Analysis")
            return
        
        # x = current_vol & y = forward_vol and try to see if there is some slope and intercept values that can explain the situation
        slope1, intercept1, r1, p1, std_err1 = stats.linregress(
            analysis_df['current_vol'], analysis_df['forward_30d_vol']
        )

        # x = current_vol & y = diff between forward and current vol | try to see if some slope and intercept can give us diff between current and forward vol
        slope2, intercept2, r2, p2, std_err2 = stats.linregress(
            analysis_df['current_vol'], analysis_df['vol_diff']
        )

        # Now we are trying to find a breakpoint to split regimes between high and low vol
        if slope1 != 1:
            x_intersection = intercept1/(1-slope1)
        else:
            x_intersection = analysis_df['current_vol'].median()        # If slope is 1 which means regress line is equal to y=x, then our regime split will be at the median IV value
        
        # Whereever the condition is true, high_vol_regime will store a True value so high and low vol regime dfs are storing boolean values
        high_vol_regime = analysis_df['current_vol'] > x_intersection       # Rmr x values are current vol values so if they are greater than intersection between y=x, that means every x value current vol results in a higher forward vol
        low_vol_regime = analysis_df['current_vol'] <= x_intersection

        # Do the regression for high vol regime
        if high_vol_regime.sum() > 10:      # If there are more than 10 True values essentially cause True is 1 as an int
            slope_high, intercept_high, r_high, p_high, std_err_high = stats.linregress(
                analysis_df.loc[high_vol_regime, 'current_vol'], analysis_df.loc[high_vol_regime, 'vol_diff']       # Basically filters the columns to only have values where high vol is True
            )
        else:
            slope_high = intercept_high = r_high = p_high = std_err_high = None

        # Same thing for low vol regime
        if low_vol_regime.sum() > 10:
            slope_low, intercept_low, r_low, p_low, std_err_low = stats.linregress(
                analysis_df.loc[low_vol_regime, 'current_vol'], analysis_df.loc[low_vol_regime, 'vol_diff']
            )
        else:
            slope_low = intercept_low = r_low = p_low = std_err_low = None


        # Clear all of the subplots for graphing purposes
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()

        # Just added this
        self.fig.subplots_adjust(left=0.06, right=0.98, top=0.92, bottom=0.12, wspace=0.3)

        self.ax1.scatter(analysis_df["current_vol"], analysis_df['forward_30d_vol'], alpha=0.6, s=20)

        x_range = np.linspace(analysis_df['current_vol'].min(), analysis_df['current_vol'].max(), 100)  # 100 points for x range
        y_pred1 = slope1 * x_range + intercept1 
        self.ax1.plot(x_range, y_pred1, "r-", linewidth=2, label=f"Regression R^2 = {r1**2: .3f}")

        # Need to plot the y=x line
        min_val = min(analysis_df['current_vol'].min(), analysis_df['forward_30d_vol'].min())
        max_val = max(analysis_df['current_vol'].max(), analysis_df['forward_30d_vol'].max())
        self.ax1.plot([min_val, max_val], [min_val, max_val], "k--", linewidth=1, alpha=.7, label="y=x (No Change)")    # The point of this line is a reference, if the current IV is equal to the 30day forward IV, there is no change

        self.ax1.set_xlabel("Current IV", fontsize=5)
        self.ax1.set_ylabel("30-D Forward Avg IV", fontsize=5)
        self.ax1.set_title(f"Forward IV vs. Current IV", fontsize=5)
        self.ax1.legend(fontsize=5)
        self.ax1.grid(True, alpha=.3)
        self.ax1.tick_params(labelsize=5)


        """ Onto the Second Chart Now """

        self.ax2.scatter(analysis_df.loc[high_vol_regime, 'current_vol'], analysis_df.loc[high_vol_regime, 'vol_diff'],
                         alpha=.6, s=20, color='red', label='High Vol Regime')
        
        self.ax2.scatter(analysis_df.loc[low_vol_regime, 'current_vol'], analysis_df.loc[low_vol_regime, 'vol_diff'],
                         alpha=.6, s=20, color='blue', label='Low Vol Regime')

        # If high regression executed
        if slope_high is not None:
            x_high = np.linspace(analysis_df.loc[high_vol_regime, 'current_vol'].min(), 
                                 analysis_df.loc[high_vol_regime, 'current_vol'].max(), 100)
            y_pred_high = slope_high*x_high + intercept_high
            self.ax2.plot(x_high, y_pred_high, "r-", linewidth=2, label=f"High Regime R^2 = {r_high**2: .3f}")

        if slope_low is not None:
            x_low = np.linspace(analysis_df.loc[low_vol_regime, 'current_vol'].min(), 
                                 analysis_df.loc[low_vol_regime, 'current_vol'].max(), 100)
            y_pred_low = slope_low*x_low + intercept_low
            self.ax2.plot(x_low, y_pred_low, "b-", linewidth=2, label=f"Low Regime R^2 = {r_low**2: .3f}")


        # Rmr our no change for the unconditional regression was the y=x line. Now our y-value is the difference between current vol and forward vol. Now if the diff is 0, this is equal to our unconditional y=x line
        # Since our y value for ax2 is the diff, if that diff is 0, meaning y=0 horizontal line is our no change line where current vol = forward vol
        self.ax2.axhline(y=0, color="k", linestyle='--', linewidth=1, alpha=.7, label="No Change (y=0)")

        # Place a vertical x line at the point of intersection on the unconditional regression
        self.ax2.axvline(x=x_intersection, color="k", linestyle="--", linewidth=1, alpha=.7,
                         label=f"Regime Split (Vol = {x_intersection: .3f})")
        
        self.ax2.set_xlabel('Current Implied Volatility', fontsize=5)
        self.ax2.set_ylabel('Vol Diff (F - C)', fontsize=5)
        self.ax2.set_title('Vol Diff vs Current Vol (Regime Analysis)', fontsize=5)
        self.ax2.legend(fontsize=5, loc='best')
        self.ax2.grid(True, alpha=0.3)
        self.ax2.tick_params(labelsize=5)


        """ Code for the Third Graph Starts Here """

        # This is the graph for showing IV overtime
        self.ax3.plot(self.volatility_data.index, self.volatility_data['implied_vol'], 
                     label='Implied Volatility', linewidth=1)
        
        # Add regime bands
        vol_75th = self.volatility_data['implied_vol'].quantile(0.75)
        vol_25th = self.volatility_data['implied_vol'].quantile(0.25)
        
        # Add horizontal lines for seeing the percentiles
        self.ax3.axhline(y=vol_75th, color='red', linestyle='--', alpha=0.7, label='75th Percentile')
        self.ax3.axhline(y=vol_25th, color='green', linestyle='--', alpha=0.7, label='25th Percentile')
        self.ax3.axhline(y=self.volatility_data['implied_vol'].mean(), color='black', linestyle='-', alpha=0.7, label='Mean')

        if self.current_implied_vol is not None:
            self.ax3.scatter(self.volatility_data.index[-1], self.current_implied_vol, 
                           color='red', s=100, zorder=5, label='Current')
        
        self.ax3.set_xlabel('Date', fontsize=5)
        self.ax3.set_ylabel('IV', fontsize=5)
        self.ax3.set_title('IV Time Series', fontsize=5)
        self.ax3.legend(fontsize=5, loc='best')
        self.ax3.grid(True, alpha=0.3)
        
        # Rotate x-axis labels for better readability
        self.ax3.tick_params(axis='x', rotation=45, labelsize=3)
        self.ax3.tick_params(axis='y', labelsize=5)
        
        # Update canvas
        self.canvas.draw()

        # Log Everything
        self.log_message(f"Regression 1 - Forward Vol on Current Vol:")
        self.log_message(f"  Slope: {slope1:.4f}, Intercept: {intercept1:.4f}")
        self.log_message(f"  R²: {r1**2:.4f}, P-value: {p1:.4f}")
        self.log_message(f"  Intersection with y=x at Vol = {x_intersection:.4f}")
        
        self.log_message(f"Regression 2 - Vol Difference on Current Vol:")
        self.log_message(f"  Slope: {slope2:.4f}, Intercept: {intercept2:.4f}")
        self.log_message(f"  R²: {r2**2:.4f}, P-value: {p2:.4f}")
        
        self.log_message(f"Regime Analysis:")
        if slope_high is not None:
            self.log_message(f"  HIGH VOL regime (Vol > {x_intersection:.3f}):")
            self.log_message(f"    Slope: {slope_high:.4f}, Intercept: {intercept_high:.4f}")
            self.log_message(f"    R²: {r_high**2:.4f}, P-value: {p_high:.4f}")
            self.log_message(f"    Data points: {high_vol_regime.sum()}")
        else:
            self.log_message(f"  HIGH VOL regime: Insufficient data for regression")
            
        if slope_low is not None:
            self.log_message(f"  LOW VOL regime (Vol ≤ {x_intersection:.3f}):")
            self.log_message(f"    Slope: {slope_low:.4f}, Intercept: {intercept_low:.4f}")
            self.log_message(f"    R²: {r_low**2:.4f}, P-value: {p_low:.4f}")
            self.log_message(f"    Data points: {low_vol_regime.sum()}")
        else:
            self.log_message(f"  LOW VOL regime: Insufficient data for regression")
        
        # Trading insights
        if slope1 < 1:
            self.log_message("INSIGHT: Forward volatility tends to mean-revert (slope < 1)")
        else:
            self.log_message("INSIGHT: Forward volatility tends to trend (slope > 1)")
            
        if slope2 < 0:
            self.log_message("INSIGHT: High current volatility predicts lower future volatility (mean reversion)")
        else:
            self.log_message("INSIGHT: High current volatility predicts higher future volatility (momentum)")