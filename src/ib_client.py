from ibapi.client import EClient
from ibapi.wrapper import EWrapper

class IBApp(EClient, EWrapper):

    def __init__(self):
        EClient.__init__(self, self)

        # Our dict to store historical data
        self.historical_data = {}
        self.connected = False

    def error(self, reqID, errorCode, errorString):

        """ This function is called by IB whenever there is an error in the code or with some request. """

        if errorCode == 2176 and "fractional share" in errorString.lower():
            print(f"Ignore this warning | Error {reqID} {errorCode} {errorString}")
        
        print(f"Error {reqID} {errorCode} {errorString}")

    def nextValidId(self, orderId):
        self.connected = True
        print("Connected to IB")

    def historicalData(self, reqID, bar):
        """ This is the function that IB is going to call when giving your requested historical data to you. """

        if reqID not in self.historical_data:
            # If the reqID, which is an arbitrary id is not in our dict, clear a list for it
            self.historical_data[reqID] = []

        # We are not going to append to the list the incoming bar
        self.historical_data[reqID].append({
            "date": bar.date ,
            "open": bar.open,
            "close": bar.close,
            "high": bar.high,
            "low": bar.low,
            "volume": bar.volume
        })

    def historicalDataEnd(self, reqID, start, end):
        """ This is the function that IB calls when the request is finished. It is Optional. """

        print(f"Historical Data has been recieved for reqID {reqID}")