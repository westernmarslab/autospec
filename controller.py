#The controller runs the main thread controlling the program.
#It creates and starts a View object, which extends Thread and will show a pygame window.

dev=True
test=True
online=False
computer='new'

import os
import sys
import platform

from tkinter import *
from tkinter import messagebox
import importlib
import threading
import tkinter as tk
from tkinter import ttk
#import pygame
try:
    import pexpect
except:
    os.system('python -m pip install pexpect')
    
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import matplotlib.backends.tkagg as tkagg
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime
import time
from threading import Thread

#Which computer are you using? This should probably be new. I don't know why you would use the old one.
computer='new'

#Figure out where this file is hanging out and tell python to look there for custom modules. This will depend on what operating system you are using.

global opsys
opsys=platform.system()
if opsys=='Darwin': opsys='Mac' #For some reason Macs identify themselves as Darwin. I don't know why but I think this is more intuitive.

global package_loc
package_loc=''

if opsys=='Windows':
    #If I am running this script from my IDE, __file__ is not defined. In that case, go with a hard-coded file location.
    try:
        rel_package_loc='\\'.join(__file__.split('\\')[:-1])+'\\'
        if 'C:' in rel_package_loc:
            package_loc=rel_package_loc
        else: package_loc=os.getcwd()+'\\'+rel_package_loc
    except:
        print('Developer mode!')
        dev=True
        package_loc='C:\\Users\\hozak\\Python\\autospectroscopy\\'

elif opsys=='Linux':
    try:
        rel_package_loc='/'.join(__file__.split('/')[:-1])+'/'
        if rel_package_loc[0]=='/':
            package_loc=rel_package_loc
        else: package_loc=os.getcwd()+'/'+rel_package_loc
    except:
        print('Developer mode!')
        dev=True
        package_loc='/home/khoza/Python/autospectroscopy/'
else:
    print("AHH I'm on a Mac!!")
    
sys.path.append(package_loc)

import robot_model
import robot_view
import plotter

#This is needed because otherwise changes won't show up until you restart the shell. Not needed if you aren't changing the modules.
if dev:
    importlib.reload(robot_model)
    from robot_model import Model
    importlib.reload(robot_view)
    from robot_view import View
    importlib.reload(plotter)
    from plotter import Plotter
    
#Server and share location. Can change if spectroscopy computer changes.
server=''
global NUMLEN
global tk_master
tk_master=None

NUMLEN=500
if computer=='old':
    #global NUMLEN
    NUMLEN=3
    server='melissa' #old computer
elif computer=='new':
    #global NUMLEN
    NUMLEN=5
    server='geol-chzc5q2' #new computer

share='specshare'

if opsys=='Linux':
    share_loc='/run/user/1000/gvfs/smb-share:server='+server+',share='+share+'/'
    delimiter='/'
    write_command_loc=share_loc+'commands/from_control/'
    read_command_loc=share_loc+'commands/from_spec/'
    config_loc=package_loc+'config/'
    log_loc=package_loc+'log/'
elif opsys=='Windows':
    share_loc='\\\\'+server.upper()+'\\'+share+'\\'
    write_command_loc=share_loc+'commands\\from_control\\'
    read_command_loc=share_loc+'commands\\from_spec\\'
    config_loc=package_loc+'config\\'
    log_loc=package_loc+'log\\'
elif opsys=='Mac':
    mac=ErrorDialog(self, label="ahhhhh I don't know what to do on a Mac!!")

def donothing():
    pass
def exit_func():
    print('exit!')
    exit()
    
def retry_func():
     os.execl(sys.executable, os.path.abspath(__file__), *sys.argv) 

