#Plotter takes a Tk root object and uses it as a base to spawn Tk Toplevel plot windows.

import tkinter as tk
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from tkinter import *

import matplotlib.backends.tkagg as tkagg
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class Plotter():
    def __init__(self, notebook,dpi, style):

        self.plots={}
        self.figs={}
        self.canvases={}
        self.data={}
        self.num=0
        self.notebook=notebook
        self.dpi=dpi
        self.titles=[]
        self.style=style
        plt.style.use(style)
        
        
    def embed_plot(self,title):
 
        #top = tk.Toplevel(self.root)
        #top.wm_title(title)
        close_img=tk.PhotoImage("img_close", data='''
                R0lGODlhCAAIAMIBAAAAADs7O4+Pj9nZ2Ts7Ozs7Ozs7Ozs7OyH+EUNyZWF0ZWQg
                d2l0aCBHSU1QACH5BAEKAAQALAAAAAAIAAgAAAMVGDBEA0qNJyGw7AmxmuaZhWEU
                5kEJADs=
                ''')
        top=Frame(self.notebook)
        top.pack()
        #self.notebook.add(top,text=title,image=close_img,compound=tk.RIGHT)
        self.notebook.add(top,text=title+' x')
        width=self.notebook.winfo_width()
        height=self.notebook.winfo_height()
        fig = mpl.figure.Figure(figsize=(width/self.dpi, height/self.dpi), dpi=self.dpi)
        self.figs[title]=fig
        plot = fig.add_subplot(111)
        canvas = FigureCanvasTkAgg(fig, master=top)
        vbar=Scrollbar(top,orient=VERTICAL)
        vbar.pack(side=RIGHT,fill=Y)
        vbar.config(command=canvas.get_tk_widget().yview)
        canvas.get_tk_widget().config(width=300,height=300)
        canvas.get_tk_widget().config(yscrollcommand=vbar.set)
        canvas.get_tk_widget().pack(side=LEFT,expand=True,fill=BOTH)
        
        #canvas.get_tk_widget().pack()
        canvas.draw()
        self.plots[title]=plot
        self.canvases[title]=canvas
        
        def on_closing():
            # for i in self.plots:
            #     del self.plots[i]
            # #del self.plots[i]
            top.destroy()
        #top.protocol("WM_DELETE_WINDOW", on_closing)
        
    def plot_spectrum(self,i,e, data):

        #If we've never plotted spectra at this incidence angle, make a whole new plot.
        if i not in self.plots:
            self.embed_plot('Incidence='+str(i))
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

    def plot_spectra(self, title, file, caption, loglabels,exclude_wr=True):
        try:
            wavelengths, reflectance, labels=self.load_data(file)
        except:
            print('Error loading data!')
            raise('Error loading data!')
            return

        for i, label in enumerate(labels):
            if i==0:
                continue

            if label in loglabels:
                if loglabels[label]!='':
                    labels[i]=loglabels[label]
            label2=label[0:-3]
            if label2 in loglabels:
                print('and it is there! +sco')
                if loglabels[label2]!='':
                    print(loglabels[label2])
                    labels[i]=loglabels[label2]
                    
        if title=='':
            title='Plot '+str(self.num+1)
            self.num+=1
        elif title in self.titles:
            j=1
            new=title+' ('+str(j)+')'
            while new in self.titles:
                j+=1
                new=title+' ('+str(j)+')'
            title=new
        self.titles.append(title)
        self.data[title]={'wavelengths':wavelengths,'reflectance':reflectance,'labels':labels}
        self.embed_plot(title)
        self.draw_plot(title)
        self.canvases[title].draw()
        #self.num=0
        # light_colors=['red','orange','yellow','greenyellow','cyan','dodgerblue','purple','magenta','red','orange','yellow','greenyellow','cyan','dodgerblue','purple','magenta','red','orange','yellow','greenyellow','cyan','dodgerblue','purple']
        # dark_colors=['mediumaquamarine','lemonchiffon','mediumpurple','lightcoral','skyblue','sandybrown','yellowgreen','pink','lightgray','mediumpurple']

        
    def draw_plot(self, title, exclude_wr=True):
        labels=self.data[title]['labels']
        wavelengths=self.data[title]['wavelengths']
        reflectance=self.data[title]['reflectance']
        
        for i,spectrum in enumerate(reflectance):
            if 'White reference' in labels[i+1] and exclude_wr:
                continue
            if True: #dark in style
                self.plots[title].plot(wavelengths, spectrum, label=labels[i+1])
        
        self.plots[title].set_title(title, fontsize=24)
        self.plots[title].set_ylabel('Relative Reflectance',fontsize=18)
        self.plots[title].set_xlabel('Wavelength (nm)',fontsize=18)
        self.plots[title].tick_params(labelsize=14)
        self.plots[title].legend()
        
        
        self.figs[title].savefig(title)
    
    def savefig(self,title):
        self.draw_plot(title, 'v2.0')
        self.plots[title].savefig(title)
        self.draw_plot(self.style)
        
        
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
            
        
        