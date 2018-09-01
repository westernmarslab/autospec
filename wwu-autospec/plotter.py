#Plotter takes a Tk root object and uses it as a base to spawn Tk Toplevel plot windows.

import tkinter as tk
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
        self.num=0
 
    def new_plot(self,title):
        top = tk.Toplevel(self.root)
        top.wm_title(title)
        fig = mpl.figure.Figure(figsize=(20,15))
        plot = fig.add_subplot(111)
        canvas = FigureCanvasTkAgg(fig, master=top)
        canvas.get_tk_widget().pack()
        canvas.draw()
        self.plots[title]=plot
        self.canvases[title]=canvas
        
        def on_closing():
            # for i in self.plots:
            #     del self.plots[i]
            # #del self.plots[i]
            top.destroy()
        top.protocol("WM_DELETE_WINDOW", on_closing)
        
    def plot_spectrum(self,i,e, data):
        #If we've never plotted spectra at this incidence angle, make a whole new plot.
        if i not in self.plots:
            self.new_plot('Incidence='+str(i))
        #Next, plot data onto the appropriate plot.
        self.plots[i].plot(data[0],data[1])
        self.canvases[i].draw()
        
    # def load_data(self, file):
    #     print('loading data')
    #     data = np.genfromtxt(file, skip_header=1, dtype=float,delimiter='\t')
    #     wavelengths=[]
    #     #reflectance=[[],[]]
    #     reflectance=[]
    #     for i, d in enumerate(data):
    #         if i==0: wavelengths=np.array(d) #the first column in my .tsv (now first row) was wavelength in nm
    #         else: #the other columns are all reflectance values
    #             d=np.array(d)
    #             reflectance.append(d)
    #             #d2=d/np.max(d) #d2 is normalized reflectance
    #             #reflectance[0].append(d)
    #             #reflectance[1].append(d2)
    #     print('returning data')
    #     print(wavelengths)
    #     print(reflectance)
    #     return wavelengths, reflectance
    #     

    def plot_spectra(self, title, file, caption, loglabels):
        try:
            wavelengths, reflectance, default_labels=self.load_data(file)
        except:
            print('Error loading data!')
            raise('Error loading data!')
            return
        print(loglabels)
        for i, label in enumerate(default_labels):
            if i==0:
                continue
            print(label)
            print(label[0:-3])
            if label in loglabels:
                if loglabels[label]!='':
                    print(loglabels[label])
                    default_labels[i]=loglabels[label]
            label2=label[0:-3]
            if label2 in loglabels:
                print('scolabel')
                if loglabels[label2]!='':
                    print(loglabels[label2])
                    default_labels[i]=loglabels[label2]
            
        self.new_plot(title)
        #self.num=0
        colors=['red','orange','yellow','greenyellow','cyan','dodgerblue','purple','magenta','red','orange','yellow','greenyellow','cyan','dodgerblue','purple','magenta','red','orange','yellow','greenyellow','cyan','dodgerblue','purple']
        for i,spectrum in enumerate(reflectance):
            if 'White reference' in default_labels[i+1]:
                continue
            self.plots[title].plot(wavelengths, spectrum, label=default_labels[i+1], color=colors[i])
        self.plots[title].set_title(title, fontsize=24)
        self.plots[title].set_ylabel('Relative Reflectance',fontsize=18)
        self.plots[title].set_xlabel('Wavelength (nm)',fontsize=18)
        self.plots[title].tick_params(labelsize=14)
        self.plots[title].legend()
        self.canvases[title].draw()
        
    def load_data(self, file):

        try:
            data = np.genfromtxt(file, names=True, dtype=float,delimiter='\t')
        except:
            data = np.genfromtxt(file, names=True, dtype=None,delimiter='\t')
        print('loaded!')

        labels=list(data.dtype.names)
        data=zip(*data)
        wavelengths=[]
        reflectance=[]
        for i, d in enumerate(data):
            if i==0: wavelengths=d #the first column in my .tsv (now first row) was wavelength in nm
            else: #the other columns are all reflectance values
                d=np.array(d)
                reflectance.append(d)
                #d2=d/np.max(d) #d2 is normalized reflectance
                #reflectance[0].append(d)
                #reflectance[1].append(d2)
        return wavelengths, reflectance, labels
            
        
        