def main():
    #if tk_master !=None:
    #    tk_master.destroy()
    #Check if you are connected to the server. If not, exit.
    try:
        files=os.listdir(read_command_loc)
    except:
        buttons={
            'retry':{
                main:[],
                },
            'exit':{
                exit_func:[]
            }
        }
            
        dialog=Dialog(controller=None, title='Not Connected',label='Error: No connection with server.\n\nCheck you are on the correct WiFi\nnetwork and server is mounted.',buttons=buttons)
        return


        
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
        print(os.getcwd())
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
            spec_startnum=str(int(self.spec_save_config.readline().strip('\n'))+1)
            while len(spec_startnum)<NUMLEN:
                spec_startnum='0'+spec_startnum
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
        
        self.label_label=Label(self.auto_frame, padx=padx,pady=pady,bg=bg, text='Label:')
        self.label_label.pack()
        self.label_entry=Entry(self.auto_frame, width=50, bd=bd)
        self.label_entry.pack(pady=(0,15))
        
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
        self.wrfailsafe_check.select()
        
        self.wr_timeout_frame=Frame(self.failsafe_frame, bg=bg)
        self.wr_timeout_frame.pack(pady=(0,10))
        self.wr_timeout_label=Label(self.wr_timeout_frame, text='Timeout (minutes):', bg=bg)
        self.wr_timeout_label.pack(side=LEFT, padx=(10,0))
        self.wr_timeout_entry=Entry(self.wr_timeout_frame, bd=bd,width=10)
        self.wr_timeout_entry.pack(side=LEFT, padx=(0,20))
        self.wr_timeout_entry.insert(0,'8')
        self.filler_label=Label(self.wr_timeout_frame,bg=bg,text='              ')
        self.filler_label.pack(side=LEFT)
        
        
        self.optfailsafe=IntVar()
        self.optfailsafe_check=Checkbutton(self.failsafe_frame, text='Prompt if the instrument has not been optimized.', bg=bg, pady=pady,highlightthickness=0, variable=self.optfailsafe)
        self.optfailsafe_check.pack()#side=LEFT, pady=pady)
        self.optfailsafe_check.select()
        
        self.opt_timeout_frame=Frame(self.failsafe_frame, bg=bg)
        self.opt_timeout_frame.pack()
        self.opt_timeout_label=Label(self.opt_timeout_frame, text='Timeout (minutes):', bg=bg)
        self.opt_timeout_label.pack(side=LEFT, padx=(10,0))
        self.opt_timeout_entry=Entry(self.opt_timeout_frame,bd=bd, width=10)
        self.opt_timeout_entry.pack(side=LEFT, padx=(0,20))
        self.opt_timeout_entry.insert(0,'60')
        self.filler_label=Label(self.opt_timeout_frame,bg=bg,text='              ')
        self.filler_label.pack(side=LEFT)
        
        self.anglesfailsafe=IntVar()
        self.anglesfailsafe_check=Checkbutton(self.failsafe_frame, text='Check validity of emission and incidence angles.', bg=bg, pady=pady,highlightthickness=0, variable=self.anglesfailsafe)
        self.anglesfailsafe_check.pack(pady=(6,5))#side=LEFT, pady=pady)
        self.anglesfailsafe_check.select()
        
        self.labelfailsafe=IntVar()
        self.labelfailsafe_check=Checkbutton(self.failsafe_frame, text='Require a label for each spectrum.', bg=bg, pady=pady,highlightthickness=0, variable=self.labelfailsafe)
        self.labelfailsafe_check.pack(pady=(6,5))#side=LEFT, pady=pady)
        self.labelfailsafe_check.select()
        
        
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
        
    
        #********************** Process frame ******************************
    
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
        # self.process_plot=IntVar()
        # self.process_plot_check=Checkbutton(self.process_check_frame, text='Plot spectra', bg=bg, pady=pady,highlightthickness=0)
        # self.process_plot_check.pack(side=LEFT, pady=(5,15))
        
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
        
        # self.plot_title_frame=Frame(self.plot_frame, bg=bg)
        # self.plot_title_frame.pack()
        self.plot_title_label=Label(self.plot_frame,padx=padx,pady=pady,bg=bg,text='Plot title:')
        self.plot_title_label.pack(padx=padx,pady=pady)
        self.plot_title_entry=Entry(self.plot_frame, width=50,bd=bd)
        self.plot_title_entry.pack()
        
        # self.plot_caption_frame=Frame(self.plot_frame, bg=bg)
        # self.plot_caption_frame.pack()
        # self.plot_caption_label=Label(self.plot_frame,padx=padx,pady=pady,bg=bg,text='Plot caption:')
        # self.plot_caption_label.pack(padx=padx,pady=pady)
        # self.plot_caption_entry=Entry(self.plot_frame, width=50)
        # self.plot_caption_entry.pack()
        
        self.no_wr_frame=Frame(self.plot_frame, bg=bg)
        self.no_wr_frame.pack()
        self.no_wr=IntVar()
        self.no_wr_check=Checkbutton(self.no_wr_frame, text='Exclude white references', bg=bg, pady=pady,highlightthickness=0, variable=self.no_wr, command=self.no_wr_cmd)
        self.no_wr_check.pack(pady=(5,5))
        self.no_wr_check.select()
        
        #self.no_wr_entry=Entry(self.load_labels_frame, width=50)
        
        self.load_labels_frame=Frame(self.plot_frame, bg=bg)
        self.load_labels_frame.pack()
        self.load_labels=IntVar()
        self.load_labels_check=Checkbutton(self.load_labels_frame, text='Load labels from log file', bg=bg, pady=pady,highlightthickness=0, variable=self.load_labels, command=self.load_labels_cmd)
        self.load_labels_check.pack(pady=(5,5))
        
        self.load_labels_entry=Entry(self.load_labels_frame, width=50)
        #self.load_labels_entry.pack()
        
        
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
        self.plot_button.pack(pady=(10,5))
    
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
        
    def no_wr_cmd(self):
        pass
        
    def load_labels_cmd(self):
        print('labels!')
        if self.load_labels.get():
            self.load_labels_entry.pack()
            if self.load_labels_entry.get()=='':
                self.load_labels_entry.insert(0,self.log_filename)
        else:
            self.load_labels_entry.pack_forget()
    
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
                
    def input_check(self, func, args=[]):
            label=''
            now=int(time.time())
            incidence=self.man_incidence_entry.get()
            emission=self.man_emission_entry.get()
            
            if self.optfailsafe.get():
                try:
                    opt_limit=int(float(self.opt_timeout_entry.get()))*60
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
                    
            if self.wrfailsafe.get():
                try:
                    wr_limit=int(float(self.wr_timeout_entry.get()))*60
                except:
                    wr_limit=sys.maxsize
                if self.wr_time==None:
                    label+='No white reference has been taken.\n'
                elif now-self.wr_time>wr_limit: 
                    minutes=str(int((now-self.wr_time)/60))
                    seconds=str((now-self.wr_time)%60)
                    if int(minutes)>0:
                        label+=' No white reference has been taken for '+minutes+' minutes '+seconds+' seconds.\n'
                    else: label+=' No white reference has been taken for '+seconds+' seconds.\n'
                    
            if self.anglesfailsafe.get():
                valid_i=validate_int_input(incidence,-90,90)
                valid_e=validate_int_input(emission,-90,90)
                if not valid_i or not valid_e:
                    label+='The emission and/or incidence angle is invalid\n'
                    
            if self.labelfailsafe.get():
                print('label check!')
                if self.label_entry.get()=='':
                    label +='This spectrum has no label.\n'

            if label !='': #if we came up with errors
                title='Warning!'
                
                buttons={
                    'yes':{
                        #if the user says they want to continue anyway, run take spectrum again but this time with override=True
                        func:args
                    },
                    'no':{}
                }
                label='Warning!\n'+label
                label+='Do you want to continue?'
                dialog=Dialog(self,title,label,buttons)
                return False
            else: #if there were no errors
                return True
        
    def wr(self, override=False):#opt_check=True):
        print('Going to white reference!')
        valid_input=True #We'll check this in a moment if override=False
        self.wr_time=int(time.time())
        if self.label_entry.get()!='' and 'White reference' not in self.label_entry.get():
            self.label_entry.insert(0, 'White reference: ')
        elif self.label_entry.get()=='':
            self.label_entry.insert(0,'White reference')

        if not override:
            valid_input=self.input_check(self.wr,[True])
            print(valid_input)
        #If the input wasn't valid, we already popped up an error dialog. If the user says to continue, wr will be called again with override=True
        if not valid_input:
            return
        else:
            print('invalid input')

        try:
            new_spec_config_count=int(self.instrument_config_entry.get())
            if new_spec_config_count<1 or new_spec_config_count>32767:
                raise(Exception)
        except:
            dialog=ErrorDialog(self,label='Error: Invalid number of spectra to average.\nEnter a value from 1 to 32767')
            return 
            
        print('new config count'+str(new_spec_config_count))
        print('old config count'+str(self.spec_config_count))
        if self.spec_config_count==None or str(new_spec_config_count) !=str(self.spec_config_count):
            print('time to configure!')
            
            self.configure_instrument()
            time.sleep(5)
            print('ok done waiting')
        config=self.check_save_config()
        if config:
            self.set_save_config(self.wr, [override])
            return
        self.model.white_reference()
        
        buttons={
            'success':{
                self.take_spectrum:[True]
            }
        }
        waitdialog=WaitForWRDialog(self, buttons=buttons)
    
        #We already did all the required input checks, so override them in take_spectrum
        #self.take_spectrum(override=True)
        
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
        
    def check_save_config(self):

        
        new_spec_save_dir=self.spec_save_path_entry.get()
        new_spec_basename=self.spec_basename_entry.get()
        new_spec_num=int(self.spec_startnum_entry.get())
        

            
        if new_spec_save_dir=='' or new_spec_basename=='':
            dialog=ErrorDialog(self,'Error: Please enter a save directory and a basename')
            return

        save_timeout=0
        config_timeout=0
        
        if new_spec_save_dir != self.spec_save_path or new_spec_basename != self.spec_basename or self.spec_num==None or new_spec_num!=self.spec_num:
            print('set save config')
            return True
        else:
            return False
        
            
    def take_spectrum(self, override=False):
        
        incidence=self.man_incidence_entry.get()
        emission=self.man_emission_entry.get()

        #If the user hasn't already said they want to override input checks 1) ask whether the user has input checkboxes selected in the Settings tab and then 2)if they do, see if the inputs are valid. If they aren't all valid, create one dialog box that will list everything wrong.
        valid_input=True
        if not override:  
            valid_input=self.input_check(self.take_spectrum,[True])
            
        #If input isn't valid and the user asks to continue, take_spectrum will be called again with override set to True
        if not valid_input:
            return

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
            
        if self.check_save_config():
            print('setting save_config from inside take spectrum')
            self.set_save_config(self.take_spectrum,[True])
            return
        config_timeout=0
        if self.spec_config_count==None or str(new_spec_config_count) !=str(self.spec_config_count):
            print('configure!')
            self.configure_instrument()
            config_timeout=15
            
        startnum_str=str(self.spec_startnum_entry.get())
        while len(startnum_str)<NUMLEN:
            startnum_str='0'+startnum_str

        self.model.take_spectrum(self.man_incidence_entry.get(), self.man_emission_entry.get(),self.spec_save_path, self.spec_basename, startnum_str)
        
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

        timeout=new_spec_config_count*2+20+config_timeout

        wait_dialog=WaitForSpectrumDialog(self, timeout=timeout)

        return wait_dialog
    
    def configure_instrument(self):
        self.spec_config_count=self.instrument_config_entry.get()
        self.model.configure_instrument(self.spec_config_count)
        
    def set_save_config(self, func, args):
        
        self.spec_save_path=self.spec_save_path_entry.get()
        self.spec_basename = self.spec_basename_entry.get()
        spec_num=self.spec_startnum_entry.get()
        self.spec_num=int(spec_num)
        while len(spec_num)<NUMLEN:
            spec_num='0'+spec_num
            
        self.model.set_save_path(self.spec_save_path, self.spec_basename, spec_num)
        buttons={
            'success':{
                func:args
            }
        }
        waitdialog=WaitForSaveConfigDialog(self, buttons=buttons, timeout=50)

        print('I am ready to move on')

        # self.listener.wait_for_unexpected='waiting'
        # self.model.check_for_unexpected
        # while self.listener.wait_for_unexpected=='waiting':
        #     print('waiting to see if there are unexpected files')
        # if self.listener.alert_unexpected=='True':
        #     error=ErrorDialog('hooray!')
        # self.listener.waiting_for_saveconfig='waiting'
        # print('set save path, model!')
        # error=
        # return error
            
            
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
        if output_file=='':
            dialog=ErrorDialog(self, label='Error: Enter an output file name')
            return
        if '.' not in output_file: output_file=output_file+'.tsv'
        error=self.model.process(self.input_dir_entry.get(), self.output_dir_entry.get(), output_file)
        if error!=None:
            dialog=ErrorDialog(self, label='Error sending process command:\n'+error.strerror)
        # try:
        #     self.model.process(self.input_dir_entry.get(), self.output_dir_entry.get(), output_file)
        # except:
        #     print("error:", sys.exc_info()[0])
        #     dialog=ErrorDialog(self)
        #     self.model.process(self.input_dir_entry.get(), self.output_dir_entry.get(), output_file)
        
        if self.process_save_dir.get():
            file=open(self.config_loc+'/process_directories','w')
            file.write(self.input_dir_entry.get()+'\n')
            file.write(self.output_dir_entry.get()+'\n')
            file.write(output_file+'\n')
            self.plot_input_dir_entry.delete(0,'end')
            plot_file=self.output_dir_entry.get()+'\\'+output_file
            self.plot_input_dir_entry.insert(0,plot_file)
            
        process_dialog=WaitForProcessDialog(self)
            
    def plot(self):
        filename=self.plot_input_dir_entry.get()
        filename=filename.replace('C:\\SpecShare',self.share_loc)
        if self.opsys=='Windows': filename=filename.replace('\\','/')
        title=self.plot_title_entry.get()
        caption=''#self.plot_caption_entry.get()
        labels={}
        nextfile=None
        nextnote=None
        try:
            if self.load_labels.get():
                with open(self.load_labels_entry.get()) as log:
                    for line in log:
                        if 'filename' in line:
                            if '\\' in line:
                                line=line.split('\\')
                            else:
                                line=line.split('/')
                            nextfile=line[-1].strip('\n')
                            nextfile=nextfile.split('.')
                            nextfile=nextfile[0]+nextfile[1]
                            print(nextfile)
                        elif 'Label' in line:
                            nextnote=line.split('Label: ')[-1]
                            print(nextnote)
                        if nextfile != None and nextnote != None:
                            labels[nextfile]=nextnote.strip('\n')
                            nextfile=None
                            nextnote=None
                        
                    
        except:
            dialog=ErrorDialog(self, label='Error! File not found: '+self.load_labels_entry.get())
        try:
            self.plotter.plot_spectra(title,filename,caption,labels)
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
            while len(num)<NUMLEN:
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
        while len(numstr)<NUMLEN:
            numstr='0'+numstr
        datestring=''
        datestringlist=str(datetime.datetime.now()).split('.')[:-1]
        for d in datestringlist:
            datestring=datestring+d
            
        info_string='SUCCESS:\n Spectrum saved at '+datestring+ '\n\ti='+self.man_incidence_entry.get()+'\n\te='+self.man_emission_entry.get()+'\n\tfilename='+self.spec_save_path+'\\'+self.spec_basename+'.'+numstr+'\n\tNotes: '+self.label_entry.get()+'\n'
        
        self.textbox.insert(END,info_string)
        with open(self.log_filename,'a') as log:
            log.write(info_string)
            
        self.man_incidence_entry.delete(0,'end')
        self.man_emission_entry.delete(0,'end')
        self.label_entry.delete(0,'end')

    
