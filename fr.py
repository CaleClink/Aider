import tkinter as tk
from tkinter import ttk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class FRDMCalculator:
    def __init__(self, master):
        self.master = master
        self.master.title("FRDM Calculator")
        self.master.geometry("1200x700")
        self.master.configure(bg='#2E2E2E')

        # Set the title bar color to black
        self.master.tk_setPalette(background='#000000', foreground='white')

        self.df = pd.read_csv('NEW_GE_VDAS_HDAS_Channel_ID.csv')
        self.show_ring = tk.BooleanVar(value=False)  # Default off

        self.create_widgets()

    def create_widgets(self):
        # Top frame for input and output
        top_frame = ttk.Frame(self.master, padding="10", style='Dark.TFrame')
        top_frame.pack(fill=tk.X)

        # Input section
        input_frame = ttk.Frame(top_frame, style='Dark.TFrame')
        input_frame.pack(side=tk.LEFT)

        ttk.Label(input_frame, text="Input measurement from isocenter (mm):", style='Dark.TLabel').pack(side=tk.LEFT)
        self.input_entry = ttk.Entry(input_frame, font=('Helvetica', 20), width=5)
        self.input_entry.pack(side=tk.LEFT, padx=5)
        self.input_entry.bind('<Return>', self.calculate)

        # Toggle Ring Button
        self.toggle_button = ttk.Checkbutton(input_frame, text="Show Ring", variable=self.show_ring, 
                                             command=self.toggle_ring, style='Large.TCheckbutton')
        self.toggle_button.pack(side=tk.LEFT, padx=10)

        # Output section
        self.output_frame = ttk.Frame(top_frame, style='Dark.TFrame')
        self.output_frame.pack(side=tk.LEFT, padx=20)

        # Warning frame
        self.warning_frame = ttk.Frame(self.master, padding="5", style='Dark.TFrame')
        self.warning_frame.pack(fill=tk.X)

        # Visualization frame
        self.viz_frame = ttk.Frame(self.master, padding="10", style='Dark.TFrame')
        self.viz_frame.pack(fill=tk.BOTH, expand=True)

        self.fig, self.ax = plt.subplots(figsize=(14, 6), facecolor='#2E2E2E')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.viz_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.draw_frdm_modules()

        # Configure styles
        style = ttk.Style()
        style.configure('Dark.TFrame', background='#2E2E2E')
        style.configure('Dark.TLabel', background='#2E2E2E', foreground='white', font=('Helvetica', 16))
        style.configure('Large.TLabel', font=('Helvetica', 20, 'bold'), background='#2E2E2E', foreground='white')
        style.configure('Warning.TLabel', font=('Helvetica', 16, 'bold'), foreground='red', background='#2E2E2E')
        style.configure('Large.TCheckbutton', background='#2E2E2E', foreground='white', font=('Helvetica', 16))

    def calculate(self, event=None):
        try:
            input_mm = float(self.input_entry.get())
            current_row = self.df[(self.df['mm'] <= input_mm) & (self.df['mm'].shift(-1) > input_mm)].iloc[0]

            low_channel = round(current_row['low ch'], 1)
            high_channel = round(current_row['high ch'], 1)
            low_frdm = int(current_row['Low FRDM'])
            high_frdm = int(current_row['High FRDM'])

            for widget in self.output_frame.winfo_children():
                widget.destroy()
            for widget in self.warning_frame.winfo_children():
                widget.destroy()

            # Check for warnings
            next_row = self.df[self.df['mm'] > input_mm].iloc[0] if input_mm < self.df['mm'].max() else None
            prev_row = self.df[self.df['mm'] < input_mm].iloc[-1] if input_mm > self.df['mm'].min() else None

            low_warning = False
            high_warning = False
            warning_message = ""
            close_frdm = []

            if next_row is not None and abs(next_row['mm'] - input_mm) <= 2:
                if next_row['Low FRDM'] != current_row['Low FRDM']:
                    low_warning = True
                    warning_message += f"Low channel is close to the edge near FRDM {int(next_row['Low FRDM'])}. "
                    close_frdm.append(int(next_row['Low FRDM']))
                if next_row['High FRDM'] != current_row['High FRDM']:
                    high_warning = True
                    warning_message += f"High channel is close to the edge near FRDM {int(next_row['High FRDM'])}. "
                    close_frdm.append(int(next_row['High FRDM']))

            if prev_row is not None and abs(input_mm - prev_row['mm']) <= 2:
                if prev_row['Low FRDM'] != current_row['Low FRDM']:
                    low_warning = True
                    warning_message += f"Low channel is close to the edge near FRDM {int(prev_row['Low FRDM'])}. "
                    close_frdm.append(int(prev_row['Low FRDM']))
                if prev_row['High FRDM'] != current_row['High FRDM']:
                    high_warning = True
                    warning_message += f"High channel is close to the edge near FRDM {int(prev_row['High FRDM'])}. "
                    close_frdm.append(int(prev_row['High FRDM']))

            # Display results
            ttk.Label(self.output_frame, text=f"Low Channel: {low_channel} (FRDM {low_frdm})", 
                      style='Large.TLabel', foreground='blue').pack(side=tk.LEFT, padx=10)
            ttk.Label(self.output_frame, text=f"High Channel: {high_channel} (FRDM {high_frdm})", 
                      style='Large.TLabel', foreground='green').pack(side=tk.LEFT, padx=10)

            if warning_message:
                ttk.Label(self.warning_frame, text="WARNING: " + warning_message, 
                          style='Warning.TLabel', wraplength=1180).pack(anchor='w')

            self.highlight_frdm_modules(input_mm, low_frdm, high_frdm, low_warning, high_warning, close_frdm)

        except ValueError:
            ttk.Label(self.output_frame, text="Invalid input. Please enter a valid number.", 
                      style='Warning.TLabel').pack(anchor='w')

    def draw_frdm_modules(self):
        self.ax.clear()
        self.ax.set_facecolor('#2E2E2E')
        for i in range(1, 58):
            self.ax.add_patch(plt.Rectangle((i-1, 0), 1, 0.4, fill=False, edgecolor='white'))
            self.ax.text(i-0.5, 0.2, str(i), ha='center', va='center', color='white', fontsize=20)
        self.ax.set_xlim(0, 57)
        self.ax.set_ylim(-0.6, 0.8)
        self.ax.axis('off')
        self.canvas.draw()

    def highlight_frdm_modules(self, input_mm, low_frdm, high_frdm, low_warning, high_warning, close_frdm):
        self.draw_frdm_modules()
        
        # Set constant FRDM box height
        frdm_height = 0.4
        
        # Highlight the calculated FRDMs
        self.ax.add_patch(plt.Rectangle((low_frdm-1, 0), 1, frdm_height, fill=True, facecolor='red', alpha=0.5))
        self.ax.add_patch(plt.Rectangle((high_frdm-1, 0), 1, frdm_height, fill=True, facecolor='red', alpha=0.5))

        # Highlight close proximity modules
        for frdm in close_frdm:
            self.ax.add_patch(plt.Rectangle((frdm-1, 0), 1, frdm_height, fill=True, facecolor='yellow', alpha=0.3))

        # Calculate circle parameters
        center_x = (low_frdm + high_frdm - 1) / 2
        center_y = frdm_height / 2
        radius = (high_frdm - low_frdm) / 2

        # Draw circle if toggled on
        if self.show_ring.get():
            circle = plt.Circle((center_x, center_y), radius, fill=False, edgecolor='white', linewidth=2, transform=self.ax.transData)
            self.ax.add_artist(circle)
            
            # Set aspect to 'equal' to ensure circle is round
            self.ax.set_aspect('equal', adjustable='box')
            
            # Adjust the y-limits to fit the circle while maintaining FRDM box height
            y_min = min(0, center_y - radius)
            y_max = max(frdm_height, center_y + radius)
            padding = 0.1 * (y_max - y_min)  # Add 10% padding
            self.ax.set_ylim(y_min - padding, y_max + padding)
        else:
            self.ax.set_aspect('auto')
            self.ax.set_ylim(-0.1, frdm_height + 0.1)  # Add a small padding

        # Draw lines
        self.ax.plot([low_frdm-1, center_x], [frdm_height/2, frdm_height/2], color='blue', linewidth=6)
        self.ax.plot([center_x, high_frdm], [frdm_height/2, frdm_height/2], color='green', linewidth=6)

        # Add input value text
        self.ax.text(low_frdm-0.5, -0.05, f"{input_mm:.1f}mm", ha='center', va='top', color='blue', fontsize=16)
        self.ax.text(high_frdm-0.5, -0.05, f"{input_mm:.1f}mm", ha='center', va='top', color='green', fontsize=16)
        self.ax.text(center_x, -0.05, f"{input_mm*2:.1f}mm", ha='center', va='top', color='red', fontsize=16)

        # Add vertical lines
        self.ax.plot([low_frdm-0.5, low_frdm-0.5], [-0.025, 0], color='white', linewidth=1)
        self.ax.plot([high_frdm-0.5, high_frdm-0.5], [-0.025, 0], color='white', linewidth=1)

        self.ax.set_xlim(0, 57)
        self.canvas.draw()

    def toggle_ring(self):
        if self.input_entry.get():
            self.calculate()

if __name__ == "__main__":
    root = tk.Tk()
    app = FRDMCalculator(root)
    root.mainloop()
