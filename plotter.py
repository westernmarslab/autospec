#Plotter takes a Tk root object and uses it as a base to spawn Tk Toplevel plot windows.

import tkinter as tk
import pexpect
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

import matplotlib.backends.tkagg as tkagg
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class Plotter():
    def __init__(self, root):
        plt.close() 
        self.root=root
        self.plots={}
        self.canvases={}
 
    def new_plot(self,i):
        t = tk.Toplevel(self.root)
        t.wm_title('Incidence = '+str(i))
        fig = mpl.figure.Figure(figsize=(6,6))
        plot = fig.add_subplot(111)
        canvas = FigureCanvasTkAgg(fig, master=t)
        canvas.get_tk_widget().pack()
        canvas.draw()
        self.plots[i]=plot
        self.canvases[i]=canvas
        
        def on_closing():
            del self.plots[i]
            t.destroy()
        t.protocol("WM_DELETE_WINDOW", on_closing)
        
    def plot_spectrum(self,i,e, data):
        #If we've never plotted spectra at this incidence angle, make a whole new plot.
        if i not in self.plots:
            self.new_plot(i)
        #Next, plot data onto the appropriate plot.
        self.plots[i].plot(data[0],data[1])
        self.canvases[i].draw()
        
        