class Dialog:
    def __init__(self, controller, title, label, buttons, width=None, height=None):
        self.controller=controller
        self.bg='white'
        
        #If we are starting a new master, we'll need to start a new mainloop after settin everything up. 
        #If this creates a new toplevel for an existing master, we will leave it as False.
        start_mainloop=False
        if controller==None:
            self.top=Tk()
            start_mainloop=True
            global tk_master
            tk_master=self.top
            self.top.configure(background=self.bg)
        else:
            if width==None or height==None:
                self.top = tk.Toplevel(controller.master, bg=self.bg)
            else:
                self.top=tk.Toplevel(controller.master, width=width, height=height, bg='white')
                self.top.pack_propagate(0)

        self.label_frame=Frame(self.top, bg=self.bg)
        self.label_frame.pack(side=TOP)
        self.label = tk.Label(self.label_frame, text=label, bg=self.bg)
        self.label.pack(pady=(10,10), padx=(10,10))
    
        self.button_width=20
        self.buttons=buttons
        self.set_buttons(buttons)

        self.top.wm_title(title)
        
        if start_mainloop:
            self.top.mainloop()
            
    def set_label_text(self, newlabel):
        self.label.config(text=newlabel)
        
    def close_and_exec(self,func):
        print(func)
        func()
        self.top.destroy()
        
    def set_buttons(self, buttons):
        self.buttons=buttons
        try:
            self.button_frame.destroy()
        except:
            pass
        self.button_frame=Frame(self.top, bg=self.bg)
        self.button_frame.pack(side=BOTTOM)
        tk_buttons={}

        for button in buttons:
            if 'ok' in button.lower():
                self.ok_button = Button(self.button_frame, text='OK', command=self.ok, width=self.button_width)
                self.ok_button.pack(side=LEFT, padx=(10,10), pady=(10,10))
            elif 'yes' in button.lower():
                self.yes_button=Button(self.button_frame, text='Yes', bg='light gray', command=self.yes, width=self.button_width)
                self.yes_button.pack(side=LEFT, padx=(10,10), pady=(10,10))
            elif 'no' in button.lower():
                self.no_button=Button(self.button_frame, text='No',command=self.no, width=self.button_width)
                self.no_button.pack(side=LEFT, padx=(10,10), pady=(10,10))
            elif 'cancel' in button.lower():
                self.cancel_button=Button(self.button_frame, text='Cancel',command=self.cancel, width=self.button_width)
                self.cancel_button.pack(side=LEFT, padx=(10,10), pady=(10,10))
            elif 'retry' in button.lower():
                print('retry button added')
                self.retry_button=Button(self.button_frame, text='Retry',command=self.retry, width=self.button_width)
                self.retry_button.pack(side=LEFT, padx=(10,10), pady=(10,10))
            elif 'exit' in button.lower():
                self.exit_button=Button(self.button_frame, text='Exit',command=self.exit, width=self.button_width)
                self.exit_button.pack(side=LEFT, padx=(10,10), pady=(10,10))
            # else:
            #     #For each button, only handle one function with no arguments here 
            #     #the for loop is just a way to grab the function.
            #     #It would be cool to do better than this, but it will work for now.
            #     for func in buttons[button]:
            #         print(button)
            #         print(func)
            #         tk_buttons[button]=Button(self.button_frame, text=button,command=func)
            #         tk_buttons[button].pack(side=LEFT, padx=(10,10),pady=(10,10))
        
    def retry(self):
        dict=self.buttons['retry']
        self.top.destroy()
        for func in dict:
            if len(dict[func])>0:
                arg=dict[func][0]
                func(arg)
            else:
                print(func)
                func()
    def exit(self):
        self.top.destroy()
        exit()

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



