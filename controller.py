#The controller runs the main thread controlling the program.
#It creates and starts a View object, which extends Thread and will show a pygame window.

dev=True
test=True
online=False

from tkinter import *
from tkinter import messagebox
import imp
import threading
import tkinter as tk
from tkinter import ttk
import pygame
import pexpect
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import matplotlib.backends.tkagg as tkagg
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime
import time
from threading import Thread
import os

#From pyzo shell, looks in /home/khoza/Python for modules
#From terminal, it will look in current directory
if dev: sys.path.append('auto_goniometer')

import robot_model
import robot_view
import plotter

global PROCESS_COUNT
global SPECTRUM_COUNT

#This is needed because otherwise changes won't show up until you restart the shell.
if dev:
    imp.reload(robot_model)
    from robot_model import Model
    imp.reload(robot_view)
    from robot_view import View
    imp.reload(plotter)
    from plotter import Plotter
    

global spec_save_path
spec_save_path=''
global spec_basename
spec_basename=''
global g_spec_num
g_spec_num=None

global user_cmds
user_cmds=[]
global user_cmd_index
user_cmd_index=-1

share_loc='/run/user/1000/gvfs/smb-share:server=melissa,share=kathleen'
write_command_loc=share_loc+'/commands/from_control'
read_command_loc=share_loc+'/commands/from_spec'
config_loc='/home/khoza/Python/auto_goniometer/config'

def main():
    
    delme=os.listdir(read_command_loc)
    for file in delme:
        os.remove(read_command_loc+'/'+file)
        
    delme=os.listdir(write_command_loc)
    for file in delme:
        os.remove(write_command_loc+'/'+file)
    
    listener=Listener(read_command_loc)

    control=Controller(listener)
    
    

