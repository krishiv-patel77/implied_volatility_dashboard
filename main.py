import tkinter as tk
from src.dashboard import ImpliedVolatilityDashboard

def main():
    root = tk.Tk()
    app = ImpliedVolatilityDashboard(root)
    root.mainloop()

if __name__ == "__main__":
    main()