class WaitDialog(Dialog):
    def __init__(self, controller, title='Working...', label='Working...', buttons={'cancel':{}}, timeout=30):
        super().__init__(controller, title, label,buttons,width=300, height=150)
        
        #We'll keep track of elapsed time so we can cancel the operation if it takes too long
        self.t0=time.clock()
        self.t=time.clock()
        self.timeout_s=timeout
        
        #I think these three attributes are useless and should be deleted
        self.canceled=False
        self.interrupted=False
        self.fileexists=False
        
        self.frame=Frame(self.top, bg=self.bg, width=200, height=30)
        self.frame.pack()
  
        style=ttk.Style()
        style.configure('Horizontal.TProgressbar', background='white')
        self.pbar = ttk.Progressbar(self.frame, mode='indeterminate', name='pb2', style='Horizontal.TProgressbar' )
        self.pbar.start([10])
        self.pbar.pack(padx=(10,10),pady=(10,10))
        
        #A Listener object is always running a loop in a separate thread. It  listens for files dropped into a command folder and changes its attributes based on what it finds.
        self.listener=self.controller.listener
        self.timeout_s=timeout

        #Start the wait function, which will watch the listener to see what attributes change and react accordingly.
        thread = Thread(target =self.wait, args = (self.timeout_s, ))
        thread.start()
        
    @property
    def timeout_s(self):
        return self.__timeout_s
        
    @timeout_s.setter
    def timeout_s(self, val):
        self.__timeout_s=val
        
    def wait(self, timeout_s):
        while True:
            print('waiting in super...')
            self.timeout_s-=1
            if self.timeout<0:
                self.timeout()
            time.sleep(1)
               
    def timeout(self):
        self.set_label_text('Error: Operation timed out')
        self.pbar.stop()
        self.set_buttons({'ok':{}})
        
    def finish(self):
        self.top.destroy()
        
    def cancel(self):
        self.canceled=True
        
    def interrupt(self,label):
        self.interrupted=True
        self.set_label_text(label)
        self.pbar.stop()
        self.set_buttons({'ok':{}})
                
    def send(self):
        global username
        username = self.myEntryBox.get()
        self.top.destroy()
        

        
