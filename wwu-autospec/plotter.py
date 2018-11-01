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
        self.sample_labels={}
        self.num=0
        self.notebook=notebook
        self.dpi=dpi
        self.titles=[]
        self.style=style
        plt.style.use(style)
        self.title_bases={}
        
        
    def embed_plot(self,title, sample=None):
        if sample!=None:
            self.figs[title]={}
            self.plots[title]={}
            self.canvases[title]={}
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
        if title in self.title_bases:
            base=self.title_bases[title]
        else:
            base=title
        self.notebook.add(top,text=base+' '+sample+' x')
        width=self.notebook.winfo_width()
        height=self.notebook.winfo_height()
        fig = mpl.figure.Figure(figsize=(width/self.dpi, height/self.dpi), dpi=self.dpi)
        self.figs[title][sample]=fig
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
        self.plots[title][sample]=plot
        self.canvases[title][sample]=canvas
        
        def on_closing():
            # for i in self.plots:
            #     del self.plots[i]
            # #del self.plots[i]
            top.destroy()
        #top.protocol("WM_DELETE_WINDOW", on_closing)
        
    # def plot_spectrum(self,i,e, data):

    #       #If we've never plotted spectra at this incidence angle, make a whole new plot.
    #     if i not in self.plots:
    #         self.embed_plot('Incidence='+str(i))
    #     #Next, plot data onto the appropriate plot.
    #     self.plots[i].plot(data[0],data[1])
    #     self.canvases[i].draw()
        
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
        if title=='':
            title='Plot '+str(self.num+1)
            self.num+=1
        elif title in self.titles:
            j=1
            new=title+' ('+str(j)+')'
            while new in self.titles:
                j+=1
                new=title+' ('+str(j)+')'
            base=title
            title=new
            self.title_bases[title]=base
            print('saving a base:')
            print(base)
        self.titles.append(title)
        

        
        #self.sample_labels[title]=[]
        self.data[title]={}
        sample_labels=[]
        try:
            wavelengths, reflectance, labels=self.load_data(file)
        except:
            print('Error loading data!')
            raise(Exception('Error loading data!'))
            return
            

        for i, label in enumerate(labels):
            if i==0:
                continue

            if label in loglabels:
                if loglabels[label]!='':
                    labels[i]=loglabels[label]
            label2=label[0:-3]
            if label2 in loglabels:
                if loglabels[label2]!='':
                    labels[i]=loglabels[label2]
            sample_label=labels[i].split(' (i=')[0]
            if sample_label not in sample_labels:
                sample_labels.append(sample_label)
                self.data[title][sample_label]={}
                self.data[title][sample_label]['labels']=[]
                self.data[title][sample_label]['wavelengths']=wavelengths
                self.data[title][sample_label]['reflectance']=[]
            self.data[title][sample_label]['labels'].append(labels[i])
            self.data[title][sample_label]['reflectance'].append(reflectance[i-1])

            
                    

        #self.data[title]={'wavelengths':wavelengths,'reflectance':reflectance,'labels':labels}

        if False:
            self.data[title]={'wavelengths':wavelengths,'reflectance':reflectance,'labels':labels}
            self.embed_plot(title)
            self.draw_plot(title)
            self.canvases[title].draw()
        elif True:
            for sample in self.data[title]:
                self.embed_plot(title, sample)
                self.draw_plot(title, sample)
                self.canvases[title][sample].draw()
                
        #self.num=0
        # light_colors=['red','orange','yellow','greenyellow','cyan','dodgerblue','purple','magenta','red','orange','yellow','greenyellow','cyan','dodgerblue','purple','magenta','red','orange','yellow','greenyellow','cyan','dodgerblue','purple']
        # dark_colors=['mediumaquamarine','lemonchiffon','mediumpurple','lightcoral','skyblue','sandybrown','yellowgreen','pink','lightgray','mediumpurple']

        
    def draw_plot(self, title, sample=None, exclude_wr=True):
        # if sample=='White reference':
        #     return
        if sample!=None:
            labels=self.data[title][sample]['labels']
            wavelengths=self.data[title][sample]['wavelengths']
            reflectance=self.data[title][sample]['reflectance']
            plot=self.plots[title][sample]
        else:
            labels=self.data[title]['labels']
            wavelengths=self.data[title]['wavelengths']
            reflectance=self.data[title]['reflectance']
            plot=self.plots[title]
        sample_names=[]
        samples={}
        colors=[]
        colors.append(['#004d80','#006bb3','#008ae6','#33adff','#80ccff','#b3e0ff','#e6f5ff']) #blue
        colors.append(['#145214','#1f7a1f','#2eb82e','#5cd65c','#99e699','#d6f5d6']) #green
        colors.append(['#661400','#b32400','#ff3300','#ff704d','#ff9980','#ffd6cc']) #red
        colors.append(['#330066','#5900b3','#8c1aff','#b366ff','#d9b3ff','#f2e6ff']) #purple
        
        #for i,spectrum in enumerate(reflectance):
        for i in range(len(labels)):
            label=labels[i]
            sample_label=label.split(' (')[0]
            if 'White reference' in label and exclude_wr and sample==None:
                 continue
            if sample_label not in sample_names:
                num=len(sample_names)
                sample_names.append(sample_label)
                samples[sample_label]=Sample(colors[num%len(colors)])
            color=samples[sample_label].next_color()
            plot.plot(wavelengths, reflectance[i], label=label,color=color,linewidth=2)
        if sample!=None:
            if title in self.title_bases:
                base=self.title_bases[title]
            else:
                base=title
            plot.set_title(base+' '+sample, fontsize=24)
        else:
            plot.set_title(title, fontsize=24)
            
        plot.set_ylabel('Relative Reflectance',fontsize=18)
        plot.set_xlabel('Wavelength (nm)',fontsize=18)
        plot.tick_params(labelsize=14)
        plot.legend()
        
        
        #self.figs[title][sample].savefig(title)
    
    def savefig(self,title, sample=None):
        self.draw_plot(title, 'v2.0')
        self.plots[title].savefig(title)
        self.draw_plot(self.style)
        
        
    def load_data(self, file):

        data = np.genfromtxt(file, names=True, dtype=float,delimiter='\t')

        labels=list(data.dtype.names)
        data=zip(*data)
        wavelengths=[]
        reflectance=[]
        for i, d in enumerate(data):
            if i==0: wavelengths=d[60:] #the first column in my .tsv (now first row) was wavelength in nm. Exclude the first 100 values because they are typically very noisy.
            else: #the other columns are all reflectance values
                d=np.array(d)
                reflectance.append(d[60:])
                #d2=d/np.max(d) #d2 is normalized reflectance
                #reflectance[0].append(d)
                #reflectance[1].append(d2)
        return wavelengths, reflectance, labels
        
class Sample():
    def __init__(self, colors):
        self.colors=colors
        self.index=-1
        self.__next_color=self.colors[0]
    
    def next_color(self):
        self.index+=1
        self.index=self.index%len(self.colors)
        return self.colors[self.index]

        
            
        
        