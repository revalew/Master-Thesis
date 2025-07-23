import tkinter as tk

import matplotlib.pyplot as plt

from utils import StepDataCollector

def main() -> None:
    root = tk.Tk()
    app = StepDataCollector(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        # Ensure clean exit
        plt.close('all')
        root.quit()

if __name__ == "__main__":
    main()