# class WaitForUnexpectedDialog(WaitDialog):
#     def __init__(self, controller, title='Setting Save Configuration...', label='Working...', buttons={'cancel':{}}, timeout=30):
#         super().__init__(controller, title, label,buttons,timeout)
#         self.done=False
#     def wait(self, timeout_s):
#         print('wait for unexpected file check')
#         while self.timeout_s>0:
#             self.timeout_s -=1
#             time.sleep(1)
#             print(self.timeout_s)
#         
#         self.done=True
#         self.interrupt('ummm does anything happen')
#         
#     def interrupt(self,label):
#         self.interrupted=True
#         #self.controller.take_spectrum()
#         self.set_label_text(label)
#         self.pbar.stop()
#         self.set_buttons({'ok':{}})
#         # while True:
#         #     time.sleep(1)
#         #     print('keep me around')

class WaitForWRDialog(WaitDialog):
    def __init__(self, controller, title='White referencing...', label='White referencing...', buttons={'cancel':{}}, timeout=200):
        super().__init__(controller, title, label,buttons={},timeout=2*timeout)
        self.loc_buttons=buttons
        print(self.loc_buttons)

    def wait(self, timeout_s):
        while self.timeout_s>0:
            self.timeout_s-=1
            time.sleep(0.5)
            if self.controller.listener.wr_status=='success':
                self.controller.listener.wr_status='unknown'
                self.success()
                return
                
    def success(self):
        print('WR succeeded!')
        time.sleep(3)
        self.top.destroy()
        dict=self.loc_buttons['success']

        for func in dict:
            if len(dict[func])==1:
                arg=dict[func][0]
                func(arg)
            elif len(dict[func])==2:
                arg1=dict[func][0]
                arg2=dict[func][1]
                func(arg1,arg2)
            
            