class Controller():
    def __init__(self, listener):
        self.listener=listener
        self.listener.set_controller(self)
        self.listener.start()
        self.share_loc='/run/user/1000/gvfs/smb-share:server=melissa,share=kathleen'
        self.write_command_loc=self.share_loc+'/commands/from_control'
        self.read_command_loc='self.share_loc+/commands/from_spec'
        self.config_loc='/home/khoza/Python/auto_goniometer/config'
        
        self.log_filename='log_'+datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')+'.txt'
        with open(self.log_filename,'w+') as log:
            log.write(str(datetime.datetime.now())+'\n')
        if dev: plt.close('all')
    
        self.view=View()
        self.view.start()
        
        self.master=Tk()
        self.notebook=ttk.Notebook(self.master)
        self.plotter=Plotter(self.master)
    
        self.model=Model(self.view, self.plotter, self.share_loc, self.write_command_loc, False, False)
        
        self.take_spectrum_with_bad_i_or_e=False
    
            
        master_bg='white'
        self.master.configure(background = master_bg)
        self.master.title('Control')
    
        padx=3
        pady=3
        border_color='light gray'
        bg='white'
        button_width=15
        
        process_config=open(self.config_loc+'/process_directories','r')
        input_dir=''
        output_dir=''
        try:
            input_dir=process_config.readline().strip('\n')
            output_dir=process_config.readline().strip('\n')
        except:
            print('invalid config')
    
        self.spec_save_config=open(self.config_loc+'/spec_save','r')
        spec_save_path=''
        spec_basename=''
        spec_startnum=''
        
        try:
            spec_save_path=self.spec_save_config.readline().strip('\n')
            spec_basename=self.spec_save_config.readline().strip('\n')
            spec_startnum=self.spec_save_config.readline().strip('\n')
        except:
            print('invalid config')
        
        self.auto_frame=Frame(self.notebook, bg=bg)
    
        self.spec_save_path_label=Label(self.auto_frame,padx=padx,pady=pady,bg=bg,text='Save directory:')
        self.spec_save_path_label.pack(padx=padx,pady=pady)
        self.spec_save_path_entry=Entry(self.auto_frame, width=50,bd=3)
        self.spec_save_path_entry.insert(0, spec_save_path)
        self.spec_save_path_entry.pack(padx=padx, pady=pady)
    
        self.spec_save_frame=Frame(self.auto_frame, bg=bg)
        self.spec_save_frame.pack()
        
        self.spec_basename_label=Label(self.spec_save_frame,pady=pady,bg=bg,text='Base name:')
        self.spec_basename_label.pack(side=LEFT,pady=(5,15),padx=(0,0))
        self.spec_basename_entry=Entry(self.spec_save_frame, width=10,bd=3)
        self.spec_basename_entry.pack(side=LEFT,padx=(5,5), pady=pady)
        self.spec_basename_entry.insert(0,spec_basename)
        
        self.spec_startnum_label=Label(self.spec_save_frame,padx=padx,pady=pady,bg=bg,text='Number:')
        self.spec_startnum_label.pack(side=LEFT,pady=pady)
        self.spec_startnum_entry=Entry(self.spec_save_frame, width=10,bd=3)
        self.spec_startnum_entry.insert(0,spec_startnum)
        self.spec_startnum_entry.pack(side=RIGHT, pady=pady)
        
        self.spec_save_config=IntVar()
        self.spec_save_config_check=Checkbutton(self.auto_frame, text='Save file configuration', bg=bg, pady=pady,highlightthickness=0, variable=self.spec_save_config)
        self.spec_save_config_check.pack(pady=pady)
        self.spec_save_config_check.select()
        
        self.auto_check_frame=Frame(self.auto_frame, bg=bg)
        self.auto_check_frame.pack()
        self.auto=IntVar()
        self.auto_check=Checkbutton(self.auto_check_frame, text='Automatically iterate through viewing geometries', bg=bg, pady=pady,highlightthickness=0, variable=self.auto, command=self.auto_cycle_check)
        self.auto_check.pack(side=LEFT, pady=pady)
        
        self.manual_frame=Frame(self.auto_frame, bg=bg)
        self.manual_frame.pack()
        
        self.man_incidence_label=Label(self.manual_frame,padx=padx,pady=pady,bg=bg,text='Incidence angle:')
        self.man_incidence_label.pack(side=LEFT, padx=padx,pady=(0,8))
        self.man_incidence_entry=Entry(self.manual_frame, width=10)
        self.man_incidence_entry.pack(side=LEFT)
        self.man_emission_label=Label(self.manual_frame, padx=padx,pady=pady,bg=bg, text='Emission angle:')
        self.man_emission_label.pack(side=LEFT, padx=(10,0))
        self.man_emission_entry=Entry(self.manual_frame, width=10)
        self.man_emission_entry.pack(side=LEFT, padx=(0,20))
        
        self.man_notes_label=Label(self.auto_frame, padx=padx,pady=pady,bg=bg, text='Notes:')
        self.man_notes_label.pack()
        self.man_notes_entry=Entry(self.auto_frame, width=60)
        self.man_notes_entry.pack()
        
        self.top_frame=Frame(self.auto_frame,padx=padx,pady=pady,bd=2,highlightbackground=border_color,highlightcolor=border_color,highlightthickness=0,bg=bg)
        #self.top_frame.pack()
        self.light_frame=Frame(self.top_frame,bg=bg)
        self.light_frame.pack(side=LEFT)
        self.light_label=Label(self.light_frame,padx=padx, pady=pady,bg=bg,text='Light Source')
        self.light_label.pack()
        
        light_labels_frame = Frame(self.light_frame,bg=bg,padx=padx,pady=pady)
        light_labels_frame.pack(side=LEFT)
        
        light_start_label=Label(light_labels_frame,padx=padx,pady=pady,bg=bg,text='Start:')
        light_start_label.pack(pady=(0,8))
        light_end_label=Label(light_labels_frame,bg=bg,padx=padx,pady=pady,text='End:',fg='lightgray')
        light_end_label.pack(pady=(0,5))
    
        light_increment_label=Label(light_labels_frame,bg=bg,padx=padx,pady=pady,text='Increment:',fg='lightgray')
        light_increment_label.pack(pady=(0,5))
    
        
        light_entries_frame=Frame(self.light_frame,bg=bg,padx=padx,pady=pady)
        light_entries_frame.pack(side=RIGHT)
        
    
        
        light_start_entry=Entry(light_entries_frame,bd=3,width=10)
        light_start_entry.pack(padx=padx,pady=pady)
        light_start_entry.insert(0,'10')
        
        light_end_entry=Entry(light_entries_frame,bd=1,width=10, highlightbackground='white')
        light_end_entry.pack(padx=padx,pady=pady)    
        light_increment_entry=Entry(light_entries_frame,bd=1,width=10,highlightbackground='white')
        light_increment_entry.pack(padx=padx,pady=pady)
        
        detector_frame=Frame(self.top_frame,bg=bg)
        detector_frame.pack(side=RIGHT)
        
        detector_label=Label(detector_frame,padx=padx, pady=pady,bg=bg,text='Detector')
        detector_label.pack()
        
        detector_labels_frame = Frame(detector_frame,bg=bg,padx=padx,pady=pady)
        detector_labels_frame.pack(side=LEFT)
        
        detector_start_label=Label(detector_labels_frame,padx=padx,pady=pady,bg=bg,text='Start:')
        detector_start_label.pack(pady=(0,8))
        detector_end_label=Label(detector_labels_frame,bg=bg,padx=padx,pady=pady,text='End:',fg='lightgray')
        detector_end_label.pack(pady=(0,5))
    
        detector_increment_label=Label(detector_labels_frame,bg=bg,padx=padx,pady=pady,text='Increment:',fg='lightgray')
        detector_increment_label.pack(pady=(0,5))
    
        
        detector_entries_frame=Frame(detector_frame,bg=bg,padx=padx,pady=pady)
        detector_entries_frame.pack(side=RIGHT)
        detector_start_entry=Entry(detector_entries_frame,bd=3,width=10)
        detector_start_entry.pack(padx=padx,pady=pady)
        detector_start_entry.insert(0,'0')
        
        detector_end_entry=Entry(detector_entries_frame,bd=1,width=10,highlightbackground='white')
        detector_end_entry.pack(padx=padx,pady=pady)
        
        detector_increment_entry=Entry(detector_entries_frame,bd=1,width=10, highlightbackground='white')
        detector_increment_entry.pack(padx=padx,pady=pady)
        
    
        
        self.auto_check_frame=Frame(self.auto_frame, bg=bg)
        #self.auto_check_frame.pack()
        self.auto_process=IntVar()
        self.auto_process_check=Checkbutton(self.auto_check_frame, text='Process data', bg=bg, highlightthickness=0)
        self.auto_process_check.pack(side=LEFT)
        
        self.auto_plot=IntVar()
        self.auto_plot_check=Checkbutton(self.auto_check_frame, text='Plot spectra', bg=bg, highlightthickness=0)
        self.auto_plot_check.pack(side=LEFT)
        
        gen_bg=bg
        
        self.gen_frame=Frame(self.auto_frame,padx=padx,pady=pady,bd=2,highlightbackground=border_color,highlightcolor=border_color,highlightthickness=0,bg=gen_bg)
        self.gen_frame.pack()
        
        self.opt_button=Button(self.gen_frame, text='Optimize', padx=padx, pady=pady,width=button_width, bg='light gray', command=self.opt)
        self.opt_button.pack(padx=padx,pady=pady, side=LEFT)
        self.wr_button=Button(self.gen_frame, text='White Reference', padx=padx, pady=pady, width=button_width, bg='light gray', command=self.wr)
        self.wr_button.pack(padx=padx,pady=pady, side=LEFT)
    
        self.go_button=Button(self.gen_frame, text='Take Spectrum', padx=padx, pady=pady, width=button_width,bg='light gray', command=self.go)
        self.go_button.pack(padx=padx,pady=pady, side=LEFT)
        
        #***************************************************************
        # Frame for manual control
        
        self.dumb_frame=Frame(self.notebook, bg=bg, pady=2*pady)
        self.dumb_frame.pack()
        # entries_frame=Frame(man_frame, bg=bg)
        # entries_frame.pack(fill=BOTH, expand=True)
        # man_light_label=Label(entries_frame,padx=padx, pady=pady,bg=bg,text='Instrument positions:')
        # man_light_label.pack()
        # man_light_label=Label(entries_frame,padx=padx,pady=pady,bg=bg,text='Incidence:')
        # man_light_label.pack(side=LEFT, padx=(30,5),pady=(0,8))
        # man_light_entry=Entry(entries_frame, width=10)
        # man_light_entry.insert(0,'10')
        # man_light_entry.pack(side=LEFT)
        # man_detector_label=Label(entries_frame, padx=padx,pady=pady,bg=bg, text='Emission:')
        # man_detector_label.pack(side=LEFT, padx=(10,0))
        # man_detector_entry=Entry(entries_frame, width=10,text='0')
        # man_detector_entry.insert(0,'10')
        # man_detector_entry.pack(side=LEFT)
        
        self.timer_frame=Frame(self.dumb_frame, bg=bg, pady=2*pady)
        self.timer_frame.pack()
        self.timer_check_frame=Frame(self.timer_frame, bg=bg)
        self.timer_check_frame.pack(pady=(15,5))
        self.timer=IntVar()
        self.timer_check=Checkbutton(self.timer_check_frame, text='Use a self.timer to take spectra at set intervals at each geometry', bg=bg, pady=pady,highlightthickness=0, variable=self.timer)
        self.timer_check.pack(side=LEFT, pady=(5,15))
        self.timer_spectra_label=Label(self.timer_frame,padx=padx,pady=pady,bg=bg,text='Total duration (min):')
        self.timer_spectra_label.pack(side=LEFT, padx=padx,pady=(0,8))
        self.timer_spectra_entry=Entry(self.timer_frame, width=10)
        self.timer_spectra_entry.pack(side=LEFT)
        self.timer_interval_label=Label(self.timer_frame, padx=padx,pady=pady,bg=bg, text='Interval (min):')
        self.timer_interval_label.pack(side=LEFT, padx=(10,0))
        self.timer_interval_entry=Entry(self.timer_frame, width=10,text='0')
    # self.timer_interval_entry.insert(0,'-1')
        self.timer_interval_entry.pack(side=LEFT, padx=(0,20))
        
        # check_frame=Frame(man_frame, bg=bg)
        # check_frame.pack()
        # process=IntVar()
        # process_check=Checkbutton(check_frame, text='Process data', bg=bg, pady=pady,highlightthickness=0)
        # process_check.pack(side=LEFT, pady=(5,15))
        # 
        # plot=IntVar()
        # plot_check=Checkbutton(check_frame, text='Plot spectrum', bg=bg, pady=pady,highlightthickness=0)
        # plot_check.pack(side=LEFT, pady=(5,15))
    
        #   move_button=Button(man_frame, text='Move', padx=padx, pady=pady, width=int(button_width*1.6),bg='light gray', command=go)
        # move_button.pack(padx=padx,pady=pady, side=LEFT)
        # spectrum_button=Button(man_frame, text='Collect data', padx=padx, pady=pady, width=int(button_width*1.6), bg='light gray', command=take_spectrum)
        # spectrum_button.pack(padx=padx,pady=pady, side=LEFT)
        
    
    
    
        self.process_frame=Frame(self.notebook, bg=bg, pady=2*pady)
        self.process_frame.pack()
        self.input_frame=Frame(self.process_frame, bg=bg)
        self.input_frame.pack()
        self.input_dir_label=Label(self.process_frame,padx=padx,pady=pady,bg=bg,text='Input directory:')
        self.input_dir_label.pack(padx=padx,pady=pady)
        self.input_dir_var = StringVar()
        self.input_dir_var.trace('w', self.validate_input_dir)
        self.input_dir_entry=Entry(self.process_frame, width=50, textvariable=self.input_dir_var)
        self.input_dir_entry.insert(0, input_dir)
        self.input_dir_entry.pack()
        
        self.output_frame=Frame(self.process_frame, bg=bg)
        self.output_frame.pack()
        self.output_dir_label=Label(self.process_frame,padx=padx,pady=pady,bg=bg,text='Output directory:')
        self.output_dir_label.pack(padx=padx,pady=pady)
        self.output_dir_entry=Entry(self.process_frame, width=50)
        self.output_dir_entry.insert(0, output_dir)
        self.output_dir_entry.pack()
        
        self.output_file_frame=Frame(self.process_frame, bg=bg)
        self.output_file_frame.pack()
        self.output_file_label=Label(self.process_frame,padx=padx,pady=pady,bg=bg,text='Output file name:')
        self.output_file_label.pack(padx=padx,pady=pady)
        self.output_file_entry=Entry(self.process_frame, width=50)
        self.output_file_entry.pack()
        
        
        self.process_check_frame=Frame(self.process_frame, bg=bg)
        self.process_check_frame.pack(pady=(15,5))
        self.process_save_dir=IntVar()
        self.process_save_dir_check=Checkbutton(self.process_check_frame, text='Save file configuration', bg=bg, pady=pady,highlightthickness=0, variable=self.process_save_dir)
        self.process_save_dir_check.pack(side=LEFT, pady=(5,15))
        self.process_save_dir_check.select()
        self.process_plot=IntVar()
        self.process_plot_check=Checkbutton(self.process_check_frame, text='Plot spectra', bg=bg, pady=pady,highlightthickness=0)
        self.process_plot_check.pack(side=LEFT, pady=(5,15))
        
        self.process_button=Button(self.process_frame, text='Process', padx=padx, pady=pady, width=int(button_width*1.6),bg='light gray', command=self.process_cmd)
        self.process_button.pack()
        
        #********************** Plot frame ******************************
        
        self.plot_frame=Frame(self.notebook, bg=bg, pady=2*pady)
        #self.process_frame.pack()
        self.plot_frame.pack()
        self.plot_input_frame=Frame(self.plot_frame, bg=bg)
        self.plot_input_frame.pack()
        self.plot_input_dir_label=Label(self.plot_frame,padx=padx,pady=pady,bg=bg,text='Path to .tsv file:')
        self.plot_input_dir_label.pack(padx=padx,pady=pady)
        self.plot_input_dir_entry=Entry(self.plot_frame, width=50)
        self.plot_input_dir_entry.insert(0, input_dir)
        self.plot_input_dir_entry.pack()
        
        self.plot_title_frame=Frame(self.plot_frame, bg=bg)
        self.plot_title_frame.pack()
        self.plot_title_label=Label(self.plot_frame,padx=padx,pady=pady,bg=bg,text='Plot title:')
        self.plot_title_label.pack(padx=padx,pady=pady)
        self.plot_title_entry=Entry(self.plot_frame, width=50)
        self.plot_title_entry.insert(0, output_dir)
        self.plot_title_entry.pack()
        
        self.plot_caption_frame=Frame(self.plot_frame, bg=bg)
        self.plot_caption_frame.pack()
        self.plot_caption_label=Label(self.plot_frame,padx=padx,pady=pady,bg=bg,text='Plot caption:')
        self.plot_caption_label.pack(padx=padx,pady=pady)
        self.plot_caption_entry=Entry(self.plot_frame, width=50)
        self.plot_caption_entry.insert(0, output_dir)
        self.plot_caption_entry.pack()
        
        
        # pr_check_frame=Frame(self.process_frame, bg=bg)
        # self.process_check_frame.pack(pady=(15,5))
        # self.process_save_dir=IntVar()
        # self.process_save_dir_check=Checkbutton(self.process_check_frame, text='Save file configuration', bg=bg, pady=pady,highlightthickness=0, variable=self.process_save_dir)
        # self.process_save_dir_check.pack(side=LEFT, pady=(5,15))
        # self.process_save_dir_check.select()
        # self.process_plot=IntVar()
        # self.process_plot_check=Checkbutton(self.process_check_frame, text='Plot spectra', bg=bg, pady=pady,highlightthickness=0)
        # self.process_plot_check.pack(side=LEFT, pady=(5,15))
        
        self.plot_button=Button(self.plot_frame, text='Plot', padx=padx, pady=pady, width=int(button_width*1.6),bg='light gray', command=self.plot)
        self.plot_button.pack()
    
        #************************Console********************************
        self.console_frame=Frame(self.notebook, bg=bg)
        self.console_frame.pack(fill=BOTH, expand=True)
        self.text_frame=Frame(self.console_frame)
        self.scrollbar = Scrollbar(self.text_frame)
        self.notebook_width=self.notebook.winfo_width()
        self.notebook_height=self.notebook.winfo_width()
        self.textbox = Text(self.text_frame, width=self.notebook_width)
        self.scrollbar.pack(side=RIGHT, fill=Y)
    
        self.scrollbar.config(command=self.textbox.yview)
        self.textbox.configure(yscrollcommand=self.scrollbar.set)
        self.console_entry=Entry(self.console_frame, width=self.notebook_width)
        self.console_entry.bind("<Return>",self.run)
        self.console_entry.bind('<Up>',self.run)
        self.console_entry.bind('<Down>',self.run)
        self.console_entry.pack(fill=BOTH, side=BOTTOM)
        self.text_frame.pack(fill=BOTH, expand=True)
        self.textbox.pack(fill=BOTH,expand=True)
        self.console_entry.focus()
    
        self.notebook.add(self.auto_frame, text='Spectrometer control')
        self.notebook.add(self.dumb_frame, text='self.timer control')
        self.notebook.add(self.process_frame, text='Data processing')
        self.notebook.add(self.plot_frame, text='Plot')
        self.notebook.add(self.console_frame, text='Console')
        #self.notebook.add(val_frame, text='Validation tools')
        #checkbox: Iterate through a range of geometries
        #checkbox: Choose a single geometry
        #checkbox: Take one spectrum
        #checkbox: Use a self.timer to collect a series of spectra
        #self.timer interval: 
        #Number of spectra to collect:
        self.notebook.pack(fill=BOTH, expand=True)
        self.master.mainloop()
        
    

        self.view.join()
    
    def go(self):    
        if not self.auto.get():
            self.take_spectrum()
            # print('hi?')
            # for i in range(3):
            #     time.sleep(1)
            #     print(i)
            # if waiter != None:
            #     print('trying to wait...')
            #     waiter.wait(3)
        else:
            incidence={'start':-1,'end':-1,'increment':-1}
            emission={'start':-1,'end':-1,'increment':-1}
            try:
                incidence['start']=int(light_start_entry.get())
                incidence['end']=int(light_end_entry.get())
                incidence['increment']=int(light_increment_entry.get())
                
                emission['start']=int(detector_start_entry.get())
                emission['end']=int(detector_end_entry.get())
                emission['increment']=int(detector_increment_entry.get())
            except:
                print('Invalid input')
                return
            self.model.go(incidence, emission)
        
            if self.spec_save_config.get():
                file=open('spec_save','w')
                file.write(self.spec_save_path_entry.get()+'\n')
                file.write(self.spec_basename_entry.get()+'\n')
                file.write(self.spec_startnum_entry.get()+'\n')
    def wr(self):
        self.model.white_reference()
        info_string='UNVERIFIED:\n White reference taken at '+str(datetime.datetime.now())+'\n'
        with open(self.log_filename,'a') as log:
            log.write(info_string)
        self.textbox.insert(END,info_string)
    def opt(self):
        self.model.opt()
        self.model.white_reference()
        info_string='UNVERIFIED:\n Instrument optimized at '+str(datetime.datetime.now())+'\n'
        with open(self.log_filename,'a') as log:
            log.write(info_string)
        self.textbox.insert(END, info_string)
    
    def test(self,arg=False):
        print(arg)
        
            
    def take_spectrum(self, force=False):
        global spec_save_path
        global spec_basename
        global g_spec_num
        
        incidence=self.man_incidence_entry.get()
        emission=self.man_emission_entry.get()
        
            
        if force==False: 
            if self.man_incidence_entry.get()=='' or self.man_emission_entry.get()=='':
                
                title='Error: Invalid Input'
                buttons={
                    'yes':{
                        self.take_spectrum:[True],
                        self.test:[True]
                    },
                    'no':{}
                }
                label='Error: Invalid emission and/or incidence angle.\nDo you want to continue?'
                dialog=Dialog(self,title,label,buttons)
                return
                
        new_spec_save_dir=self.spec_save_path_entry.get()
        new_spec_basename=self.spec_basename_entry.get()
        if new_spec_save_dir=='' or new_spec_basename=='':
            dialog=ErrorDialog(self,'Error: Please enter a save directory and a basename')
            return
        try:
            new_spec_num=int(self.spec_startnum_entry.get())
        except:
            dialog=ErrorDialog(self,'Error: Invalid spectrum number')
            return

        if new_spec_save_dir != spec_save_path or new_spec_basename != spec_basename or g_spec_num==None or new_spec_num!=g_spec_num:
            self.set_save_config()
            time.sleep(1)


        startnum_str=str(self.spec_startnum_entry.get())
        while len(startnum_str)<3:
            startnum_str='0'+startnum_str
            
        self.model.take_spectrum(incidence,emission)
        
        filename=self.spec_save_path_entry.get()+'\\'+self.spec_basename_entry.get()+'.'+startnum_str
        self.listener.expected_data_files.append(filename)
        
        info_string='UNVERIFIED:\n Spectrum saved at '+str(datetime.datetime.now())+ '\n\ti='+self.man_incidence_entry.get()+'\n\te='+self.man_emission_entry.get()+'\n\tfilename='+filename+'\n\tNotes: '+self.man_notes_entry.get()+'\n'
        self.textbox.insert(END,info_string)
        #self.increment_num()
        with open(self.log_filename,'a') as log:
            log.write(info_string)
        
        self.man_incidence_entry.delete(0,'end')
        self.man_emission_entry.delete(0,'end')
        self.man_notes_entry.delete(0,'end')
        
        if self.spec_save_config.get():
            file=open(self.config_loc+'/spec_save','w')
            file.write(self.spec_save_path_entry.get()+'\n')
            file.write(self.spec_basename_entry.get()+'\n')
            file.write(self.spec_startnum_entry.get()+'\n')

            self.input_dir_entry.delete(0,'end')
            self.input_dir_entry.insert(0,self.spec_save_path_entry.get())
        
        wait_dialog=WaitDialog(self)
        return wait_dialog
        
    def set_save_config(self):
        global g_spec_num
        global spec_save_path
        global spec_basename
        spec_save_path=self.spec_save_path_entry.get()
        spec_basename = self.spec_basename_entry.get()
        spec_num=self.spec_startnum_entry.get()
        g_spec_num=int(spec_num)
        while len(spec_num)<3:
            spec_num='0'+spec_num
        self.model.set_save_path(spec_save_path, spec_basename, spec_num)
            
    def increment_num(self):
        try:
            num=int(self.spec_startnum_entry.get())+1
            self.spec_startnum_entry.delete(0,'end')
            self.spec_startnum_entry.insert(0,str(num))
        except:
            return
    
    def move(self):
        try:
            incidence=int(man_light_entry.get())
            emission=int(man_detector_entry.get())
        except:
            print('Invalid input')
            return
        if incidence<0 or incidence>90 or emission<0 or emission>90:
            print('Invalid input')
            return
        self.model.move_light(i)
        self.model.move_detector(e)
        
    def process_cmd(self):
        output_file=self.output_file_entry.get()
        if '.' not in output_file: output_file=output_file+'.tsv'
        try:
            self.model.process(self.input_dir_entry.get(), self.output_dir_entry.get(), output_file)
        except:
            print("error:", sys.exc_info()[0])
            dialog=ErrorDialog(self)
            self.model.process(self.input_dir_entry.get(), self.output_dir_entry.get(), output_file)
        
        if self.process_save_dir.get():
            file=open(self.config_loc+'/process_directories','w')
            file.write(self.input_dir_entry.get()+'\n')
            file.write(self.output_dir_entry.get()+'\n')
            file.write(output_file+'\n')
            self.plot_input_dir_entry.delete(0,'end')
            plot_file=self.output_dir_entry.get()+'\\'+output_file
            self.plot_input_dir_entry.insert(0,plot_file)
            
    def plot(self):
        filename=self.plot_input_dir_entry.get()
        filename=filename.replace('C:\\Kathleen','/run/user/1000/gvfs/smb-share:server=melissa,share=kathleen/')
        filename=filename.replace('\\','/')
        title=self.plot_title_entry.get()
        caption=self.plot_caption_entry.get()
        try:
            self.plotter.plot_spectra(title,filename,caption)
        except:
            dialog=Dialog(self, 'Plotting Error', 'Error: Plotting failed. Does file exist?',{'ok':{}})
        #self.plotter.plot_spectra(title,filename,caption)
    
    
    def auto_cycle_check(self):
        if self.auto.get():
            light_end_label.config(fg='black')
            detector_end_label.config(fg='black')
            light_increment_label.config(fg='black')
            detector_increment_label.config(fg='black')
            light_end_entry.config(bd=3)
            detector_end_entry.config(bd=3)
            light_increment_entry.config(bd=3)
            detector_increment_entry.config(bd=3)
        else:
            light_end_label.config(fg='lightgray')
            detector_end_label.config(fg='lightgray')
            light_increment_label.config(fg='lightgray')
            detector_increment_label.config(fg='lightgray')
            light_end_entry.config(bd=1)
            detector_end_entry.config(bd=1)
            light_increment_entry.config(bd=1)
            detector_increment_entry.config(bd=1)
        
    def run(self, keypress_event):
        global user_cmds
        global user_cmd_index
        if keypress_event.keycode==36:
            cmd=self.console_entry.get()
            if cmd !='':
                user_cmds.insert(0,cmd)
                user_cmd_index=-1
                self.textbox.insert(END,'>>> '+cmd+'\n')
                self.console_entry.delete(0,'end')
                
                params=cmd.split(' ')
                if params[0].lower()=='process':
                    try:
                        if params[1]=='--save_config':
                            self.process_save_dir_check.select()
                            params.pop(1)
                        self.input_dir_entry.delete(0,'end')
                        self.input_dir_entry.insert(0,params[1])
                        self.output_dir_entry.delete(0,'end')
                        self.output_dir_entry.insert(0,params[2]) 
                        self.output_file_entry.delete(0,'end')
                        self.output_file_entry.insert(0,params[3])
                        process_cmd()
                    except:
                        self.textbox.insert(END,'Error: Failed to process file.')
                elif params[0].lower()=='wr':
                    self.wr()
                elif params[0].lower()=='opt':
                    self.opt()
                elif params[0].lower()=='log':
                    logstring=''
                    for word in params:
                        logstring=logstring+word+' '
                    logstring=logstring+'\n'
                    with open('log.txt','a') as log:
                        log.write(logstring)
                    
            
        elif keypress_event.keycode==111:
            if len(user_cmds)>user_cmd_index+1 and len(user_cmds)>0:
                user_cmd_index=user_cmd_index+1
                last=user_cmds[user_cmd_index]
                self.console_entry.delete(0,'end')
                self.console_entry.insert(0,last)

        elif keypress_event.keycode==116:
            if user_cmd_index>0:
                user_cmd_index=user_cmd_index-1
                next=user_cmds[user_cmd_index]
                self.console_entry.delete(0,'end')
                self.console_entry.insert(0,next)
    
    def validate_basename(self,*args):
        basename=limit_len(self.spec_basename_entry.get())
        basename=rm_reserved_chars(basename)
        self.spec_basename_entry.set(basename)
    
    def validate_startnum(self,*args):
        num=spec_startnum.get()
        valid=validate_int_input(num,999,0)
        if not valid:
            spec_startnum.set('')
        else:
            while len(num)<3:
                num=0+num
        self.spec_startnum_entry.detel(0,'end')
        self.spec_startnum_entry.insert(0,num)
    
    def validate_input_dir(self,*args):
        input_dir=rm_reserved_chars(self.input_dir_entry.get())
        self.input_dir_entry.delete(0,'end')
        self.input_dir_entry.insert(0,input_dir)
        
    def validate_output_dir():
        output_dir=rm_reserved_chars(self.output_dir_entry.get())
        self.output_dir_entry.delete(0,'end')
        self.output_dir_entry.insert(0,output_dir)


    
