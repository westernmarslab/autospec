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
#import pygame
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
import sys
import platform

if dev:
    sys.path.append('C:\\Users\\hozak\\Python\\autospectroscopy')

import robot_model
import robot_view
import plotter

#This is needed because otherwise changes won't show up until you restart the shell. Not needed if you aren't change
if dev:
    imp.reload(robot_model)
    from robot_model import Model
    imp.reload(robot_view)
    from robot_view import View
    imp.reload(plotter)
    from plotter import Plotter

def main():
    #Server and share location. Could change if spectroscopy computer changes.
    server='melissa'
    share='specshare'
    
    #Figure out where this file is hanging out and tell python to look there for modules.
    package_loc=os.path.dirname(sys.argv[0])
    sys.path.append(package_loc)
    if package_loc=='' and dev:
        package_loc='C:\\Users\\hozak\\Python\\autospectroscopy'
    
    #Figure out all of your various directory locations. These will depend on what operating system you are using.
    opsys=platform.system()
    if opsys=='Darwin': opsys='Mac' #For some reason Macs identify themselves as Darwin. I don't know why but I think this is more intuitive.
    if opsys=='Linux':
        share_loc='/run/user/1000/gvfs/smb-share:server='+server+',share='+share+'/'
        delimiter='/'
        write_command_loc=share_loc+'commands/from_control/'
        read_command_loc=share_loc+'commands/from_spec/'
        package_loc=package_loc+'/'
        config_loc=package_loc+'/'+'config/'
    elif opsys=='Windows':
        share_loc='\\\\MELISSA\\SpecShare\\'
        write_command_loc=share_loc+'commands\\from_control\\'
        read_command_loc=share_loc+'commands\\from_spec\\'
        package_loc=package_loc+'\\'
        config_loc=package_loc+'config\\'
    elif opsys=='Mac':
        mac=ErrorDialog(self, label="ahhhhh I don't know what to do on a Mac!!")
        
    #Clean out your read and write directories for commands. Prevents confusion based on past instances of the program.
    delme=os.listdir(write_command_loc)
    for file in delme:
        os.remove(write_command_loc+file)
    delme=os.listdir(read_command_loc)
    for file in delme:
        os.remove(read_command_loc+file)
    
    #Create a listener, which listens for commands, and a controller, which manages the model (which writes commands) and the view.
    listener=Listener(read_command_loc)
    control=Controller(listener, share_loc, write_command_loc, config_loc,opsys)

