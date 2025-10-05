import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext

root = tk.Tk()

root.title("Implied Volatility Trading Dashboard")
root.geometry("1400x1200")

# This is the main frame of the application so it is the container for the rest of the widgets and covers the entire dashboard
# The padding is there so the widgets inside this frame do not stick to the edges of the dashboard 
main_frame = ttk.Frame(root, padding="10")

# The grid is the geometry manager and it sets the main frame up in row 0 column 0 of the window
# Now if there was some other frame at row 0 and column 1, it would be to the right of main_frame
# Sticky tells main_frame to expand in all directions and cover the area other wise it would just be in the middle of the window
main_frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))

# Here, we are just configuring both the window and the mainframe to enlarge if the window is resized, to essentially grow in size with the window and take up any empty space
# The weight means to resize, if weight=0 (default) then as the window gets bigger or smaller, the widgets wouldn't move to fill the empty space
# Root config applies to the window and mainframe config applies to the elements within mainframe
root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1)
main_frame.columnconfigure(1, weight=1)     # Our app only has one column to all elements will resize if column 1 gets bigger or smaller
main_frame.rowconfigure(5, weight=1)        # Our app has 5 rows so all elements in these rows will also resize if mainframe gets bigger and since mainframe is the only frame in the window, if mainframe gets bigger, it implies the window gets bigger


# Create the connection frame
# LabelFrame is a container with a title that can hold other widgets
conn_frame = ttk.LabelFrame(main_frame, text="Interactive Brokers Connection", padding="5")


# This frame will sit in the first column and the first row
# columnspan 2 means that this widget spans across 2 columns at index 0 and 1
# pady add vertical padding (top, bottom) so in this case no padding above this widget but there is padding below the widget (10 px)
conn_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0,10))


# ttk.Label adds just a display text within the LabelFrame but the user cannot interact with it
ttk.Label(conn_frame, text="Host:").grid(row=0, column=0, padx=(0,5))
# This is the variable that will hold the input entered into the host input
host_var = tk.StringVar(value="127.0.0.1")
# Even though we created the host_var, we still need to put it in the connection frame which is done using ttk.Entry
# The grid will position the entry field next to the Host: label which is in column 1
ttk.Entry(conn_frame, textvariable=host_var, width=15).grid(row=0, column=1, padx=(0,10))


root.mainloop()