class Dialog:
    def __init__(self, controller, title, label, buttons):
        self.controller=controller
        self.top = tk.Toplevel(controller.master, bg='white')
        self.top.wm_title(title)
        #self.buttons=buttons

        
        self.button_width=20
        self.bg='white'
        
        self.label_frame=Frame(self.top, bg=self.bg)
        self.label_frame.pack(side=TOP)
        self.label = tk.Label(self.label_frame, text=label, bg=self.bg)
        self.label.pack(pady=(10,10), padx=(10,10))
        

        self.buttons=buttons
        self.set_buttons(buttons)



            
    def set_label_text(self, newlabel):
        self.label.config(text=newlabel)
        
    def set_buttons(self, buttons):
        self.buttons=buttons
        try:
            self.button_frame.destroy()
        except:
            pass
        self.button_frame=Frame(self.top, bg=self.bg)
        self.button_frame.pack(side=BOTTOM)

        if 'ok' in buttons:
            self.ok_button = Button(self.button_frame, text='OK', command=self.ok, width=self.button_width)
            self.ok_button.pack(side=LEFT, padx=(10,10), pady=(10,10))
        if 'yes' in buttons:
            self.yes_button=Button(self.button_frame, text='Yes', bg='light gray', command=self.yes, width=self.button_width)
            self.yes_button.pack(side=LEFT, padx=(10,10), pady=(10,10))
        if 'no' in buttons:
            self.no_button=Button(self.button_frame, text='No',command=self.no, width=self.button_width)
            self.no_button.pack(side=LEFT, padx=(10,10), pady=(10,10))
        if 'cancel' in buttons:
            self.cancel_button=Button(self.button_frame, text='Cancel',command=self.cancel, width=self.button_width)
            self.cancel_button.pack(side=LEFT, padx=(10,10), pady=(10,10))
        
    def ok(self):
        dict=self.buttons['ok']
        self.top.destroy()
        for func in dict:
            arg=dict[func][0]
            func(arg)
        
    def yes(self):
        dict=self.buttons['yes']
        self.top.destroy()
        for func in dict:
            arg=dict[func][0]
            func(arg)
        
    def no(self):
        dict=self.buttons['no']
        self.top.destroy()
        for func in dict:
            arg=dict[func][0]
            func(arg)
            
    def cancel(self):
        dict=self.buttons['cancel']
        self.top.destroy()
        for func in dict:
            arg=dict[func][0]
            func(arg)