class WaitForProcessDialog(WaitDialog):
    def __init__(self, controller, title='Processing...', label='Processing...', buttons={'cancel':{}}, timeout=200):
        super().__init__(controller, title, label,buttons={},timeout=2*timeout)

    def wait(self, timeout_s):
        while self.timeout_s>0:
            self.timeout_s-=1
            time.sleep(0.5)
            if self.controller.listener.process_status=='success':
                self.controller.listener.process_status='unknown'
                self.interrupt('Success!')
                return
            elif 'fileexists' in self.listener.process_status:
                self.controller.listener.process_status='unknown'
                self.interrupt('Error processing files: Output file already exists')
                
                return
            elif 'wropt' in self.listener.process_status:
                self.controller.listener.process_status='unknown'
                self.interrupt('Error processing files.\nDid you optimize and white reference before collecting data?')
                return
            elif self.controller.listener.process_status=='failure':
                self.controller.listener.process_status='unknown'
                self.interrupt('Error processing files.\nAre you sure directories exist?\n')
                return
        
class WaitForSaveConfigDialog(WaitDialog):
    def __init__(self, controller, title='Setting Save Configuration...', label='Setting save configuration...', buttons={'cancel':{}}, timeout=30):
        super().__init__(controller, title, label,buttons={},timeout=2*timeout)
        self.keep_around=False
        self.loc_buttons=buttons
        self.unexpected_files=[]
        self.listener.new_dialogs=False
    def wait(self, timeout_s, lookforunexpected=True):
        old_files=list(self.controller.listener.saved_files)
        while self.controller.listener.donelookingforunexpected==False:
            time.sleep(1)
            print('waiting to be done looking')
            print(self.controller.listener.unexpected_files)
        if len(self.controller.listener.unexpected_files)>0:
            self.keep_around=True
            print('found unexpected files')
            #dialog=ErrorDialog(self.controller,title='Untracked Files in Data Directory', label='unexpected files!\n\n'+'\n'.join(self.controller.listener.unexpected_files))
            #self.interrupt('unexpected files!\n\n'+'\n'.join(self.controller.listener.unexpected_files))
        self.unexpected_files=list(self.controller.listener.unexpected_files)
        self.controller.listener.unexpected_files=[]
        self.controller.listener.new_dialogs=True
        self.controller.listener.donelookingforunexpected=False
        while self.timeout_s>0:

            self.timeout_s-=1
            print('wait for saveconfig success')
            if self.controller.listener.saveconfig_status!='unknown':
                if 'success' in self.controller.listener.saveconfig_status:
                    print('success!')
                    self.controller.listener.saveconfig_status='unknown'
                    self.success()
                    return
                    
                elif 'failure' in self.controller.listener.saveconfig_status:
                    print('failure!')
                    #This seems silly. Shouldn't it do this earlier?
                    if 'fileexists' in self.controller.listener.saveconfig_status:
                        self.interrupt('Error: File exists. Choose a different base name,\nspectrum number, or save directory and try again.')
                        #dialog=ErrorDialog(self.controller, label='Error: File exists. Choose a different base name,\nspectrum number, or save directory and try again.')
                    else:
                        self.interrupt('Error: There was a problem with\nsetting the save configuration.\nIs the spectrometer connected?')
                        self.controller.spec_save_path=''
                        self.controller.spec_basename=''
                        self.controller.spec_num=None
                        print('failed to save config for a different reason')
                    self.controller.listener.saveconfig_status='unknown'
                    return
                
            # if self.controller.listener.fileexists:
            #     self.controller.listener.fileexists=False
            #     self.interrupt('Error: File exists. Choose a different base name,\nspectrum number, or save directory and try again.')
            #     return
                
            time.sleep(0.5)
        self.controller.listener.saveconfig_status=='unknown'
            

        
        self.interrupt('Error: timeout')
        
    def success(self):
        print('I succeeded!')
        print('keep me around? '+str(self.keep_around))
        print(self.loc_buttons)
        dict=self.loc_buttons['success']
        if not self.keep_around:
            self.top.destroy()
        else:
            self.pbar.stop()
            if len(self.unexpected_files)>1:
                self.set_label_text('Save configuration was set successfully,\nbut there are untracked files in the\ndata directory. Do these belong here?\n\n'+'\n'.join(self.unexpected_files))
            else:
                self.set_label_text('Save configuration was set successfully, but there is an\n untracked file in the data directory. Does this belong here?\n\n'+'\n'.join(self.unexpected_files))
            self.set_buttons({'ok':{}})
        for func in dict:
            if len(dict[func])==1:
                arg=dict[func][0]
                func(arg)
            elif len(dict[func])==2:
                arg1=dict[func][0]
                arg2=dict[func][1]
                func(arg1,arg2)
        
    def interrupt(self,label):
        self.interrupted=True
        #self.controller.take_spectrum()
        self.set_label_text(label)
        self.pbar.stop()
        self.set_buttons({'ok':{}})
        # while True:
        #     time.sleep(1)
        #     print('keep me around')
                
            
    