class Controller():
    def __init__(self, listener, share_loc, write_command_loc, config_loc, opsys):
        self.listener=listener
        self.listener.set_controller(self)
        self.listener.start()
        
        self.share_loc=share_loc
        self.write_command_loc=write_command_loc
        self.config_loc=config_loc
        self.opsys=opsys
        
        #Log your actions!
        self.log_filename='log_'+datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')+'.txt'
        with open(self.log_filename,'w+') as log:
            log.write(str(datetime.datetime.now())+'\n')
        if dev: plt.close('all')
        
        #These will get set via user input.
        self.spec_save_path=''
        self.spec_basename=''
        self.spec_num=None
        self.spec_config_count=None
        self.take_spectrum_with_bad_i_or_e=False
        self.wr_time=None
        self.opt_time=None
        
        #Tkinter notebook GUI
        self.master=Tk()
        self.notebook=ttk.Notebook(self.master)
        
        #The plotter, surprisingly, plots things.
        self.plotter=Plotter(self.master)
        
        #The view displays what the software thinks the goniometer is up to.
        self.view=View()
        self.view.start()
    
        #The model keeps track of the goniometer state and sends commands to the raspberry pi and spectrometer
        self.model=Model(self.view, self.plotter, self.write_command_loc, False, False)
        
        #Yay formatting
        bg='white'
        bd=2
        padx=3
        pady=3
        border_color='light gray'
        button_width=15
        
        self.master.configure(background = bg)
        self.master.title('Control')
    
        process_config=open(self.config_loc+'process_directories','r')
        input_dir=''
        output_dir=''
        try:
            input_dir=process_config.readline().strip('\n')
            output_dir=process_config.readline().strip('\n')
        except:
            print('invalid config')
    
        self.spec_save_config=open(self.config_loc+'spec_save','r')
        self.spec_save_path=''
        self.spec_basename=''
        spec_startnum=''
        
        try:
            self.spec_save_path=self.spec_save_config.readline().strip('\n')
            self.spec_basename=self.spec_save_config.readline().strip('\n')
            spec_startnum=self.spec_save_config.readline().strip('\n')
        except:
            print('invalid config')
        
        self.auto_frame=Frame(self.notebook, bg=bg)
    
        self.spec_save_path_label=Label(self.auto_frame,padx=padx,pady=pady,bg=bg,text='Save directory:')
        self.spec_save_path_label.pack(padx=padx,pady=(15,5))
        self.spec_save_path_entry=Entry(self.auto_frame, width=50,bd=bd)
        self.spec_save_path_entry.insert(0, self.spec_save_path)
        self.spec_save_path_entry.pack(padx=padx, pady=pady)
    
        self.spec_save_frame=Frame(self.auto_frame, bg=bg)
        self.spec_save_frame.pack()
        
        self.spec_basename_label=Label(self.spec_save_frame,pady=pady,bg=bg,text='Base name:')
        self.spec_basename_label.pack(side=LEFT,pady=(5,15),padx=(0,0))
        self.spec_basename_entry=Entry(self.spec_save_frame, width=10,bd=bd)
        self.spec_basename_entry.pack(side=LEFT,padx=(5,5), pady=pady)
        self.spec_basename_entry.insert(0,self.spec_basename)
        
        self.spec_startnum_label=Label(self.spec_save_frame,padx=padx,pady=pady,bg=bg,text='Number:')
        self.spec_startnum_label.pack(side=LEFT,pady=pady)
        self.spec_startnum_entry=Entry(self.spec_save_frame, width=10,bd=bd)
        self.spec_startnum_entry.insert(0,spec_startnum)
        self.spec_startnum_entry.pack(side=RIGHT, pady=pady)
        
        self.spec_save_config=IntVar()
        self.spec_save_config_check=Checkbutton(self.auto_frame, text='Save file configuration', bg=bg, pady=pady,highlightthickness=0, variable=self.spec_save_config)
        self.spec_save_config_check.pack(pady=(0,5))
        self.spec_save_config_check.select()
        
        self.instrument_config_frame=Frame(self.auto_frame, bg=bg)
        self.instrument_config_frame.pack(pady=(15,15))
        self.instrument_config_label=Label(self.instrument_config_frame, text='Number of spectra to average:', bg=bg)
        self.instrument_config_label.pack(side=LEFT)
        self.instrument_config_entry=Entry(self.instrument_config_frame, width=10, bd=bd)
        self.instrument_config_entry.insert(0, 5)
        self.instrument_config_entry.pack(side=LEFT)
        #self.filler_label=Label(self.instrument_config_frame,bg=bg,text='       ')
        # self.filler_label.pack(side=LEFT)
        


        
        self.manual_frame=Frame(self.auto_frame, bg=bg)
        self.manual_frame.pack()
        
        self.man_incidence_label=Label(self.manual_frame,padx=padx,pady=pady,bg=bg,text='Incidence angle:')
        self.man_incidence_label.pack(side=LEFT, padx=padx,pady=(0,8))
        self.man_incidence_entry=Entry(self.manual_frame, width=10, bd=bd)
        self.man_incidence_entry.pack(side=LEFT)
        self.man_emission_label=Label(self.manual_frame, padx=padx,pady=pady,bg=bg, text='Emission angle:')
        self.man_emission_label.pack(side=LEFT, padx=(10,0))
        self.man_emission_entry=Entry(self.manual_frame, width=10, bd=bd)
        self.man_emission_entry.pack(side=LEFT, padx=(0,20))
        
        self.man_notes_label=Label(self.auto_frame, padx=padx,pady=pady,bg=bg, text='Notes:')
        self.man_notes_label.pack()
        self.man_notes_entry=Entry(self.auto_frame, width=50, bd=bd)
        self.man_notes_entry.pack(pady=(0,15))
        
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
        
        light_start_entry=Entry(light_entries_frame,width=10, bd=bd)
        light_start_entry.pack(padx=padx,pady=pady)
        light_start_entry.insert(0,'10')
        
        light_end_entry=Entry(light_entries_frame,width=10, highlightbackground='white', bd=bd)
        light_end_entry.pack(padx=padx,pady=pady)    
        light_increment_entry=Entry(light_entries_frame,width=10,highlightbackground='white', bd=bd)
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
        detector_start_entry=Entry(detector_entries_frame,bd=bd,width=10)
        detector_start_entry.pack(padx=padx,pady=pady)
        detector_start_entry.insert(0,'0')
        
        detector_end_entry=Entry(detector_entries_frame,bd=bd,width=10,highlightbackground='white')
        detector_end_entry.pack(padx=padx,pady=pady)
        
        detector_increment_entry=Entry(detector_entries_frame,bd=bd,width=10, highlightbackground='white')
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
        # Frame for settings
        
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

        # self.instrument_config_title_frame=Frame(self.dumb_frame, bg=bg)
        # self.instrument_config_title_frame.pack(pady=pady)
        # self.instrument_config_label0=Label(self.instrument_config_title_frame, text='Instrument Configuration:                                ', bg=bg)
        # self.instrument_config_label0.pack(side=LEFT)

        
        self.automation_title_frame=Frame(self.dumb_frame, bg=bg)
        self.automation_title_frame.pack(pady=pady)
        self.automation_label0=Label(self.automation_title_frame, text='Automation:                                               ', bg=bg)
        self.automation_label0.pack(side=LEFT)
        
        
        self.auto_check_frame=Frame(self.dumb_frame, bg=bg)
        self.auto_check_frame.pack()
        self.auto=IntVar()
        self.auto_check=Checkbutton(self.auto_check_frame, text='Automatically iterate through viewing geometries', bg=bg, pady=pady,highlightthickness=0, variable=self.auto, command=self.auto_cycle_check)
        self.auto_check.pack(side=LEFT, pady=pady)
        
        self.timer_title_frame=Frame(self.dumb_frame, bg=bg)
        self.timer_title_frame.pack(pady=(10,0))
        self.timer_label0=Label(self.timer_title_frame, text='Timer:                                                   ', bg=bg)
        self.timer_label0.pack(side=LEFT)
        self.timer_frame=Frame(self.dumb_frame, bg=bg, pady=pady)
        self.timer_frame.pack()
        self.timer_check_frame=Frame(self.timer_frame, bg=bg)
        self.timer_check_frame.pack(pady=pady)
        self.timer=IntVar()
        self.timer_check=Checkbutton(self.timer_check_frame, text='Collect sets of spectra using a timer           ', bg=bg, pady=pady,highlightthickness=0, variable=self.timer)
        self.timer_check.pack(side=LEFT, pady=pady)
        
        self.timer_duration_frame=Frame(self.timer_frame, bg=bg)
        self.timer_duration_frame.pack()
        self.timer_spectra_label=Label(self.timer_duration_frame,padx=padx,pady=pady,bg=bg,text='Total duration (min):')
        self.timer_spectra_label.pack(side=LEFT, padx=padx,pady=(0,8))
        self.timer_spectra_entry=Entry(self.timer_duration_frame, bd=1,width=10)
        self.timer_spectra_entry.pack(side=LEFT)
        self.filler_label=Label(self.timer_duration_frame,bg=bg,text='              ')
        self.filler_label.pack(side=LEFT)
        
        self.timer_interval_frame=Frame(self.timer_frame, bg=bg)
        self.timer_interval_frame.pack()
        self.timer_interval_label=Label(self.timer_interval_frame, padx=padx,pady=pady,bg=bg, text='Interval (min):')
        self.timer_interval_label.pack(side=LEFT, padx=(10,0))
        self.timer_interval_entry=Entry(self.timer_interval_frame,bd=bd,width=10,text='0')
    # self.timer_interval_entry.insert(0,'-1')
        self.timer_interval_entry.pack(side=LEFT, padx=(0,20))
        self.filler_label=Label(self.timer_interval_frame,bg=bg,text='                   ')
        self.filler_label.pack(side=LEFT)
        
        self.failsafe_title_frame=Frame(self.dumb_frame, bg=bg)
        self.failsafe_title_frame.pack(pady=(10,0))
        self.failsafe_label0=Label(self.failsafe_title_frame, text='Failsafes:                                              ', bg=bg)
        self.failsafe_label0.pack(side=LEFT)
        self.failsafe_frame=Frame(self.dumb_frame, bg=bg, pady=pady)
        self.failsafe_frame.pack(pady=pady)

        
        self.wrfailsafe=IntVar()
        self.wrfailsafe_check=Checkbutton(self.failsafe_frame, text='Prompt if no white reference has been taken.    ', bg=bg, pady=pady,highlightthickness=0, variable=self.wrfailsafe)
        self.wrfailsafe_check.pack()#side=LEFT, pady=pady)
        #self.wrfailsafe_check.select()
        
        self.wr_timeout_frame=Frame(self.failsafe_frame, bg=bg)
        self.wr_timeout_frame.pack(pady=(0,10))
        self.wr_timeout_label=Label(self.wr_timeout_frame, text='Timeout (s):', bg=bg)
        self.wr_timeout_label.pack(side=LEFT, padx=(10,0))
        self.wr_timeout_entry=Entry(self.wr_timeout_frame, bd=bd,width=10)
        self.wr_timeout_entry.pack(side=LEFT, padx=(0,20))
        self.wr_timeout_entry.insert(0,'120')
        self.filler_label=Label(self.wr_timeout_frame,bg=bg,text='              ')
        self.filler_label.pack(side=LEFT)
        
        
        self.optfailsafe=IntVar()
        self.optfailsafe_check=Checkbutton(self.failsafe_frame, text='Prompt if the instrument has not been optimized.', bg=bg, pady=pady,highlightthickness=0, variable=self.optfailsafe)
        self.optfailsafe_check.pack()#side=LEFT, pady=pady)
       # self.optfailsafe_check.select()
        
        self.opt_timeout_frame=Frame(self.failsafe_frame, bg=bg)
        self.opt_timeout_frame.pack()
        self.opt_timeout_label=Label(self.opt_timeout_frame, text='Timeout (s):', bg=bg)
        self.opt_timeout_label.pack(side=LEFT, padx=(10,0))
        self.opt_timeout_entry=Entry(self.opt_timeout_frame,bd=bd, width=10)
        self.opt_timeout_entry.pack(side=LEFT, padx=(0,20))
        self.opt_timeout_entry.insert(0,'240')
        self.filler_label=Label(self.opt_timeout_frame,bg=bg,text='              ')
        self.filler_label.pack(side=LEFT)
        
        self.anglesfailsafe=IntVar()
        self.anglesfailsafe_check=Checkbutton(self.failsafe_frame, text='Check validity of emission and incidence angles.', bg=bg, pady=pady,highlightthickness=0, variable=self.anglesfailsafe)
        self.anglesfailsafe_check.pack(pady=(6,5))#side=LEFT, pady=pady)
       # self.anglesfailsafe_check.select()
        
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
        self.input_dir_entry=Entry(self.process_frame, width=50,bd=bd, textvariable=self.input_dir_var)
        self.input_dir_entry.insert(0, input_dir)
        self.input_dir_entry.pack()
        
        self.output_frame=Frame(self.process_frame, bg=bg)
        self.output_frame.pack()
        self.output_dir_label=Label(self.process_frame,padx=padx,pady=pady,bg=bg,text='Output directory:')
        self.output_dir_label.pack(padx=padx,pady=pady)
        self.output_dir_entry=Entry(self.process_frame, width=50,bd=bd)
        self.output_dir_entry.insert(0, output_dir)
        self.output_dir_entry.pack()
        
        self.output_file_frame=Frame(self.process_frame, bg=bg)
        self.output_file_frame.pack()
        self.output_file_label=Label(self.process_frame,padx=padx,pady=pady,bg=bg,text='Output file name:')
        self.output_file_label.pack(padx=padx,pady=pady)
        self.output_file_entry=Entry(self.process_frame, width=50,bd=bd)
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
        self.plot_input_dir_entry=Entry(self.plot_frame, width=50,bd=bd)
        self.plot_input_dir_entry.insert(0, input_dir)
        self.plot_input_dir_entry.pack()
        
        self.plot_title_frame=Frame(self.plot_frame, bg=bg)
        self.plot_title_frame.pack()
        self.plot_title_label=Label(self.plot_frame,padx=padx,pady=pady,bg=bg,text='Plot title:')
        self.plot_title_label.pack(padx=padx,pady=pady)
        self.plot_title_entry=Entry(self.plot_frame, width=50,bd=bd)
        self.plot_title_entry.pack()
        
        self.plot_caption_frame=Frame(self.plot_frame, bg=bg)
        self.plot_caption_frame.pack()
        self.plot_caption_label=Label(self.plot_frame,padx=padx,pady=pady,bg=bg,text='Plot caption:')
        self.plot_caption_label.pack(padx=padx,pady=pady)
        self.plot_caption_entry=Entry(self.plot_frame, width=50,bd=bd)
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
        self.console_entry=Entry(self.console_frame, width=self.notebook_width,bd=bd)
        self.console_entry.bind("<Return>",self.run)
        self.console_entry.bind('<Up>',self.run)
        self.console_entry.bind('<Down>',self.run)
        self.console_entry.pack(fill=BOTH, side=BOTTOM)
        self.text_frame.pack(fill=BOTH, expand=True)
        self.textbox.pack(fill=BOTH,expand=True)
        self.console_entry.focus()
    
        self.notebook.add(self.auto_frame, text='Spectrometer control')
        self.notebook.add(self.dumb_frame, text='Settings')
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
    def wr(self, opt_check=True):
        

        if opt_check and self.optfailsafe.get():
            label=''
            now=int(time.time())
            try:
                opt_limit=int(float(self.opt_timeout_entry.get()))
            except:
                opt_limit=sys.maxsize
                
            if self.opt_time==None:
                label+='The instrument has not been optimized.\n'
            elif now-self.opt_time>opt_limit: 
                minutes=str(int((now-self.opt_time)/60))
                seconds=str((now-self.opt_time)%60)
                if int(minutes)>0:
                    label+='The instrument has not been optimized for '+minutes+' minutes '+seconds+' seconds.\n'
                else: label+='The instrument has not been optimized for '+seconds+' seconds.\n'
                
            if label !='':
                title='Warning!'
                buttons={
                    'yes':{
                        self.wr:[False],
                        self.test:[True]
                    },
                    'no':{}
                }
                label='Warning!\n'+label
                label+='Do you want to continue?'
                dialog=Dialog(self,title,label,buttons)
                return
                    
        try:
            print('in try')
            new_spec_config_count=int(self.instrument_config_entry.get())
            print('went fine')
            print(self.instrument_config_entry.get())
            print(new_spec_config_count)
            if new_spec_config_count<1 or new_spec_config_count>32767:
                raise(Exception)
        except:
            dialog=ErrorDialog(self,label='Error: Invalid number of spectra to average.\nEnter a value from 1 to 32767')
            return 
        if self.spec_config_count==None or str(new_spec_config_count) !=str(self.spec_config_count):
            self.configure_instrument()
            
        self.model.white_reference()
        self.wr_time=int(time.time())
        
        datestring=''
        datestringlist=str(datetime.datetime.now()).split('.')[:-1]
        for d in datestringlist:
            datestring=datestring+d
        
        info_string='UNVERIFIED:\n White reference taken at '+datestring+'\n'
        with open(self.log_filename,'a') as log:
            log.write(info_string)
        self.textbox.insert(END,info_string)
    def opt(self):
        self.model.opt()
        self.opt_time=int(time.time())
        #self.model.white_reference()
        datestring=''
        datestringlist=str(datetime.datetime.now()).split('.')[:-1]
        for d in datestringlist:
            datestring=datestring+d
        
        info_string='UNVERIFIED:\n Instrument optimized at '+datestring+'\n'
        with open(self.log_filename,'a') as log:
            log.write(info_string)
        self.textbox.insert(END, info_string)
    
    def test(self,arg=False):
        print(arg)
        
            
    def take_spectrum(self, input_check=True, opt_wr_check=True):

        if opt_wr_check:
            try:
                wr_limit=int(float(self.wr_timeout_entry.get()))
            except:
                wr_limit=sys.maxsize
            try:
                opt_limit=int(float(self.opt_timeout_entry.get()))
            except:
                opt_limit=sys.maxsize
                
            label=''
            if self.optfailsafe.get():
                if self.opt_time==None:
                    label+='The instrument has not been optimized.\n'
                elif now-self.opt_time>opt_limit: 
                    minutes=str(int((now-self.opt_time)/60))
                    seconds=str((now-self.opt_time)%60)
                    if int(minutes)>0:
                        label+='The instrument has not been optimized for '+minutes+' minutes '+seconds+' seconds.\n'
                    else: label+='The instrument has not been optimized for '+seconds+' seconds.\n'
            if self.wrfailsafe.get():
                if self.wr_time==None:
                    label+='No white reference has been taken.\n'
                elif now-self.wr_time>wr_limit: 
                    minutes=str(int((now-self.wr_time)/60))
                    seconds=str((now-self.wr_time)%60)
                    if int(minutes)>0:
                        label+=' No white reference has been taken for '+minutes+' minutes '+seconds+' seconds.\n'
                    else: label+=' No white reference has been taken for '+seconds+' seconds.\n'

            if label !='':
                title='Warning!'
                buttons={
                    'yes':{
                        self.take_spectrum:[input_check,False],
                        self.test:[True]
                    },
                    'no':{}
                }
                label='Warning!\n'+label
                label+='Do you want to continue?'
                dialog=Dialog(self,title,label,buttons)
                return

        incidence=self.man_incidence_entry.get()
        emission=self.man_emission_entry.get()
        
            
        if input_check and self.anglesfailsafe.get(): 
            if self.man_incidence_entry.get()=='' or self.man_emission_entry.get()=='':
                
                title='Error: Invalid Input'
                buttons={
                    'yes':{
                        self.take_spectrum:[False,opt_wr_check],
                        self.test:[True]
                    },
                    'no':{}
                }
                label='Error: Invalid emission and/or incidence angle.\nDo you want to continue?'
                dialog=Dialog(self,title,label,buttons)
                return
                
        new_spec_save_dir=self.spec_save_path_entry.get()
        new_spec_basename=self.spec_basename_entry.get()
        try:
            new_spec_num=int(self.spec_startnum_entry.get())
        except:
            dialog=ErrorDialog(self,'Error: Invalid spectrum number')
            return
            
        try:
            new_spec_config_count=int(self.instrument_config_entry.get())
            if new_spec_config_count<1 or new_spec_config_count>32767:
                raise(Exception)
        except:
            dialog=ErrorDialog(self,label='Error: Invalid number of spectra to average.\nEnter a value from 1 to 32767')
            return    
            
        startnum_str=str(self.spec_startnum_entry.get())
        while len(startnum_str)<3:
            startnum_str='0'+startnum_str
            
        if new_spec_save_dir=='' or new_spec_basename=='':
            dialog=ErrorDialog(self,'Error: Please enter a save directory and a basename')
            return


        if new_spec_save_dir != self.spec_save_path or new_spec_basename != self.spec_basename or self.spec_num==None or new_spec_num!=self.spec_num:
            print('set save config!')
            self.set_save_config()
            
        if self.spec_config_count==None or str(new_spec_config_count) !=str(self.spec_config_count):
            print('configure!')
            self.configure_instrument()
            
        self.model.take_spectrum(incidence,emission)
        
        #filename=self.spec_save_path_entry.get()+'\\'+self.spec_basename_entry.get()+'.'+startnum_str
        #print('telling listener to expect '+filename)
        #filetupe=(filename,)
        #self.listener.ex_files=self.listener.ex_files+filetupe
        
        
        
        if self.spec_save_config.get():
            file=open(self.config_loc+'/spec_save','w')
            file.write(self.spec_save_path_entry.get()+'\n')
            file.write(self.spec_basename_entry.get()+'\n')
            file.write(self.spec_startnum_entry.get()+'\n')

            self.input_dir_entry.delete(0,'end')
            self.input_dir_entry.insert(0,self.spec_save_path_entry.get())
        timeout=new_spec_config_count+20
        print('oh wait I must have gotten here')
        wait_dialog=WaitDialog(self, timeout=timeout)
        return wait_dialog
    
    def configure_instrument(self):
        self.spec_config_count=self.instrument_config_entry.get()
        self.model.configure_instrument(self.spec_config_count)
        
    def set_save_config(self):
        self.spec_save_path=self.spec_save_path_entry.get()
        self.spec_basename = self.spec_basename_entry.get()
        spec_num=self.spec_startnum_entry.get()
        self.spec_num=int(spec_num)
        while len(spec_num)<3:
            spec_num='0'+spec_num
        self.listener.waiting_for_saveconfig='waiting'
        print('set save path, model!')
        self.model.set_save_path(self.spec_save_path, self.spec_basename, spec_num)
            
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
        filename=filename.replace('C:\\SpecShare',self.share_loc)
        if self.opsys=='Windows': filename=filename.replace('\\','/')
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
        self.spec_startnum_entry.delete(0,'end')
        self.spec_startnum_entry.insert(0,num)
    
    def validate_input_dir(self,*args):
        input_dir=rm_reserved_chars(self.input_dir_entry.get())
        self.input_dir_entry.delete(0,'end')
        self.input_dir_entry.insert(0,input_dir)
        
    def validate_output_dir(self):
        output_dir=rm_reserved_chars(self.output_dir_entry.get())
        self.output_dir_entry.delete(0,'end')
        self.output_dir_entry.insert(0,output_dir)

    def success(self):
        numstr=str(int(self.spec_num)-1)
        while len(numstr)<3:
            numstr='0'+numstr
        datestring=''
        datestringlist=str(datetime.datetime.now()).split('.')[:-1]
        for d in datestringlist:
            datestring=datestring+d
        info_string='SUCCESS:\n Spectrum saved at '+datestring+ '\n\ti='+self.man_incidence_entry.get()+'\n\te='+self.man_emission_entry.get()+'\n\tfilename='+self.spec_save_path+'\\'+self.spec_basename+'.'+numstr+'\n\tNotes: '+self.man_notes_entry.get()+'\n'
        
        self.textbox.insert(END,info_string)
        with open(self.log_filename,'a') as log:
            log.write(info_string)
            
        self.man_incidence_entry.delete(0,'end')
        self.man_emission_entry.delete(0,'end')
        self.man_notes_entry.delete(0,'end')

    
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
            try:
                arg1=dict[func][1]
                func(arg, arg1)
            except:
                func(arg)
        
    def no(self):
        dict=self.buttons['no']
        self.top.destroy()
        for func in dict:
            arg=dict[func][0]
            func(arg)
            
    def cancel(self):
        dict=self.buttons['cancel']
        print('made it to cancellation')
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
    def __init__(self, controller, title='Working...', label='Working...', buttons={'cancel':{}}, timeout=10):
        t0=time.clock()
        t=time.clock()
        self.canceled=False

        super().__init__(controller, title, label,buttons)
        
        self.interrupted=False
        
        self.frame=Frame(self.top, bg=self.bg, width=200, height=30)
        self.frame.pack()
  
        style=ttk.Style()
        style.configure('Horizontal.TProgressbar', background='white')
        self.pbar = ttk.Progressbar(self.frame, mode='indeterminate', name='pb2', style='Horizontal.TProgressbar' )
        self.pbar.start([10])
        self.pbar.pack(padx=(10,10),pady=(10,10))
        
        self.listener=self.controller.listener
        self.timeoutint=timeout
        
        thread = Thread(target = self.wait, args = (self.timeoutint, ))
        thread.start()
    
    def cancel(self):

        self.canceled=True
        
    def wait(self, timeoutint):
        
        print('my timeout is '+str(timeoutint))
        old_files=list(self.controller.listener.saved_files)
        for i in range(timeoutint):
            if self.canceled==True:
                print('canceled!')
                self.interrupt('Operation canceled by user. Warning! This might\nhave left some of your changes halfway entered\nor the spectrometer software in a strange state.')
                return
            if self.controller.listener.failed:
                self.controller.listener.failed=False
                self.interrupt('Error: Failed to save file.\nAre you sure the spectrometer is connected?')
                return
            #print('waiting for saveconfig?')
            #print(self.controller.listener.waiting_for_saveconfig)
            # elif self.listener.unexpected_file !=None:
            #     self.listener.unexpected_file=None

            elif 'failed' in self.controller.listener.waiting_for_saveconfig:
                if 'fileexists' in self.controller.listener.waiting_for_saveconfig:
                    self.interrupt('Error: File exists. Choose a different base name,\nspectrum number, or save directory and try again.')
                    #dialog=ErrorDialog(self.controller, label='Error: File exists. Choose a different base name,\nspectrum number, or save directory and try again.')
                else:
                    self.interrupt('Error: There was a problem with setting the save configuration.')
                    print('failed to save config for a different reason')
                self.controller.listener.waiting_for_saveconfig='done'
                print('waiting for saveconfig failed:')
                print(self.controller.listener.waiting_for_saveconfig)
                return
                
            elif self.controller.listener.noconfig=='noconfig':
                self.controller.listener.noconfig=''
                print('got noconfig, saving to current')
                self.controller.set_save_config()
                self.controller.model.take_spectrum(self.controller.man_incidence_entry.get(), self.controller.man_emission_entry.get())
            elif self.controller.listener.nonumspectra=='nonumspectra':
                self.controller.listener.nonumspectra=''
                print('got nonumspectra, saving to current')
                self.controller.configure_instrument()
                self.controller.model.take_spectrum(self.controller.man_incidence_entry.get(), self.controller.man_emission_entry.get())
                
            time.sleep(1)
            current_files=self.controller.listener.saved_files
            
            if current_files==old_files:
                pass
            else:
                for file in current_files:
                    if file not in old_files:
                        self.controller.spec_num+=1
                        self.controller.spec_startnum_entry.delete(0,'end')
                        spec_num_string=str(self.controller.spec_num)
                        while len(spec_num_string)<3:
                            spec_num_string='0'+spec_num_string
                        self.controller.spec_startnum_entry.insert(0,spec_num_string)
                        self.controller.success()
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
        #self.__ex_files=()
        # print('expected data files:')
        # print(self.ex_files)
        self.controller=None
        
        self.failed=False
        self.noconfig=''
        self.nonumspectra=''
        self.waiting_for_saveconfig=None
        self.unexpect_file=None
        
    # @property
    # def ex_files(self):
    #     return self.__ex_files

    #   @ex_files.setter
    # def ex_files(self, newfiles):
    #     print('changing data files to these ones:')
    #     print(newfiles)
    #     self.__ex_files=newfiles
    
    @property
    def nonumspectra(self):
        return self.__noconfig2
        
    @nonumspectra.setter
    def nonumspectra(self, val):
        print('changing noconfig2 to '+str(val))
        self.__noconfig2=val
        
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
                        print(cmd)
                        if 'savedfile' in cmd:
                            self.saved_files.append(params[0])

                        elif 'failedtosavefile' in cmd:
                            self.failed=True
                            
                        elif 'processerror' in cmd:
                            dialog=ErrorDialog(self.controller, label='Error: Processing failed.\nAre you sure directories exist?')
                            
                        elif 'unexpectedfile' in cmd:
                            self.unexpected_file=params[0]
                            try:
                                dialog=ErrorDialog(self.controller, label='Warning! Unexpected file in data directory.\nDoes this belong here? Make sure numbers match\nbetween computers before continuing\n\n'+params[0])
                            except:
                                print('Ignoring RuntimeError: Main thread not in main loop.')
                                
                        elif 'saveconfigerror' in cmd:
                            self.waiting_for_saveconfig='failed:saveconfigerror'
                            
                        elif 'saveconfigsuccess' in cmd:
                            self.waiting_for_saveconfig='success'
                            
                        elif 'noconfig' in cmd:
                            print("Spectrometer computer doesn't have a file configuration saved (python restart over there?). Setting to current configuration.")
                            self.noconfig='noconfig'
                            
                        elif 'nonumspectra' in cmd:
                            print("Spectrometer computer doesn't have an instrument configuration saved (python restart over there?). Setting to current configuration.")
                            self.nonumspectra='nonumspectra' 
                    
                        elif 'fileexists' in cmd:
                            self.waiting_for_saveconfig='failed:fileexists'
                            
                        else:
                            print('unexpected cmd: '+file)
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