# class CustomButton(Button):
#     def __init__(text, func_dict):
#         
#         super(frame, text=text, command=self.command, width=width)
#         
#     def command(self, func_dict):
        
class WaitDialog(Dialog):
    def __init__(self, controller, title='Working...', label='Working...', buttons={'cancel':{}}, timeout=-1):
        t0=time.clock()
        t=time.clock()

        super().__init__(controller, title, label,buttons)
        
        self.interrupted=False
        
        self.frame=Frame(self.top, bg=self.bg, width=200, height=30)
        self.frame.pack()
  
        style=ttk.Style()
        style.configure('Horizontal.TProgressbar', background='white')
        self.pbar = ttk.Progressbar(self.frame, mode='indeterminate', name='pb2', style='Horizontal.TProgressbar' )
        self.pbar.start([10])
        self.pbar.pack(padx=(10,10),pady=(10,10))
        
        thread = Thread(target = self.wait, args = (10, ))
        thread.start()
        
    def wait(self, timeout):
        old_files=list(self.controller.listener.saved_files)
        timeout=15
        for i in range(timeout):
            if self.controller.listener.failed:
                self.controller.listener.failed=False
                self.interrupt('Error: Failed to save file.\nAre you sure the spectrometer is connected?')
                return
            elif self.controller.listener.noconfig==True:
                self.controller.listener.noconfig=False
                self.controller.set_save_config()
                self.controller.model.take_spectrum(self.controller.man_incidence_entry.get(), self.controller.man_emission_entry.get())
                
            time.sleep(1)
            current_files=self.controller.listener.saved_files
            
            if current_files==old_files:
                print('waiting')
            else:
                for file in current_files:
                    if file not in old_files:
                        global g_spec_num
                        g_spec_num+=1
                        self.controller.spec_startnum_entry.delete(0,'end')
                        spec_num_string=str(g_spec_num)
                        while len(spec_num_string)<3:
                            spec_num_string='0'+spec_num_string
                        self.controller.spec_startnum_entry.insert(0,spec_num_string)
                        self.interrupt('Success!')
                        return
        self.timeout()
        # t0=time.clock()
        # if timeout>0:
        #     t=time.clock()
        #     while t-t0<timeout:
        #         time.sleep(1)
        #         t=time.clock()
        #     self.timeout()
    def interrupt(self,label):
        self.interrupted=True
        self.set_label_text(label)
        self.pbar.stop()
        self.set_buttons({'ok':{}})
            

                
    def timeout(self):
        self.set_label_text('Error: Operation timed out')
        self.pbar.stop()
        self.set_buttons({'ok':{}})
        
    def finish():
        self.top.destroy()
                
    def send(self):
        global username
        username = self.myEntryBox.get()
        self.top.destroy()
        