class WaitForSpectrumDialog(WaitDialog):
    def __init__(self, controller, title='Saving Spectrum...', label='Saving spectrum...', buttons={'cancel':{}}, timeout=30):
        super().__init__(controller, title, label, buttons={},timeout=2*timeout)
        
    def wait(self, timeout_s):
        print('waiting where I want to be')
        old_files=list(self.controller.listener.saved_files)
        while self.timeout_s>0:
            self.timeout_s-=1
            if self.canceled==True:
                print('canceled!')
                self.interrupt("Operation canceled by user. Warning! This really\ndoesn't do anything except stop tkinter from waiting\n, you probably still saved a spectrum")
                return
                

            if self.controller.listener.failed:
                self.controller.listener.failed=False
                self.interrupt('Error: Failed to save file.\nAre you sure the spectrometer is connected?')
                return
            #print('waiting for saveconfig?')
            #print(self.controller.listener.waiting_for_saveconfig)
            # elif self.listener.unexpected_file !=None:
            #     self.listener.unexpected_file=None


                
            elif self.controller.listener.noconfig=='noconfig':
                self.controller.listener.noconfig=''
                error=self.controller.set_save_config(self.controller.take_spectrum, [True])
                self.finish()
                return
                if error !=None:
                    self.interrupt(error.strerror)

                numstr=str(self.controller.spec_num)
                while len(numstr)<NUMLEN:
                    numstr='0'+numstr
                self.controller.model.take_spectrum(self.controller.man_incidence_entry.get(), self.controller.man_emission_entry.get(),self.controller.spec_save_path, self.controller.spec_basename, numstr)
                self.finish()

            elif self.controller.listener.nonumspectra=='nonumspectra':
                self.controller.listener.nonumspectra=''
                print('got nonumspectra, saving to current')
                self.controller.configure_instrument()
                numstr=str(self.controller.spec_num)
                while len(numstr)<NUMLEN:
                    numstr='0'+numstr
                self.controller.model.take_spectrum(self.controller.man_incidence_entry.get(), self.controller.man_emission_entry.get(),self.controller.spec_save_path, self.controller.spec_basename, numstr)
                #self.finish()
                
            time.sleep(0.5)
            current_files=self.controller.listener.saved_files
            
            if current_files==old_files:
                pass
            else:
                for file in current_files:
                    if file not in old_files:
                        self.controller.spec_num+=1
                        self.controller.spec_startnum_entry.delete(0,'end')
                        spec_num_string=str(self.controller.spec_num)
                        while len(spec_num_string)<NUMLEN:
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

        
class ErrorDialog(Dialog):
    def __init__(self, controller, title='Error', label='Error!', buttons={'ok':{}}, listener=None):
        self.listener=None
        super().__init__(controller, title, label,buttons)

        
