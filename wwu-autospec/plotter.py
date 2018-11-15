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
        
        self.tsv_titles=[]
        self.tabs=[]
        
        self.samples={}
    
    def update_tab_names(self):
        pass
        # try:
        #     print(self.notebook.tab(0))
        #     print(dir(type(self.notebook.tab(0))))
        # except:
        #     print(self.notebook.tab(0).width)
        
    def open_right_click_menu(self,event):
        print('hooray!')
        print(event)
        print(event.x)

    def plot_spectra(self, title, file, caption, exclude_wr=True):
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
                

        try:
            wavelengths, reflectance, labels=self.load_data(file)
        except:
            raise(Exception('Error loading data!'))
            return
            
        for i, label in enumerate(labels):
            print(label)
            print(reflectance[i])
        print()
        print()
            

        for i, spectrum_label in enumerate(labels):
            
            sample_label=spectrum_label.split('(i')[0]
            
            #If we don't have any data from this file yet, add it to the samples dictionary, and place the first sample inside.
            if file not in self.samples:
                self.samples[file]={}
                self.samples[file][sample_label]=Sample(sample_label, file,title)
            #If there is already data associated with this file, check if we've already got the sample in question there. If it doesn't exist, make it. If it does, just add this spectrum and label into its data dictionary.
            else:
                sample_exists=False 
                for sample in self.samples[file]:
                    if self.samples[file][sample].name==sample_label:
                        sample_exists=True

                if sample_exists==False:
                    self.samples[file][sample_label]=Sample(sample_label, file,title)
                    
            self.samples[file][sample_label].add_spectrum(spectrum_label)
            self.samples[file][sample_label].data[spectrum_label]['reflectance']=reflectance[i]
            self.samples[file][sample_label].data[spectrum_label]['wavelengths']=wavelengths


        for sample in self.samples[file]:
            tab=Tab(self, title,[self.samples[file][sample]])

    def savefig(self,title, sample=None):
        self.draw_plot(title, 'v2.0')
        self.plots[title].savefig(title)
        self.draw_plot(self.style)
        
        
    def load_data(self, file):

        data = np.genfromtxt(file, names=True, dtype=None,delimiter='\t',deletechars='')

        labels=list(data.dtype.names)[1:] #the first label is wavelengths
        for i in range(len(labels)):
            labels[i]=labels[i].replace('_(i=',' (i=').replace('_e=',' e=')
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
    def __init__(self, label, file, title):#colors):
        #self.colors=colors
        # self.index=-1
        # self.__next_color=self.colors[0]
        self.title=title
        self.name=label
        self.file=file
        self.data={}
        self.spectrum_labels=[]
    
    def add_spectrum(self,spectrum_label):
        self.data[spectrum_label]={'reflectance':[],'wavelengths':[]}
        self.spectrum_labels.append(spectrum_label)
        
    def set_colors(self, colors):
        self.colors=colors
        self.index=-1
        #self.__next_color=self.colors[0]
        
    def next_color(self):
        self.index+=1
        self.index=self.index%len(self.colors)
        return self.colors[self.index]
        
class Tab():
    def __init__(self, plotter, title, samples):
        self.plotter=plotter
        self.samples=samples
        self.title=title+ ': '+samples[0].name
        
        self.top=Frame(self.plotter.notebook)
        self.top.pack()
            
        self.plotter.notebook.add(self.top,text=self.title+' x')
        
        width=self.plotter.notebook.winfo_width()
        height=self.plotter.notebook.winfo_height()
        
        self.fig = mpl.figure.Figure(figsize=(width/self.plotter.dpi, height/self.plotter.dpi), dpi=self.plotter.dpi)
        #self.figs[title][samples]=fig
        self.mpl_plot = self.fig.add_subplot(111)


        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.top)
        self.canvas.get_tk_widget().bind('<Button-3>',lambda event: self.open_right_click_menu(event))
        self.vbar=Scrollbar(self.top,orient=VERTICAL)
        self.vbar.pack(side=RIGHT,fill=Y)
        self.vbar.config(command=self.canvas.get_tk_widget().yview)
        self.canvas.get_tk_widget().config(width=300,height=300)
        self.canvas.get_tk_widget().config(yscrollcommand=self.vbar.set)
        self.canvas.get_tk_widget().pack(side=LEFT,expand=True,fill=BOTH)
        
        #canvas.get_tk_widget().pack()
        
        self.plot=Plot(self.plotter, self.mpl_plot, self.samples,self.title)
        self.canvas.draw()
        
        # self.plots[title][samples]=plot
        # self.canvases[title][samples]=canvas
        # 
        
    
        