class ErrorDialog(Dialog):
    def __init__(self, controller, title='Error', label='Error!', buttons={'ok':{}}):

        super().__init__(controller, title, label,buttons)

        
def rm_reserved_chars(input):
    return input.strip('&').strip('+').strip('=')

def limit_len(input, max):
    return input[:max]
    
def validate_int_input(input, max, min):
    try:
        input=int(input)
    except:
        return False
    if input>max: return False
    if input<min: return False
    
    return True

class Listener(threading.Thread):
    def __init__(self, read_command_loc, test=False):
        threading.Thread.__init__(self)
        self.read_command_loc=read_command_loc
        self.saved_files=[]
        self.expected_data_files=[]
        self.controller=None
        
        self.failed=False
        self.noconfig=False
        
    def set_controller(self,controller):
        self.controller=controller
    
    def run(self):
        files0=os.listdir(self.read_command_loc)
        while True:
            files=os.listdir(self.read_command_loc)
            if files==files0:
                pass
            else:
                for file in files:
                    if file not in files0:
                        cmd, params=filename_to_cmd(file)
                        #os.remove(read_command_loc+'/'+file)
                        if 'savedfile' in cmd:

                            if params[0] in self.expected_data_files:
                                self.saved_files.append(params[0])
                            else:
                                print("I wasn't expecting that!")
                                dialog=ErrorDialog(self.controller, label="Warning! I wasn't expecting that! The spectrometer compy was happy to save this file but I don't think it should be here The\n\n"+params[0])
                        elif 'failedtosavefile' in cmd:
                            self.failed=True
                            pass
                            #dialog=ErrorDialog(self.controller, label='Error: Processing failed')
                        elif 'processerror' in cmd:
                            dialog=ErrorDialog(self.controller, label='Error: Processing failed.')
                        elif 'unexpectedfile' in cmd:
                            #This is hacky and bad. If you switch save directories and the new one has files that shouldn't be there but have the same names as ones in your old directory that should be there then you will lose.
                            print('could one of these match?')
                            ignore=False
                            for file in self.expected_data_files:
                                end=file.split('\\')[-1]
                                if end==params[0]:
                                    print('I think this file is probably fine: '+params[0])
                                    ignore=True
                                    
                            if not ignore:
                                print('unexpected file: '+params[0])
                                dialog=ErrorDialog(self.controller, label='Warning! Unexpected file in data directory.\nDoes this belong here? Make sure numbers match\nbetween computers before continuing\n\n'+params[0])
                        elif 'saveconfigerror' in cmd:
                            self.failed=True
                            #dialog=ErrorDialog(self.controller, label='Error: Failed to set save configuration.\nAre you sure the spectrometer is connected?')
                        elif 'noconfig' in cmd:
                            print('GOT NO CONFIG')
                            self.noconfig=True

                        else:
                            print('unexpected file: '+file)
                #This line always prints twice if it's uncommented, I'm not sure why.
                #print('forward!')
                
                files0=files
                            
            time.sleep(1)
            
    def find_file(path):
        print(path)
        i=0
        found=False
        while i<10 and found==False:
            if path in self.saved_files:
                found=True
            i=i+1
        return found
    
        
        

def filename_to_cmd(filename):
    cmd=filename.split('&')[0]
    params=filename.split('&')[1:]
    for i, param in enumerate(params):
        params[i]=param.replace('+','\\').replace('=',':')
    return cmd, params


if __name__=='__main__':
    main()