def rm_reserved_chars(input):
    return input.strip('&').strip('+').strip('=')

def limit_len(input, max):
    return input[:max]
    
def validate_int_input(input, min, max):
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
        self.controller=None
        
        self.failed=False
        self.noconfig=''
        self.nonumspectra=''
        self.saveconfig_status='unknown'
        self.unexpected_files=[]
        
        self.process_status='unknown'
        self.wr_status='unknown'
        
        self.donelookingforunexpected=False
        self.wait_for_unexpected_count=0
        self.fileexists=False
        
        self.new_dialogs=True
        
    # @property
    # def ex_files(self):
    #     return self.__ex_files

    #   @ex_files.setter
    # def ex_files(self, newfiles):
    #     print('changing data files to these ones:')
    #     print(newfiles)
    #     self.__ex_files=newfiles
    
    @property
    def donelookingforunexpected(self):
        print('someone is getting'+str(self.__donelookingforunexpected))
        return self.__donelookingforunexpected
        
    @donelookingforunexpected.setter
    def donelookingforunexpected(self, val):
        print('setting done looking for unexpected to '+str(val))
        self.__donelookingforunexpected=val
    
    @property
    def nonumspectra(self):
        return self.__noconfig2
        
    @nonumspectra.setter
    def nonumspectra(self, val):
        #print('changing noconfig2 to '+str(val))
        self.__noconfig2=val
        
    def set_controller(self,controller):
        self.controller=controller
        
    def clear_unexpected_files():
        self.unexpected_files=[]
        
    def set_new_dialogs(self):
        print('got here')
        self.new_dialogs=True
    
    def run(self):
        files0=os.listdir(self.read_command_loc)

        while True:
            try:
                files=os.listdir(self.read_command_loc)
            except:
                if self.new_dialogs:
                    try:
                        self.new_dialogs=False
                        dialog=ErrorDialog(self.controller, title='Lost Connection',label='Error: Lost connection with server.\nCheck you are on the correct WiFi network and server is mounted.\n\n Exiting',buttons={'retry':{self.set_new_dialogs:[]}})

                    except:
                        print('Ignoring an error in Listener when I make a new error dialog')
                        time.sleep(10)
                        exit()
                
            if files==files0:

                pass
            else:
                for file in files:
                    if file not in files0:
                        cmd, params=filename_to_cmd(file)

                        print('listener sees this command: '+cmd)
                        if 'savedfile' in cmd:
                            self.saved_files.append(params[0])

                        elif 'failedtosavefile' in cmd:
                            self.failed=True
                        elif 'processsuccess' in cmd:
                            self.process_status='success'
                        elif 'processerrorfileexists' in cmd:
                            self.process_status='failurefileexists'
                        elif 'processerrorwropt' in cmd:
                            self.process_status='failurewropt'
                        elif 'processerror' in cmd:
                            self.process_status='failure'
                        elif 'wrsuccess' in cmd:
                            self.wr_status='success'
                            
                            #dialog=ErrorDialog(self.controller, label='Error: Processing failed.\nAre you sure directories exist?\nDoes the output file already exist?')
                            
                        elif 'unexpectedfile' in cmd:
                            if self.new_dialogs:
                                try:
                                    dialog=ErrorDialog(self.controller, title='Untracked Files',label='There is an untracked file in the data directory.\nDoes this belong here?\n\n'+params[0])
                                except:
                                    print('Ignoring an error in Listener when I make a new error dialog')
                            else:
                                self.unexpected_files.append(params[0])
                        elif 'donelookingforunexpected' in cmd:
                            self.donelookingforunexpected=True
                                
                        elif 'saveconfigerror' in cmd:
                            self.saveconfig_status='failure:saveconfigerror'
                            
                        elif 'saveconfigsuccess' in cmd:
                            self.saveconfig_status='success'
                            
                        elif 'noconfig' in cmd:
                            print("Spectrometer computer doesn't have a file configuration saved (python restart over there?). Setting to current configuration.")
                            self.noconfig='noconfig'
                            
                        elif 'nonumspectra' in cmd:
                            print("Spectrometer computer doesn't have an instrument configuration saved (python restart over there?). Setting to current configuration.")
                            self.nonumspectra='nonumspectra' 
                    
                        elif 'fileexists' in cmd:
                            self.fileexists=True
                            #This seems silly. Maybe not needed?
                            self.saveconfig_status='failure:fileexists'
                            print('The listener knows a file exists')
                            
                        else:
                            print('unexpected cmd: '+file)
                #This line always prints twice if it's uncommented, I'm not sure why.
                #print('forward!')
                
            files0=list(files)
                            
            time.sleep(0.5)
            
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