class Plot():
    def __init__(self, plotter, mpl_plot, samples,title): #samples is a dictionary like this: {title_associated_with_a_file:[first_sample_to_plot_from_that_file,second_sample_to_plot_from_that_file],title_associated_with_a_different_file:[sample_to_plot_from_that_file]}
        
        self.plotter=plotter
        self.samples=samples
        # self.fig=fig
        self.plot=mpl_plot#fig.add_subplot(111)
        self.title='' #This will be the text to put on the notebook tab
        self.colors=[]
        self.colors.append(['#004d80','#006bb3','#008ae6','#33adff','#80ccff','#b3e0ff','#e6f5ff']) #blue
        self.colors.append(['#145214','#1f7a1f','#2eb82e','#5cd65c','#99e699','#d6f5d6']) #green
        self.colors.append(['#661400','#b32400','#ff3300','#ff704d','#ff9980','#ffd6cc']) #red
        self.colors.append(['#330066','#5900b3','#8c1aff','#b366ff','#d9b3ff','#f2e6ff']) #purple
        
        
        self.files=[]
        for i, sample in enumerate(samples):
            sample.set_colors(self.colors[i%len(self.colors)])
            if sample.file not in self.files:
                self.files.append(sample.file)
                self.title=self.title+sample.file+' '+sample.name #The tab title will be a the title of each tsv followed by the associated samples being plotted.
            else:
                self.title=self.title.split(sample.file)[0] +sample.name+self.title.split(sample.file)[1]
                #self.title=self.title+','+sample.name
                
        self.title=title

        
        #If there is data from more than one data file, associate each sample name with that file. Otherwise, just use the sample name.

        # if len(self.files)>1:
        #     for sample in samples:
        #         for i, label in sample.labels:
        #             if sample.title not in sample.labels[i]:
        #                 sample.extended_labels[i]=sample.title+' '+label
        #                 sample.data[sample.extended_labels[i]]=sample.data[label]
        #                 
        #         sample.labels=sample.title+' '+sample.label
        #         for sample in samples[tsv_title]:
        #             label=tsv_title+' '+sample
        #             self.labels.append(label)
        #             self.data[label]=plotter.data[tsv_title][sample]
        # else:
        #     for tsv_title in samples:
        #         for sample in samples[tsv_title]:
        #             label=sample
        #             self.labels.append(label)
        #             self.data[label]=plotter.data[tsv_title][sample]

        
        self.draw()
        
        def on_closing():
            # for i in self.plots:
            #     del self.plots[i]
            # #del self.plots[i]
            top.destroy()
    
    def draw(self, exclude_wr=True):#self, title, sample=None, exclude_wr=True):

        
        for sample in self.samples:
            for label in sample.spectrum_labels:

                if 'White reference' in sample.name and exclude_wr and sample==None:
                    continue
                legend_label=label
                if True:#len(self.files)>1:
                    legend_label=sample.title+': '+label

                color=sample.next_color()
                self.plot.plot(sample.data[label]['wavelengths'], sample.data[label]['reflectance'], label=legend_label,color=color,linewidth=2)
        # if sample!=None:
        #     if title in self.title_bases:
        #         base=self.title_bases[title]
        #     else:
        #         base=title
        #     plot.set_title(base+' '+sample, fontsize=24)
        # else:
        self.plot.set_title(self.title, fontsize=24)
            
        self.plot.set_ylabel('Relative Reflectance',fontsize=18)
        self.plot.set_xlabel('Wavelength (nm)',fontsize=18)
        self.plot.tick_params(labelsize=14)
        self.plot.legend()


            
            
            

        
            
        
        