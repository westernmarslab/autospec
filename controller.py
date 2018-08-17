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
# try:
#     import pexpect
# except:
#     os.system('python -m pip install pexpect')
    
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import matplotlib.backends.tkagg as tkagg
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime
import time
from threading import Thread
from tkinter.filedialog import *

try:
    import httplib
except:
    import http.client as httplib

#Which computer are you using? This should probably be new. I don't know why you would use the old one.
computer='new'

#Figure out where this file is hanging out and tell python to look there for custom modules. This will depend on what operating system you are using.

global opsys
opsys=platform.system()
if opsys=='Darwin': opsys='Mac' #For some reason Macs identify themselves as Darwin. I don't know why but I think this is more intuitive.

global package_loc
package_loc=''

global cmdnum
cmdnum=0

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
    exit()
    
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

command_share='specshare'
data_share='users'

if opsys=='Linux':
    command_share_loc='/run/user/1000/gvfs/smb-share:server='+server+',share='+command_share+'/'
    delimiter='/'
    write_command_loc=command_share_loc+'commands/from_control/'
    read_command_loc=command_share_loc+'commands/from_spec/'
    config_loc=package_loc+'config/'
    log_loc=package_loc+'log/'
elif opsys=='Windows':
    command_share_loc='\\\\'+server.upper()+'\\'+command_share+'\\'
    write_command_loc=command_share_loc+'commands\\from_control\\'
    read_command_loc=command_share_loc+'commands\\from_spec\\'
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
     
import signal

 

class ConnectionChecker():
    def __init__(self,dir,thread, controller=None):
        self.thread=thread
        self.dir=dir
        self.controller=controller
    def alert_lost_connection(self, signum=None, frame=None):
            buttons={
                'retry':{
                    self.check_connection:[False],
                    },
                'exit':{
                    exit_func:[]
                }
            }
            dialog=Dialog(controller=self.controller, title='Lost Connection',label='Error: Lost connection with server.\n\nCheck you and the spectrometer computer are\nboth on the correct WiFi network and the\nserver is mounted on your computer',buttons=buttons)

    def alert_not_connected(self, signum=None, frame=None):
        buttons={
            'retry':{
                self.check_connection:[True],
                },
            'exit':{
                exit_func:[]
            }
        }
        dialog=Dialog(controller=self.controller, title='Not Connected',label='Error: No connection with server.\n\nCheck you and the spectrometer computer are\nboth on the correct WiFi network and the\nserver is mounted on your computer',buttons=buttons)
    def have_internet(self):
        conn = httplib.HTTPConnection("www.google.com", timeout=5)
        try:
            conn.request("HEAD", "/")
            conn.close()
            return True
        except:
            conn.close()
            return False
    
    def check_connection(self,firstconnection, attempt=0):
        connected=True
        if self.thread=='main':
            signal.signal(signal.SIGALRM, self.alert_not_connected)
            signal.alarm(2)
            # This may take a while to complete
            connected = os.path.isdir(self.dir)
            signal.alarm(0)          # Disable the alarm

        else:
            if self.have_internet()==False:
                connected=False
            else: 
                connected=os.path.isdir(self.dir)
                
        if connected==False:
            #For some reason reconnecting only seems to work on the second attempt. This seems like a pretty poor way to handle that, but I just call check_connection twice if it fails the first time.
            if attempt>0:
                self.alert_not_connected(None, None)
            else:
                time.sleep(0.5)
                self.check_connection(firstconnection, attempt=1)
        else:
            return True

def main():
    #Check if you are connected to the server. 
    connection_checker=ConnectionChecker(read_command_loc, thread='main')
    connection_checker.check_connection(True)

    #Clean out your read and write directories for commands. Prevents confusion based on past instances of the program.
    delme=os.listdir(write_command_loc)
    for file in delme:
        os.remove(write_command_loc+file)
    delme=os.listdir(read_command_loc)
    for file in delme:
        os.remove(read_command_loc+file)
    
    #Create a listener, which listens for commands, and a controller, which manages the model (which writes commands) and the view.
    listener=Listener(read_command_loc)
    control=Controller(listener, command_share_loc, read_command_loc,write_command_loc, config_loc,opsys)

class Controller():
    def __init__(self, listener, command_share_loc, read_command_loc, write_command_loc, config_loc, opsys):
        self.listener=listener
        self.listener.set_controller(self)
        self.listener.start()
        
        self.read_command_loc=read_command_loc
        self.command_share_loc=command_share_loc
        self.write_command_loc=write_command_loc
        self.config_loc=config_loc
        self.opsys=opsys
        self.log_filename=None
        
        #These will get set via user input.
        self.spec_save_path=''
        self.spec_basename=''
        self.spec_num=None
        self.spec_config_count=None
        self.take_spectrum_with_bad_i_or_e=False
        self.wr_time=None
        self.opt_time=None
        self.i=-1000
        self.e=-1000
        
        #Tkinter notebook GUI
        self.master=Tk()
        self.tk_master=self.master
        self.notebook=ttk.Notebook(self.master)
        
        #The plotter, surprisingly, plots things.
        self.plotter=Plotter(self.master)
        
        #The view displays what the software thinks the goniometer is up to.
        self.view=View()
        self.view.start()
    
        #The model keeps track of the goniometer state and sends commands to the raspberry pi and spectrometer
        self.model=Model(self.view, self.plotter, self.write_command_loc, False, False)
        
        #Yay formatting. Might not work for Macs.
        self.bg='#555555'
        self.textcolor='light gray'
        self.buttontextcolor='white'
        bd=2
        padx=3
        pady=3
        border_color='light gray'
        button_width=15
        self.buttonbackgroundcolor='#888888'
        self.highlightbackgroundcolor='#222222'
        self.entry_background='light gray'
        self.listboxhighlightcolor='white'
        self.master.configure(background = self.bg)
        self.master.title('Control')
    
        #If the user has saved spectra with this program before, load in their previously used directories.
        process_config=open(self.config_loc+'process_directories','r')
        input_dir=''
        output_dir=''
        try:
            input_dir=process_config.readline().strip('\n')
            output_dir=process_config.readline().strip('\n')
        except:
            pass
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
            print('invalid config file')
        
        self.control_frame=Frame(self.notebook, bg=self.bg)
        self.control_frame.pack()
        self.save_config_frame=Frame(self.control_frame,bg=self.bg,highlightthickness=1)
        self.save_config_frame.pack(fill=BOTH,expand=True)
        self.spec_save_label=Label(self.save_config_frame,padx=padx,pady=pady,bg=self.bg,fg=self.textcolor,text='Spectra save configuration:')
        self.spec_save_label.pack(pady=(15,5))
        self.spec_save_path_label=Label(self.save_config_frame,padx=padx,pady=pady,bg=self.bg,fg=self.textcolor,text='Directory:')
        self.spec_save_path_label.pack(padx=padx)
        
        self.spec_save_dir_frame=Frame(self.save_config_frame,bg=self.bg)
        self.spec_save_dir_frame.pack()
        
        self.spec_save_dir_browse_button=Button(self.spec_save_dir_frame,text='Browse',command=self.choose_spec_save_dir)
        self.spec_save_dir_browse_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.spec_save_dir_browse_button.pack(side=RIGHT, padx=padx)
        
        self.spec_save_dir_entry=Entry(self.spec_save_dir_frame, width=50,bd=bd,bg=self.entry_background)
        self.spec_save_dir_entry.insert(0, self.spec_save_path)
        self.spec_save_dir_entry.pack(padx=padx, pady=pady, side=RIGHT)
        
        
    
        self.spec_save_frame=Frame(self.save_config_frame, bg=self.bg)
        self.spec_save_frame.pack()
        
        self.spec_basename_label=Label(self.spec_save_frame,pady=pady,bg=self.bg,fg=self.textcolor,text='Base name:')
        self.spec_basename_label.pack(side=LEFT,pady=(5,15),padx=(0,0))
        self.spec_basename_entry=Entry(self.spec_save_frame, width=10,bd=bd,bg=self.entry_background)
        self.spec_basename_entry.pack(side=LEFT,padx=(5,5), pady=pady)
        self.spec_basename_entry.insert(0,self.spec_basename)
        
        self.spec_startnum_label=Label(self.spec_save_frame,padx=padx,pady=pady,bg=self.bg,fg=self.textcolor,text='Number:')
        self.spec_startnum_label.pack(side=LEFT,pady=pady)
        self.spec_startnum_entry=Entry(self.spec_save_frame, width=10,bd=bd,bg=self.entry_background)
        self.spec_startnum_entry.insert(0,spec_startnum)
        self.spec_startnum_entry.pack(side=RIGHT, pady=pady)
        
        
        
            
        self.log_frame=Frame(self.control_frame, bg=self.bg,highlightthickness=1)
        self.log_frame.pack(fill=BOTH,expand=True)
        self.logfile_label=Label(self.log_frame,padx=padx,pady=pady,bg=self.bg,fg=self.textcolor,text='Log file:')
        self.logfile_label.pack(padx=padx,pady=(10,0))
        self.logfile_entry_frame=Frame(self.log_frame, bg=self.bg)
        self.logfile_entry_frame.pack()
        self.logfile_entry=Entry(self.logfile_entry_frame, width=50,bd=bd,bg=self.entry_background)
        self.logfile_entry.pack(padx=padx, pady=(5,15))
        self.logfile_entry.enabled=False
        self.select_logfile_button=Button(self.logfile_entry_frame, fg=self.textcolor,text='Select existing',command=self.chooselogfile, width=13, height=1,bg=self.buttonbackgroundcolor)
        self.select_logfile_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor)
        self.select_logfile_button.pack(side=LEFT,padx=(50,5), pady=(0,10))
        
        self.new_logfile_button=Button(self.logfile_entry_frame, fg=self.textcolor,text='New log file',command=self.newlog, width=13, height=1)
        self.new_logfile_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.new_logfile_button.pack(side=LEFT,padx=padx, pady=(0,10))
        
        
        
        self.spec_save_config=IntVar()
        self.spec_save_config_check=Checkbutton(self.save_config_frame, fg=self.textcolor,text='Save file configuration', bg=self.bg, pady=pady,highlightthickness=0, variable=self.spec_save_config)
        #self.spec_save_config_check.pack(pady=(0,5))
        self.spec_save_config_check.select()
        
        self.spectrum_settings_frame=Frame(self.control_frame,bg=self.bg, highlightcolor="green", highlightthickness=1)
        self.spectrum_settings_frame.pack(fill=BOTH,expand=True)
        self.spec_settings_label=Label(self.spectrum_settings_frame,padx=padx,pady=pady,bg=self.bg,fg=self.textcolor,text='Settings for this spectrum:')
        self.spec_settings_label.pack(padx=padx,pady=(10,0))
        self.instrument_config_frame=Frame(self.spectrum_settings_frame, bg=self.bg)
        self.instrument_config_frame.pack(pady=(15,15))
        self.instrument_config_label=Label(self.instrument_config_frame, fg=self.textcolor,text='Number of spectra to average:', bg=self.bg)
        self.instrument_config_label.pack(side=LEFT)
        self.instrument_config_entry=Entry(self.instrument_config_frame, width=10, bd=bd,bg=self.entry_background)
        self.instrument_config_entry.insert(0, 5)
        self.instrument_config_entry.pack(side=LEFT)

        
        self.spectrum_angles_frame=Frame(self.spectrum_settings_frame, bg=self.bg)
        self.spectrum_angles_frame.pack()
        self.man_incidence_label=Label(self.spectrum_angles_frame,padx=padx,pady=pady,bg=self.bg,fg=self.textcolor,text='Incidence angle:')
        self.man_incidence_label.pack(side=LEFT, padx=padx,pady=(0,8))
        self.man_incidence_entry=Entry(self.spectrum_angles_frame, width=10, bd=bd,bg=self.entry_background)
        self.man_incidence_entry.pack(side=LEFT)
        self.man_emission_label=Label(self.spectrum_angles_frame, padx=padx,pady=pady,bg=self.bg, fg=self.textcolor,text='Emission angle:')
        self.man_emission_label.pack(side=LEFT, padx=(10,0))
        self.man_emission_entry=Entry(self.spectrum_angles_frame, width=10, bd=bd,bg=self.entry_background)
        self.man_emission_entry.pack(side=LEFT, padx=(0,20))
        

        self.label_label=Label(self.spectrum_settings_frame, padx=padx,pady=pady,bg=self.bg, fg=self.textcolor,text='Label:')
        self.label_label.pack()
        self.label_entry=Entry(self.spectrum_settings_frame, width=50, bd=bd,bg=self.entry_background)
        self.label_entry.pack(pady=(0,15))
        
        self.top_frame=Frame(self.control_frame,padx=padx,pady=pady,bd=2,highlightbackground=border_color,highlightcolor=border_color,highlightthickness=0,bg=self.bg)
        #self.top_frame.pack()
        self.light_frame=Frame(self.top_frame,bg=self.bg)
        self.light_frame.pack(side=LEFT)
        self.light_label=Label(self.light_frame,padx=padx, pady=pady,bg=self.bg,fg=self.textcolor,text='Light Source')
        self.light_label.pack()
        
        light_labels_frame = Frame(self.light_frame,bg=self.bg,padx=padx,pady=pady)
        light_labels_frame.pack(side=LEFT)
        
        light_start_label=Label(light_labels_frame,padx=padx,pady=pady,bg=self.bg,fg=self.textcolor,text='Start:')
        light_start_label.pack(pady=(0,8))
        #light_end_label=Label(light_labels_frame,bg=self.bg,padx=padx,pady=pady,fg=self.textcolor,text='End:',fg='lightgray')
        #light_end_label.pack(pady=(0,5))
    
        #light_increment_label=Label(light_labels_frame,bg=self.bg,padx=padx,pady=pady,fg=self.textcolor,text='Increment:',fg='lightgray')
       # light_increment_label.pack(pady=(0,5))
    
        
        light_entries_frame=Frame(self.light_frame,bg=self.bg,padx=padx,pady=pady)
        light_entries_frame.pack(side=RIGHT)
        
        light_start_entry=Entry(light_entries_frame,width=10, bd=bd,bg=self.entry_background)
        light_start_entry.pack(padx=padx,pady=pady)
        light_start_entry.insert(0,'10')
        
        light_end_entry=Entry(light_entries_frame,width=10, highlightbackground='white', bd=bd,bg=self.entry_background)
        light_end_entry.pack(padx=padx,pady=pady)    
        light_increment_entry=Entry(light_entries_frame,width=10,highlightbackground='white', bd=bd,bg=self.entry_background)
        light_increment_entry.pack(padx=padx,pady=pady)
        
        detector_frame=Frame(self.top_frame,bg=self.bg)
        detector_frame.pack(side=RIGHT)
        
        detector_label=Label(detector_frame,padx=padx, pady=pady,bg=self.bg,fg=self.textcolor,text='Detector')
        detector_label.pack()
        
        detector_labels_frame = Frame(detector_frame,bg=self.bg,padx=padx,pady=pady)
        detector_labels_frame.pack(side=LEFT)
        
        detector_start_label=Label(detector_labels_frame,padx=padx,pady=pady,bg=self.bg,fg=self.textcolor,text='Start:')
        detector_start_label.pack(pady=(0,8))
        #detector_end_label=Label(detector_labels_frame,bg=self.bg,padx=padx,pady=pady,fg=self.textcolor,text='End:',fg='lightgray')
        #detector_end_label.pack(pady=(0,5))
    
        #detector_increment_label=Label(detector_labels_frame,bg=self.bg,padx=padx,pady=pady,fg=self.textcolor,text='Increment:',fg='lightgray')
        #detector_increment_label.pack(pady=(0,5))
    
        
        detector_entries_frame=Frame(detector_frame,bg=self.bg,padx=padx,pady=pady)
        detector_entries_frame.pack(side=RIGHT)
        detector_start_entry=Entry(detector_entries_frame,bd=bd,width=10,bg=self.entry_background)
        detector_start_entry.pack(padx=padx,pady=pady)
        detector_start_entry.insert(0,'0')
        
        detector_end_entry=Entry(detector_entries_frame,bd=bd,width=10,highlightbackground='white',bg=self.entry_background)
        detector_end_entry.pack(padx=padx,pady=pady)
        
        detector_increment_entry=Entry(detector_entries_frame,bd=bd,width=10, highlightbackground='white',bg=self.entry_background)
        detector_increment_entry.pack(padx=padx,pady=pady)
        
        self.auto_check_frame=Frame(self.control_frame, bg=self.bg)
        self.auto_process=IntVar()
        self.auto_process_check=Checkbutton(self.auto_check_frame, fg=self.textcolor,text='Process data', bg=self.bg, highlightthickness=0)
        self.auto_process_check.pack(side=LEFT)
        
        self.auto_plot=IntVar()
        self.auto_plot_check=Checkbutton(self.auto_check_frame, fg=self.textcolor,text='Plot spectra', bg=self.bg, highlightthickness=0)
        self.auto_plot_check.pack(side=LEFT)
        
        self.gen_frame=Frame(self.control_frame, bg=self.bg,highlightthickness=1)
        self.gen_frame.pack(fill=BOTH,expand=True)
        self.action_button_frame=Frame(self.gen_frame, bg=self.bg)
        self.action_button_frame.pack()
        
        button_width=20
        self.opt_button=Button(self.action_button_frame, fg=self.textcolor,text='Optimize', padx=padx, pady=pady,width=button_width, bg='light gray', command=self.opt, height=2)
        self.opt_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.opt_button.pack(padx=padx,pady=pady, side=LEFT)
        self.wr_button=Button(self.action_button_frame, fg=self.textcolor,text='White Reference', padx=padx, pady=pady, width=button_width, bg='light gray', command=self.wr, height=2)
        self.wr_button.pack(padx=padx,pady=pady, side=LEFT)
        self.wr_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
    
        self.go_button=Button(self.action_button_frame, fg=self.textcolor,text='Take Spectrum', padx=padx, pady=pady, width=button_width,height=2,bg='light gray', command=self.go)
        self.go_button.pack(padx=padx,pady=pady, side=LEFT)
        self.go_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        
        #***************************************************************
        # Frame for settings
        
        self.dumb_frame=Frame(self.notebook, bg=self.bg, pady=2*pady)
        self.dumb_frame.pack()
        # entries_frame=Frame(man_frame, bg=self.bg)
        # entries_frame.pack(fill=BOTH, expand=True)
        # man_light_label=Label(entries_frame,padx=padx, pady=pady,bg=self.bg,fg=self.textcolor,text='Instrument positions:')
        # man_light_label.pack()
        # man_light_label=Label(entries_frame,padx=padx,pady=pady,bg=self.bg,fg=self.textcolor,text='Incidence:')
        # man_light_label.pack(side=LEFT, padx=(30,5),pady=(0,8))
        # man_light_entry=Entry(entries_frame, width=10)
        # man_light_entry.insert(0,'10')
        # man_light_entry.pack(side=LEFT)
        # man_detector_label=Label(entries_frame, padx=padx,pady=pady,bg=self.bg, fg=self.textcolor,text='Emission:')
        # man_detector_label.pack(side=LEFT, padx=(10,0))
        # man_detector_entry=Entry(entries_frame, width=10,fg=self.textcolor,text='0')
        # man_detector_entry.insert(0,'10')
        # man_detector_entry.pack(side=LEFT)

        # self.instrument_config_title_frame=Frame(self.dumb_frame, bg=self.bg)
        # self.instrument_config_title_frame.pack(pady=pady)
        # self.instrument_config_label0=Label(self.instrument_config_title_frame, fg=self.textcolor,text='Instrument Configuration:                                ', bg=self.bg)
        # self.instrument_config_label0.pack(side=LEFT)

        
        self.automation_title_frame=Frame(self.dumb_frame, bg=self.bg)
        self.automation_title_frame.pack(pady=pady)
        self.automation_label0=Label(self.automation_title_frame, fg=self.textcolor,text='Automation:                                               ', bg=self.bg)
        self.automation_label0.pack(side=LEFT)
        
        
        self.auto_check_frame=Frame(self.dumb_frame, bg=self.bg)
        self.auto_check_frame.pack()
        self.auto=IntVar()
        self.auto_check=Checkbutton(self.auto_check_frame, fg=self.textcolor,text='Automatically iterate through viewing geometries', bg=self.bg, pady=pady,highlightthickness=0, variable=self.auto, command=self.auto_cycle_check)
        self.auto_check.pack(side=LEFT, pady=pady)
        
        self.timer_title_frame=Frame(self.dumb_frame, bg=self.bg)
        self.timer_title_frame.pack(pady=(10,0))
        self.timer_label0=Label(self.timer_title_frame, fg=self.textcolor,text='Timer:                                                   ', bg=self.bg)
        self.timer_label0.pack(side=LEFT)
        self.timer_frame=Frame(self.dumb_frame, bg=self.bg, pady=pady)
        self.timer_frame.pack()
        self.timer_check_frame=Frame(self.timer_frame, bg=self.bg)
        self.timer_check_frame.pack(pady=pady)
        self.timer=IntVar()
        self.timer_check=Checkbutton(self.timer_check_frame, fg=self.textcolor,text='Collect sets of spectra using a timer           ', bg=self.bg, pady=pady,highlightthickness=0, variable=self.timer)
        self.timer_check.pack(side=LEFT, pady=pady)
        
        self.timer_duration_frame=Frame(self.timer_frame, bg=self.bg)
        self.timer_duration_frame.pack()
        self.timer_spectra_label=Label(self.timer_duration_frame,padx=padx,pady=pady,bg=self.bg,fg=self.textcolor,text='Total duration (min):')
        self.timer_spectra_label.pack(side=LEFT, padx=padx,pady=(0,8))
        self.timer_spectra_entry=Entry(self.timer_duration_frame, bd=1,width=10,bg=self.entry_background)
        self.timer_spectra_entry.pack(side=LEFT)
        self.filler_label=Label(self.timer_duration_frame,bg=self.bg,fg=self.textcolor,text='              ')
        self.filler_label.pack(side=LEFT)
        
        self.timer_interval_frame=Frame(self.timer_frame, bg=self.bg)
        self.timer_interval_frame.pack()
        self.timer_interval_label=Label(self.timer_interval_frame, padx=padx,pady=pady,bg=self.bg, fg=self.textcolor,text='Interval (min):')
        self.timer_interval_label.pack(side=LEFT, padx=(10,0))
        self.timer_interval_entry=Entry(self.timer_interval_frame,bd=bd,width=10,fg=self.textcolor,text='0',bg=self.entry_background)
    # self.timer_interval_entry.insert(0,'-1')
        self.timer_interval_entry.pack(side=LEFT, padx=(0,20))
        self.filler_label=Label(self.timer_interval_frame,bg=self.bg,fg=self.textcolor,text='                   ')
        self.filler_label.pack(side=LEFT)
        
        self.failsafe_title_frame=Frame(self.dumb_frame, bg=self.bg)
        self.failsafe_title_frame.pack(pady=(10,0))
        self.failsafe_label0=Label(self.failsafe_title_frame, fg=self.textcolor,text='Failsafes:                                              ', bg=self.bg)
        self.failsafe_label0.pack(side=LEFT)
        self.failsafe_frame=Frame(self.dumb_frame, bg=self.bg, pady=pady)
        self.failsafe_frame.pack(pady=pady)

        
        self.wrfailsafe=IntVar()
        self.wrfailsafe_check=Checkbutton(self.failsafe_frame, fg=self.textcolor,text='Prompt if no white reference has been taken.    ', bg=self.bg, pady=pady,highlightthickness=0, variable=self.wrfailsafe)
        self.wrfailsafe_check.pack()#side=LEFT, pady=pady)
        self.wrfailsafe_check.select()
        
        self.wr_timeout_frame=Frame(self.failsafe_frame, bg=self.bg)
        self.wr_timeout_frame.pack(pady=(0,10))
        self.wr_timeout_label=Label(self.wr_timeout_frame, fg=self.textcolor,text='Timeout (minutes):', bg=self.bg)
        self.wr_timeout_label.pack(side=LEFT, padx=(10,0))
        self.wr_timeout_entry=Entry(self.wr_timeout_frame, bd=bd,width=10,bg=self.entry_background)
        self.wr_timeout_entry.pack(side=LEFT, padx=(0,20))
        self.wr_timeout_entry.insert(0,'8')
        self.filler_label=Label(self.wr_timeout_frame,bg=self.bg,fg=self.textcolor,text='              ')
        self.filler_label.pack(side=LEFT)
        
        
        self.optfailsafe=IntVar()
        self.optfailsafe_check=Checkbutton(self.failsafe_frame, fg=self.textcolor,text='Prompt if the instrument has not been optimized.', bg=self.bg, pady=pady,highlightthickness=0, variable=self.optfailsafe)
        self.optfailsafe_check.pack()#side=LEFT, pady=pady)
        self.optfailsafe_check.select()
        
        self.opt_timeout_frame=Frame(self.failsafe_frame, bg=self.bg)
        self.opt_timeout_frame.pack()
        self.opt_timeout_label=Label(self.opt_timeout_frame, fg=self.textcolor,text='Timeout (minutes):', bg=self.bg)
        self.opt_timeout_label.pack(side=LEFT, padx=(10,0))
        self.opt_timeout_entry=Entry(self.opt_timeout_frame,bd=bd, width=10,bg=self.entry_background)
        self.opt_timeout_entry.pack(side=LEFT, padx=(0,20))
        self.opt_timeout_entry.insert(0,'60')
        self.filler_label=Label(self.opt_timeout_frame,bg=self.bg,fg=self.textcolor,text='              ')
        self.filler_label.pack(side=LEFT)
        
        self.anglesfailsafe=IntVar()
        self.anglesfailsafe_check=Checkbutton(self.failsafe_frame, fg=self.textcolor,text='Check validity of emission and incidence angles.', bg=self.bg, pady=pady,highlightthickness=0, variable=self.anglesfailsafe)
        self.anglesfailsafe_check.pack(pady=(6,5))#side=LEFT, pady=pady)
        self.anglesfailsafe_check.select()
        
        self.labelfailsafe=IntVar()
        self.labelfailsafe_check=Checkbutton(self.failsafe_frame, fg=self.textcolor,text='Require a label for each spectrum.', bg=self.bg, pady=pady,highlightthickness=0, variable=self.labelfailsafe)
        self.labelfailsafe_check.pack(pady=(6,5))#side=LEFT, pady=pady)
        self.labelfailsafe_check.select()
        
        self.anglechangefailsafe=IntVar()
        self.anglechangefailsafe_check=Checkbutton(self.failsafe_frame, fg=self.textcolor,text='Remind me to check the goniometer if\nincidence and/or emission angles change.', bg=self.bg, pady=pady,highlightthickness=0, variable=self.anglechangefailsafe)
        self.anglechangefailsafe_check.pack(pady=(6,5))#side=LEFT, pady=pady)
        self.anglechangefailsafe_check.select()
        
        
        # check_frame=Frame(man_frame, bg=self.bg)
        # check_frame.pack()
        # process=IntVar()
        # process_check=Checkbutton(check_frame, fg=self.textcolor,text='Process data', bg=self.bg, pady=pady,highlightthickness=0)
        # process_check.pack(side=LEFT, pady=(5,15))
        # 
        # plot=IntVar()
        # plot_check=Checkbutton(check_frame, fg=self.textcolor,text='Plot spectrum', bg=self.bg, pady=pady,highlightthickness=0)
        # plot_check.pack(side=LEFT, pady=(5,15))
    
        #   move_button=Button(man_frame, fg=self.textcolor,text='Move', padx=padx, pady=pady, width=int(button_width*1.6),bg='light gray', command=go)
        # move_button.pack(padx=padx,pady=pady, side=LEFT)
        # spectrum_button=Button(man_frame, fg=self.textcolor,text='Collect data', padx=padx, pady=pady, width=int(button_width*1.6), bg='light gray', command=take_spectrum)
        # spectrum_button.pack(padx=padx,pady=pady, side=LEFT)
        
    
        #********************** Process frame ******************************
    
        self.process_frame=Frame(self.notebook, bg=self.bg, pady=2*pady)
        self.process_frame.pack()

        self.input_dir_label=Label(self.process_frame,padx=padx,pady=pady,bg=self.bg,fg=self.textcolor,text='Input directory:')
        self.input_dir_label.pack(padx=padx,pady=pady)
        
        self.input_frame=Frame(self.process_frame, bg=self.bg)
        self.input_frame.pack()
        
        self.process_input_browse_button=Button(self.input_frame,text='Browse',command=self.choose_process_input_dir)
        self.process_input_browse_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.process_input_browse_button.pack(side=RIGHT, padx=padx)
        
        
        self.input_dir_var = StringVar()
        self.input_dir_var.trace('w', self.validate_input_dir)
         
        self.input_dir_entry=Entry(self.input_frame, width=50,bd=bd, textvariable=self.input_dir_var,bg=self.entry_background)
        self.input_dir_entry.insert(0, input_dir)
        self.input_dir_entry.pack(side=RIGHT,padx=padx)
        

        self.output_dir_label=Label(self.process_frame,padx=padx,pady=pady,bg=self.bg,fg=self.textcolor,text='Output directory:')
        self.output_dir_label.pack(padx=padx,pady=pady)
        
        self.output_frame=Frame(self.process_frame, bg=self.bg)
        self.output_frame.pack()
        self.process_output_browse_button=Button(self.output_frame,text='Browse',command=self.choose_process_output_dir)
        self.process_output_browse_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.process_output_browse_button.pack(side=RIGHT, padx=padx)
        
        self.output_dir_entry=Entry(self.output_frame, width=50,bd=bd,bg=self.entry_background)
        self.output_dir_entry.insert(0, output_dir)
        self.output_dir_entry.pack(side=RIGHT,padx=padx)
        
        self.output_file_frame=Frame(self.process_frame, bg=self.bg)
        self.output_file_frame.pack()
        self.output_file_label=Label(self.process_frame,padx=padx,pady=pady,bg=self.bg,fg=self.textcolor,text='Output file name:')
        self.output_file_label.pack(padx=padx,pady=pady)
        self.output_file_entry=Entry(self.process_frame, width=50,bd=bd,bg=self.entry_background)
        self.output_file_entry.pack()
        
        
        self.process_check_frame=Frame(self.process_frame, bg=self.bg)
        self.process_check_frame.pack(pady=(15,5))
        self.process_save_dir=IntVar()
        self.process_save_dir_check=Checkbutton(self.process_check_frame, fg=self.textcolor,text='Save file configuration', bg=self.bg, pady=pady,highlightthickness=0, variable=self.process_save_dir)
        self.process_save_dir_check.pack(side=LEFT, pady=(5,15))
        self.process_save_dir_check.select()
        # self.process_plot=IntVar()
        # self.process_plot_check=Checkbutton(self.process_check_frame, fg=self.textcolor,text='Plot spectra', bg=self.bg, pady=pady,highlightthickness=0)
        # self.process_plot_check.pack(side=LEFT, pady=(5,15))
        
        self.process_button=Button(self.process_frame, fg=self.textcolor,text='Process', padx=padx, pady=pady, width=int(button_width*1.6),bg='light gray', command=self.process_cmd)
        self.process_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.process_button.pack()
        
        #********************** Plot frame ******************************
        
        self.plot_frame=Frame(self.notebook, bg=self.bg, pady=2*pady)
        #self.process_frame.pack()
        self.plot_frame.pack()
        self.plot_input_frame=Frame(self.plot_frame, bg=self.bg)
        self.plot_input_frame.pack()
        self.plot_input_dir_label=Label(self.plot_frame,padx=padx,pady=pady,bg=self.bg,fg=self.textcolor,text='Path to .tsv file:')
        self.plot_input_dir_label.pack(padx=padx,pady=pady)
        self.plot_input_dir_entry=Entry(self.plot_frame, width=50,bd=bd,bg=self.entry_background)
        self.plot_input_dir_entry.insert(0, input_dir)
        self.plot_input_dir_entry.pack()
        
        # self.plot_title_frame=Frame(self.plot_frame, bg=self.bg)
        # self.plot_title_frame.pack()
        self.plot_title_label=Label(self.plot_frame,padx=padx,pady=pady,bg=self.bg,fg=self.textcolor,text='Plot title:')
        self.plot_title_label.pack(padx=padx,pady=pady)
        self.plot_title_entry=Entry(self.plot_frame, width=50,bd=bd,bg=self.entry_background)
        self.plot_title_entry.pack()
        
        # self.plot_caption_frame=Frame(self.plot_frame, bg=self.bg)
        # self.plot_caption_frame.pack()
        # self.plot_caption_label=Label(self.plot_frame,padx=padx,pady=pady,bg=self.bg,fg=self.textcolor,text='Plot caption:')
        # self.plot_caption_label.pack(padx=padx,pady=pady)
        # self.plot_caption_entry=Entry(self.plot_frame, width=50)
        # self.plot_caption_entry.pack()
        
        self.no_wr_frame=Frame(self.plot_frame, bg=self.bg)
        self.no_wr_frame.pack()
        self.no_wr=IntVar()
        self.no_wr_check=Checkbutton(self.no_wr_frame, fg=self.textcolor,text='Exclude white references', bg=self.bg, pady=pady,highlightthickness=0, variable=self.no_wr, command=self.no_wr_cmd)
        self.no_wr_check.pack(pady=(5,5))
        self.no_wr_check.select()
        
        #self.no_wr_entry=Entry(self.load_labels_frame, width=50)
        
        self.load_labels_frame=Frame(self.plot_frame, bg=self.bg)
        self.load_labels_frame.pack()
        self.load_labels=IntVar()
        self.load_labels_check=Checkbutton(self.load_labels_frame, fg=self.textcolor,text='Load labels from log file', bg=self.bg, pady=pady,highlightthickness=0, variable=self.load_labels, command=self.load_labels_cmd)
        self.load_labels_check.pack(pady=(5,5))
        
        self.load_labels_entry=Entry(self.load_labels_frame, width=50,bg=self.entry_background)
        #self.load_labels_entry.pack()
        
        
        # pr_check_frame=Frame(self.process_frame, bg=self.bg)
        # self.process_check_frame.pack(pady=(15,5))
        # self.process_save_dir=IntVar()
        # self.process_save_dir_check=Checkbutton(self.process_check_frame, fg=self.textcolor,text='Save file configuration', bg=self.bg, pady=pady,highlightthickness=0, variable=self.process_save_dir)
        # self.process_save_dir_check.pack(side=LEFT, pady=(5,15))
        # self.process_save_dir_check.select()
        # self.process_plot=IntVar()
        # self.process_plot_check=Checkbutton(self.process_check_frame, fg=self.textcolor,text='Plot spectra', bg=self.bg, pady=pady,highlightthickness=0)
        # self.process_plot_check.pack(side=LEFT, pady=(5,15))
        
        self.plot_button=Button(self.plot_frame, fg=self.textcolor,text='Plot', padx=padx, pady=pady, width=int(button_width*1.6),bg='light gray', command=self.plot)
        self.plot_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.plot_button.pack(pady=(10,5))
    
        #************************Console********************************
        self.console_frame=Frame(self.notebook, bg=self.bg)
        self.console_frame.pack(fill=BOTH, expand=True)
        self.text_frame=Frame(self.console_frame)
        self.scrollbar = Scrollbar(self.text_frame)
        self.notebook_width=self.notebook.winfo_width()
        self.notebook_height=self.notebook.winfo_width()
        self.console_log = Text(self.text_frame, width=self.notebook_width,bg=self.bg, fg=self.textcolor)
        self.scrollbar.pack(side=RIGHT, fill=Y)
    
        self.scrollbar.config(command=self.console_log.yview)
        self.console_log.configure(yscrollcommand=self.scrollbar.set)
        self.console_entry=Entry(self.console_frame, width=self.notebook_width,bd=bd,bg=self.entry_background)
        self.console_entry.bind("<Return>",self.run)
        self.console_entry.bind('<Up>',self.run)
        self.console_entry.bind('<Down>',self.run)
        self.console_entry.pack(fill=BOTH, side=BOTTOM)
        self.text_frame.pack(fill=BOTH, expand=True)
        self.console_log.pack(fill=BOTH,expand=True)
        self.console_entry.focus()
    
        self.notebook.add(self.control_frame, text='Spectrometer control')
        self.notebook.add(self.dumb_frame, text='Settings')
        self.notebook.add(self.process_frame, text='Data processing')
        self.notebook.add(self.plot_frame, text='Plot')
        self.notebook.add(self.console_frame,text='Console')
        #self.notebook.add(val_frame, fg=self.textcolor,text='Validation tools')
        #checkbox: Iterate through a range of geometries
        #checkbox: Choose a single geometry
        #checkbox: Take one spectrum
        #checkbox: Use a self.timer to collect a series of spectra
        #self.timer interval: 
        #Number of spectra to collect:
        self.notebook.pack(fill=BOTH, expand=True)
        
        #r=RemoteFileExplorer(self,write_command_loc)
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
            
    def chooselogfile(self):
        self.log_filename = askopenfilename(initialdir=log_loc,title='Select existing log file to append to')
        self.logfile_entry.delete(0,'end')
        self.logfile_entry.insert(0, self.log_filename)

        # with open(self.log_filename,'w+') as log:
        #     log.write(str(datetime.datetime.now())+'\n')
        
    def newlog(self):
        try:
            dir = asksaveasfile(mode='w', defaultextension=".txt",title='Create a new log file')
        except:
            print('this is the log')
            print('log')
        if log is None: # asksaveasfile return `None` if dialog closed with "cancel".
            return
        self.log_filename=log.name
        log.write(str(datetime.datetime.now())+'\n')
        self.logfile_entry.delete(0,'end')
        self.logfile_entry.insert(0, self.log_filename)
        
    def go(self):    
        if not self.auto.get():
            self.take_spectrum()

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
                file.write(self.spec_save_dir_entry.get()+'\n')
                file.write(self.spec_basename_entry.get()+'\n')
                file.write(self.spec_startnum_entry.get()+'\n')
             
    #If the user has failsafes activated, check that requirements are met. Always require a valid number of spectra.
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
                if self.label_entry.get()=='':
                    label +='This spectrum has no label.\n'
            onlyanglechange=False
            if label=='':
                onlyanglechange=True
            if self.anglechangefailsafe.get() and 'angle is invalid' not in label:
                print('checking')
                anglechangealert=False
                if self.e==-1000 and self.i==-1000:
                    label+='This is the first time emission and incidence angles are being set.\n'
                    anglechangealert=True
                elif self.e==-1000:
                    label+='This is the first time the emission angle is being set.\n'
                    anglechangealert=True
                    if incidence!=self.i:
                        label+='The emission angle has changed since last spectrum.\n'
                    anglechangealert=True
                elif self.i==-1000:
                    label+='This is the first time the incidence angle is being set.\n'
                    anglechangealert=True
                    if emission!=self.e:
                        label+='The emission angle has changed since last spectrum.\n' 
                    anglechangealert=True
                elif emission!=self.e and incidence !=self.i:
                    label+='The emission and incidence angles have changed since last spectrum.\n'
                    anglechangealert=True
                elif emission!=self.e:
                    label+='The emission angle has changed since last spectrum.\n'
                elif incidence!=self.i:
                    label+='The incidence angle has changed since last spectrum.\n' 
                    anglechangealert=True
                    
                if anglechangealert:#and onlyanglechange:
                   label+='The goniometer arms may need to change to match.\n'
                   pass

            if label !='': #if we came up with errors
                title='Warning!'
                
                buttons={
                    'yes':{
                        #if the user says they want to continue anyway, run take spectrum again but this time with override=True
                        func:args
                    },
                    'no':{}
                }
                label='Warning!\n\n'+label
                label+='\nDo you want to continue?'
                dialog=Dialog(self,title,label,buttons)
                return False
            else: #if there were no errors
                return True
              
    #If the user didn't choose a log file, make one in working directory
    def check_logfile(self):
        if self.log_filename==None and self.logfile_entry.get()=='':
            self.log_filename='log_'+datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')+'.txt'
            with open(self.log_filename,'w+') as log:
                log.write(str(datetime.datetime.now())+'\n')
            if opsys=='Linux':
                self.logfile_entry.insert(0,os.getcwd()+'/'+self.log_filename)
            elif opsys=='Windows':
                self.logfile_entry.insert(0,os.getcwd()+'\\'+self.log_filename)
        elif self.logfile_entry.get()!=self.log_filename:
            self.log_filename=self.logfile_entry.get()
            if not os.path.isfile(self.logfile_entry.get()):
                with open(self.log_filename,'w+') as log:
                    log.write(str(datetime.datetime.now())+'\n')
            
        
            
    def wr(self, override=False):
        #If the user didn't choose a log file, make one in working directory
        self.check_logfile()

        valid_input=True #We'll check this in a moment if override=False
        self.wr_time=int(time.time())
        if self.label_entry.get()!='' and 'White reference' not in self.label_entry.get():
            self.label_entry.insert(0, 'White reference: ')
        elif self.label_entry.get()=='':
            self.label_entry.insert(0,'White reference')

        if not override:
            valid_input=self.input_check(self.wr,[True])
            
        #If the input wasn't valid, we popped up an error dialog and now will exit. If the user clicks continue, wr will be called again with override=True
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
            
        config=self.check_save_config()
        if config:
            self.set_save_config(self.wr, [override])
            return
            
        if self.spec_config_count==None or str(new_spec_config_count) !=str(self.spec_config_count):
            
            #This is a bit weird because these aren't actually buttons. Probably could be written better. 
            buttons={
                'success':{
                    self.wr:[override]
                }
            }
            
            self.configure_instrument(buttons)
            time.sleep(5)
            print('ok done waiting')
            return

        self.model.white_reference()
        
        #This is a bit weird because these aren't actually buttons. Probably could be written better. Basically, if wr succeeds then save a spectrum. Since we already did all the required input checks, set override to True.
        buttons={
            'success':{
            
                self.take_spectrum:[True]
            }
        }
        waitdialog=WaitForWRDialog(self, buttons=buttons)
            
    def opt(self):
        self.model.opt()
        self.opt_time=int(time.time())
        self.check_logfile()
        datestring=''
        datestringlist=str(datetime.datetime.now()).split('.')[:-1]
        for d in datestringlist:
            datestring=datestring+d
        
        info_string='UNVERIFIED:\n Instrument optimized at '+datestring+'\n'
        with open(self.log_filename,'a') as log:
            log.write(info_string)
        self.console_log.insert(END, info_string)
    
    def test(self,arg=False):
        print(arg)
        
    #Check whether the current save configuration is different from the last one saved. If it is, send commands to the spec compy telling it so.
    def check_save_config(self):
        new_spec_save_dir=self.spec_save_dir_entry.get()
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
        self.check_logfile()
        
        incidence=self.man_incidence_entry.get()
        emission=self.man_emission_entry.get()

        #If the user hasn't already said they want to override input checks 1) ask whether the user has input checkboxes selected in the Settings tab and then 2)if they do, see if the inputs are valid. If they aren't all valid, create one dialog box that will list everything wrong.
        valid_input=True
        if not override:  
            valid_input=self.input_check(self.take_spectrum,[True])
            
            
        #If input isn't valid and the user asks to continue, take_spectrum will be called again with override set to True
        if not valid_input:
            return
    
        self.i=incidence
        self.e=emission

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
            
        config_timeout=0
        if self.spec_config_count==None or str(new_spec_config_count) !=str(self.spec_config_count):
            buttons={
                'success':{
                    self.take_spectrum:[override]
                }
            }
            self.configure_instrument(buttons)
            return
        if self.check_save_config():
            self.set_save_config(self.take_spectrum,[True])
            return
        startnum_str=str(self.spec_startnum_entry.get())
        while len(startnum_str)<NUMLEN:
            startnum_str='0'+startnum_str

        self.model.take_spectrum(self.man_incidence_entry.get(), self.man_emission_entry.get(),self.spec_save_path, self.spec_basename, startnum_str)
        
        
        
        
        if self.spec_save_config.get():
            file=open(self.config_loc+'/spec_save','w')
            file.write(self.spec_save_dir_entry.get()+'\n')
            file.write(self.spec_basename_entry.get()+'\n')
            file.write(self.spec_startnum_entry.get()+'\n')

            self.input_dir_entry.delete(0,'end')
            self.input_dir_entry.insert(0,self.spec_save_dir_entry.get())

        timeout=new_spec_config_count*2+20+config_timeout

        wait_dialog=WaitForSpectrumDialog(self, timeout=timeout)

        return wait_dialog
    
    def check_connection(self):
        self.connection_checker.check_connection(False)
    
    def configure_instrument(self,buttons):
        self.spec_config_count=self.instrument_config_entry.get()
        self.model.configure_instrument(self.spec_config_count)
        waitdialog=WaitForConfigDialog(self, buttons=buttons)
        
    def set_save_config(self, func, args):
        self.spec_save_path=self.spec_save_dir_entry.get()
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
        filename=filename.replace('C:\\SpecShare',self.command_share_loc)
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
                self.console_log.insert(END,'>>> '+cmd+'\n')
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
                        self.console_log.insert(END,'Error: Failed to process file.')
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
                
    def choose_spec_save_dir(self):
        r=RemoteFileExplorer(self,write_command_loc,label='Select a directory to save raw spectral data.\nThis must be in the C drive of the spectrometer control computer.', target=self.spec_save_dir_entry)
        
    def choose_process_input_dir(self):
        r=RemoteFileExplorer(self,write_command_loc,label='Select the directory containing the data you want to process.\nThis must be in the C drive of the spectrometer control computer.',target=self.input_dir_entry)
        
    def choose_process_output_dir(self):
        r=RemoteFileExplorer(self,write_command_loc,label='Select the directory where you want to save your processed data.\nThis must be in the C drive of the spectrometer control computer.',target=self.output_dir_entry)
    
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
        self.man_incidence_entry.delete(0,'end')
        self.man_emission_entry.delete(0,'end')
        self.label_entry.delete(0,'end')

    
class Dialog:
    def __init__(self, controller, title, label, buttons, width=None, height=None,allow_exit=True, button_width=30, info_string=None):
        
        self.controller=controller
        
        try:
            self.textcolor=self.controller.textcolor
            self.bg=self.controller.bg
            self.buttonbackgroundcolor=self.controller.buttonbackgroundcolor
            self.highlightbackgroundcolor=self.controller.highlightbackgroundcolor
            self.entry_background=self.controller.entry_background
            self.buttontextcolor=self.controller.buttontextcolor
            self.console_log=self.controller.console_log
            self.listboxhighlightcolor=self.controller.listboxhighlightcolor
        except:
            self.textcolor='black'
            self.bg='white'
            self.buttonbackgroundcolor='light gray'
            self.highlightbackgroundcolor='white'
            self.entry_background='white'
            self.buttontextcolor='black'
            self.console_log=None
            self.listboxhighlightcolor='light gray'
        
        #If we are starting a new master, we'll need to start a new mainloop after settin everything up. 
        #If this creates a new toplevel for an existing master, we will leave it as False.
        start_mainloop=False
        if controller==None:
            self.top=Tk()
            start_mainloop=True
            #global tk_master
            #tk_master=self.top
            self.top.configure(background=self.bg)
        else:
            if width==None or height==None:
                self.top = tk.Toplevel(controller.master, bg=self.bg)
            else:
                self.top=tk.Toplevel(controller.master, width=width, height=height, bg=self.bg)
                self.top.pack_propagate(0)
        
            self.top.grab_set()
            
       # except:
        #    print('failed to grab')

        self.label_frame=Frame(self.top, bg=self.bg)
        self.label_frame.pack(side=TOP)
        self.label = tk.Label(self.label_frame, fg=self.textcolor,text=label, bg=self.bg)
        self.set_label_text(label, info_string=info_string)
        self.label.pack(pady=(10,10), padx=(10,10))
    
        self.button_width=button_width
        self.buttons=buttons
        self.set_buttons(buttons)

        self.top.wm_title(title)
        
        if not allow_exit:
            self.top.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        if start_mainloop:
            self.top.mainloop()
            
            
    def set_label_text(self, newlabel, info_string=None):
        self.label.config(fg=self.textcolor,text=newlabel)
        if info_string != None:
            self.controller.console_log.insert(END, info_string)

    def log(self, info_string):
        if info_string[-2:-1]!='\n':
            info_string+='\n'
        self.controller.console_log.insert(END,info_string)
        
    def set_buttons(self, buttons):
        self.buttons=buttons
        
        #Sloppy way to check if button_frame already exists and reset it if it does.
        try:
            self.button_frame.destroy()
        except:
            pass
        self.button_frame=Frame(self.top, bg=self.bg)
        self.button_frame.pack(side=BOTTOM)
        self.tk_buttons=[]

        for button in buttons:
            if 'ok' in button.lower():
                self.ok_button = Button(self.button_frame, fg=self.textcolor,text='OK', command=self.ok, width=self.button_width)
                self.tk_buttons.append(self.ok_button)
                self.ok_button.pack(side=LEFT, padx=(10,10), pady=(10,10))
            elif 'yes' in button.lower():
                self.yes_button=Button(self.button_frame, fg=self.textcolor,text='Yes', bg='light gray', command=self.yes, width=self.button_width)
                self.tk_buttons.append(self.yes_button)
                self.yes_button.pack(side=LEFT, padx=(10,10), pady=(10,10))
            elif 'no' in button.lower():
                self.no_button=Button(self.button_frame, fg=self.textcolor,text='No',command=self.no, width=self.button_width)
                self.no_button.pack(side=LEFT, padx=(10,10), pady=(10,10))
                self.tk_buttons.append(self.no_button)
            elif 'cancel' in button.lower():
                self.cancel_button=Button(self.button_frame, fg=self.textcolor,text='Cancel',command=self.cancel, width=self.button_width)
                self.cancel_button.pack(side=LEFT, padx=(10,10), pady=(10,10))
                self.tk_buttons.append(self.cancel_button)
            elif 'retry' in button.lower():
                self.retry_button=Button(self.button_frame, fg=self.textcolor,text='Retry',command=self.retry, width=self.button_width)
                self.retry_button.pack(side=LEFT, padx=(10,10), pady=(10,10))
                self.tk_buttons.append(self.retry_button)
            elif 'exit' in button.lower():
                self.exit_button=Button(self.button_frame, fg=self.textcolor,text='Exit',command=self.exit, width=self.button_width)
                self.exit_button.pack(side=LEFT, padx=(10,10), pady=(10,10))
                self.tk_buttons.append(self.exit_button)
                
            for button in self.tk_buttons:
                button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
            

            # else:
            #     #For each button, only handle one function with no arguments here 
            #     #the for loop is just a way to grab the function.
            #     #It would be cool to do better than this, but it will work for now.
            #     for func in buttons[button]:
            #         print(button)
            #         print(func)
            #         tk_buttons[button]=Button(self.button_frame, fg=self.textcolor,text=button,command=func)
            #         tk_buttons[button].pack(side=LEFT, padx=(10,10),pady=(10,10))
            
    def on_closing(self):
        pass
    
    def retry(self):
        self.top.destroy()
        dict=self.buttons['retry']
        self.execute(dict,False)
        
    def exit(self):
        self.top.destroy()
        exit()

    def ok(self):
        dict=self.buttons['ok']
        self.execute(dict)
        
    def yes(self):
        dict=self.buttons['yes']
        self.execute(dict)
        
    def no(self):
        dict=self.buttons['no']
        self.execute(dict)
            
    def cancel(self):
        dict=self.buttons['cancel']
        self.execute(dict)
        
    def execute(self,dict,close=True):
        for func in dict:
            print(func)
            if len(dict[func])==0:
                func()
            elif len(dict[func])==1:
                arg=dict[func][0]
                func(arg)
            elif len(dict[func])==2:
                arg=dict[func][0]
                arg1=dict[func][1]
                func(arg,arg1)
            elif len(dict[func])==3:
                arg=dict[func][0]
                arg1=dict[func][1]
                arg2=dict[func][2]
                func(arg,arg1,arg2)
            elif len(dict[func])==4:
                arg=dict[func][0]
                arg1=dict[func][1]
                arg2=dict[func][2]
                arg3=dict[func][3]
                func(arg,arg1,arg2,arg3)
        if close:
            self.top.destroy()


class WaitDialog(Dialog):
    def __init__(self, controller, title='Working...', label='Working...', buttons={}, timeout=30):
        super().__init__(controller, title, label,buttons,width=400, height=150)
        self.listener=self.controller.listener
        
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
               
    def timeout(self, info_string=None):
        if info_string==None:
            self.set_label_text('Error: Operation timed out', info_string='Error: Operation timed out')
        else:
            self.set_label_text('Error: Operation timed out',info_string=info_string)
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

class WaitForConfigDialog(WaitDialog):
    def __init__(self, controller, title='Configuring instrument...', label='Configuring instrument...', buttons={}, timeout=200):
        super().__init__(controller, title, label,timeout=2*timeout)
        self.loc_buttons=buttons
        self.listener=self.controller.listener

    def wait(self, timeout_s):
        while self.timeout_s>0:
            self.timeout_s-=1
            time.sleep(0.5)
            if 'iconfigsuccess' in self.listener.queue:
                self.listener.queue.remove('iconfigsuccess')
                self.success()
                return
            elif 'iconfigfailure' in self.listener.queue:
                self.listener.queue.remove('iconfigfailure')
                self.failure()
                return
    def failure(self):
        print('spec config failed!')
        
    def success(self):
        datestring=''
        datestringlist=str(datetime.datetime.now()).split('.')[:-1]
        for d in datestringlist:
            datestring=datestring+d
        self.log('SUCCESS:\n Instrument configured at '+datestring+ ' with '+str(self.controller.spec_config_count))

        dict=self.loc_buttons['success']

        for func in dict:
            if len(dict[func])==1:
                arg=dict[func][0]
                func(arg)
            elif len(dict[func])==2:
                arg1=dict[func][0]
                arg2=dict[func][1]
                func(arg1,arg2)
        self.top.destroy()
        
        
class WaitForWRDialog(WaitDialog):
    def __init__(self, controller, title='White referencing...', label='White referencing...', buttons={'cancel':{}}, timeout=200):
        super().__init__(controller, title, label,timeout=2*timeout)
        self.loc_buttons=buttons
        

    def wait(self, timeout_s):
        while self.timeout_s>0:
            self.timeout_s-=1
            time.sleep(0.5)
            if 'wrsuccess' in self.controller.listener.queue:
                self.listener.queue.remove('wrsuccess')
                self.success()
                return
                
    def success(self):
        datestring=''
        datestringlist=str(datetime.datetime.now()).split('.')[:-1]
        for d in datestringlist:
            datestring=datestring+d
        self.log('SUCCESS:\n White reference saved at '+datestring+ '\n\ti='+self.controller.man_incidence_entry.get()+'\n\te='+self.controller.man_emission_entry.get())

        dict=self.loc_buttons['success']

        for func in dict:
            if len(dict[func])==1:
                arg=dict[func][0]
                func(arg)
            elif len(dict[func])==2:
                arg1=dict[func][0]
                arg2=dict[func][1]
                func(arg1,arg2)
        self.top.destroy()
            
            
class WaitForProcessDialog(WaitDialog):
    def __init__(self, controller, title='Processing...', label='Processing...', buttons={'cancel':{}}, timeout=200):
        super().__init__(controller, title, label,timeout=2*timeout)

    def wait(self, timeout_s):
        while self.timeout_s>0:
            self.timeout_s-=1
            time.sleep(0.5)
            if 'processsuccess' in self.listener.queue:
                self.listener.queue.remove('processsuccess')
                self.interrupt('Success!')
                return
                
            elif 'processerrorfileexists' in self.listener.queue:
                self.controller.listener.queue.remove('processerrorfileexists')
                self.interrupt('Error processing files: Output file already exists')
                return
                
            elif 'processerrorwropt' in self.listener.queue:
                self.listener.queue.remove('processerrorwropt')
                self.interrupt('Error processing files.\nDid you optimize and white reference before collecting data?')
                return
                
            elif 'processerror' in self.listener.queue:
                self.listener.queue.remove('processerror')
                self.interrupt('Error processing files.\nAre you sure directories exist?\n')
                return
        
class WaitForSaveConfigDialog(WaitDialog):
    def __init__(self, controller, title='Setting Save Configuration...', label='Setting save configuration...', buttons={'cancel':{}}, timeout=30):
        super().__init__(controller, title, label,timeout=2*timeout)
        self.keep_around=False
        self.loc_buttons=buttons
        self.unexpected_files=[]
        self.listener.new_dialogs=False
        
    def wait(self, timeout_s, lookforunexpected=True):
        old_files=list(self.controller.listener.saved_files)
        while 'donelookingforunexpected' not in self.listener.queue:
            time.sleep(0.25)
        if len(self.controller.listener.unexpected_files)>0:
            self.keep_around=True

        self.unexpected_files=list(self.controller.listener.unexpected_files)
        self.controller.listener.unexpected_files=[]
        self.controller.listener.new_dialogs=True
        self.controller.listener.donelookingforunexpected=False
        
        while self.timeout_s>0:
            self.timeout_s-=1
            if 'saveconfigsuccess' in self.listener.queue:
                self.listener.queue.remove('saveconfigsuccess')
                self.success()
                return
                
            elif 'saveconfigfailurefileexists' in self.listener.queue:
                self.listener.queue.remove('saveconfigfailurefileexists')
                self.interrupt('Error: File exists. Choose a different base name,\nspectrum number, or save directory and try again.', info_string='Error: failed to set save configuration because file already exists.\n')

            elif 'saveconfigfailure' in self.listener.queue:
                self.listener.queue.remove('saveconfigfailure')
                self.interrupt('Error: There was a problem with\nsetting the save configuration.\nIs the spectrometer connected?', info_string='Error: There was a problem with setting the save configuration\n')
                self.controller.spec_save_path=''
                self.controller.spec_basename=''
                self.controller.spec_num=None
                return
                
            time.sleep(0.5)
            

        
        self.timeout(info_string='Error: Operation timed out while waiting to set save configuration.\n')
        
    def success(self):
        dict=self.loc_buttons['success']
        self.log('Success: Save configuration set.\n')
        if not self.keep_around:
            self.top.destroy()
        else:
            self.pbar.stop()
            if len(self.unexpected_files)>1:
                self.set_label_text('Save configuration was set successfully,\nbut there are untracked files in the\ndata directory. Do these belong here?\n\n'+'\n'.join(self.unexpected_files))
                self.log('Untracked files in data directory:\n'+'\n\t'.join(self.unexpected_files))
            else:
                self.set_label_text('Save configuration was set successfully, but there is an\n untracked file in the data directory. Does this belong here?\n\n'+'\n'.join(self.unexpected_files))
                self.log('Untracked file in data directory:\n'+'\n\t'.join(self.unexpected_files))
            self.set_buttons({'ok':{}})
        for func in dict:
            if len(dict[func])==1:
                arg=dict[func][0]
                func(arg)
            elif len(dict[func])==2:
                arg1=dict[func][0]
                arg2=dict[func][1]
                func(arg1,arg2)
        
    def interrupt(self,label, info_string=None):
        self.interrupted=True
        self.set_label_text(label)
        self.pbar.stop()
        self.set_buttons({'ok':{}})
        self.log(info_string)
                
            
    
class WaitForSpectrumDialog(WaitDialog):
    def __init__(self, controller, title='Saving Spectrum...', label='Saving spectrum...', buttons={'cancel':{}}, timeout=30):
        super().__init__(controller, title, label, buttons={},timeout=2*timeout)
        
    def wait(self, timeout_s):
        old_files=list(self.controller.listener.saved_files)
        while self.timeout_s>0:
            self.timeout_s-=1
            if self.canceled==True:
                self.interrupt("Operation canceled by user. Warning! This really\ndoesn't do anything except stop tkinter from waiting\n, you probably still saved a spectrum")
                return
                

            if 'failedtosavefile' in self.listener.queue:
                self.interrupt('Error: Failed to save file.\nAre you sure the spectrometer is connected?')
                self.listener.queue.remove('failedtosavefile')
                return

            elif 'noconfig' in self.listener.queue:
                self.listener.queue.remove('noconfig')
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

            elif 'nonumspectra' in self.controller.listener.queue:
                self.listener.queue.remove('nonumspectra')
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
                        self.success()
                        return
        self.timeout(info_string='Error: Operation timed out while waiting to save spectrum')

        
    def success(self):
        numstr=str(self.controller.spec_num)
        while len(numstr)<NUMLEN:
            numstr='0'+numstr
        datestring=''
        datestringlist=str(datetime.datetime.now()).split('.')[:-1]
        for d in datestringlist:
            datestring=datestring+d
        info_string='SUCCESS:\n Spectrum saved at '+datestring+ '\n\ti='+self.controller.man_incidence_entry.get()+'\n\te='+self.controller.man_emission_entry.get()+'\n\tfilename='+self.controller.spec_save_path+'\\'+self.controller.spec_basename+numstr+'.asd'+'\n\tNotes: '+self.controller.label_entry.get()+'\n'
        
        self.console_log.insert(END,info_string)
        with open(self.controller.log_filename,'a') as log:
            log.write(info_string)
        self.interrupt('Success!')
        
class ErrorDialog(Dialog):
    def __init__(self, controller, title='Error', label='Error!', buttons={'ok':{}}, listener=None,allow_exit=False, info_string=None):
        self.listener=None
        if info_string==None:
            self.info_string=label+'\n'
        else:
            self.info_string=info_string
        super().__init__(controller, title, label,buttons,allow_exit=False, info_string=self.info_string)
        self.top.attributes("-topmost", True)

        


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
    

class RemoteFileExplorer(Dialog):
    def __init__(self,controller,write_command_loc, target=None,title='Select a directory',label='Select a directory',buttons={'ok':{},'cancel':{}}):

        super().__init__(controller, title=title, buttons=buttons,label=label, button_width=20)
        self.controller=controller
        self.listener=self.controller.listener
        self.write_command_loc=write_command_loc
        self.target=target
        self.current_parent=None
        
        self.nav_frame=Frame(self.top,bg=self.bg)
        self.nav_frame.pack()
        self.new_button=Button(self.nav_frame, fg=self.textcolor,text='New Folder',command=self.askfornewdir, width=10)
        self.new_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.new_button.pack(side=RIGHT, pady=(5,5),padx=(0,10))

        self.path_entry_var = StringVar()
        self.path_entry_var.trace('w', self.validate_path_entry_input)
        self.path_entry=Entry(self.nav_frame, width=40,bg=self.entry_background,textvariable=self.path_entry_var)
        self.path_entry.pack(padx=(5,5),pady=(5,5),side=RIGHT)
        self.back_button=Button(self.nav_frame, fg=self.textcolor,text='<-',command=self.back,width=1)
        self.back_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.back_button.pack(side=RIGHT, pady=(5,5),padx=(10,0))
        
        self.scroll_frame=Frame(self.top,bg=self.bg)
        self.scroll_frame.pack(fill=BOTH, expand=True)
        self.scrollbar = Scrollbar(self.scroll_frame, orient=VERTICAL)
        self.listbox = Listbox(self.scroll_frame,yscrollcommand=self.scrollbar.set, selectmode=SINGLE,bg=self.entry_background, selectbackground=self.listboxhighlightcolor)

        self.scrollbar.config(command=self.listbox.yview)
        self.scrollbar.pack(side=RIGHT, fill=Y,padx=(0,10))
        self.listbox.pack(side=LEFT,expand=True, fill=BOTH,padx=(10,0))
        self.listbox.bind("<Double-Button-1>", self.expand)
        self.path_entry.bind('<Return>',self.go_to_path)
        
        if target.get()=='':
            self.expand(newparent='C:\\Users')
            self.current_parent='C:\\Users'
        else:
            self.expand(newparent=target.get())
            
    def validate_path_entry_input(self,*args):
        text=self.path_entry.get()
        
        text=rm_reserved_chars(text)
        # if len(text)<1 or text[0]!='C':
        #     text='C'+text
        # if len(text)<2 or text[1]!=':':
        #     text='C:'+text[1:]
        # if len(text)<3 or text[2]!='\\':
        #     text='C:\\'+text[2:]
        self.path_entry.delete(0,'end')
        self.path_entry.insert(0,text)
        

        
        
        
    def askfornewdir(self):
        input_dialog=InputDialog(self.controller, self)

    def mkdir(self, newdir):
        global cmdnum
        filename=encrypt('mkdir',cmdnum, parameters=[newdir])

        cmdnum=cmdnum+1
        try:
            with open(self.write_command_loc+filename,'w+') as f:
                pass
        except:
                pass
                
        while True:
            if 'mkdirsuccess' in self.listener.queue:
                self.listener.queue.remove('mkdirsuccess')
                self.expand(None,'\\'.join(newdir.split('\\')[0:-1]))
                self.select(newdir.split('\\')[-1])
                break
            elif 'mkdirfailedfileexists' in self.listener.queue:
                self.listener.queue.remove('mkdirfailedfileexists')
                dialog=ErrorDialog(self.controller,title='Error',label='Could not create directory:\n\n'+newdir+'\n\nFile exists.')
                self.expand(newparent=self.current_parent)
                break
            elif 'mkdirfailed' in self.listener.queue:
                self.listener.queue.remove('mkdirfailed')
                dialog=ErrorDialog(self.controller,title='Error',label='Could not create directory:\n\n'+newdir)
                self.expand(newparent=self.current_parent)
                break
        time.sleep(0.5)

        
    def back(self):
        if self.path_entry.get()=='C:\\':
            return
        parent='\\'.join(self.path_entry.get().split('\\')[0:-1])
        self.path_entry.delete(0,'end')
        self.expand(newparent=parent)
        
    def go_to_path(self, source):
        parent=self.path_entry.get()
        self.path_entry.delete(0,'end')
        self.expand(newparent=parent)
        
    
    def expand(self, source=None, newparent=None, buttons=None,select=None):
        global cmdnum
        if newparent==None:
            newparent=self.current_parent+'\\'+self.listbox.get(self.listbox.curselection()[0])
        if newparent[1:3]!=':\\':
            dialog=ErrorDialog(self.controller,title='Error: Invalid input',label='Error: Invalid input.\n\n'+newparent+'\n\nis not a valid filename.')
            return
        #Send a command to the spec compy asking it for directory contents
        
        cmdfilename=encrypt('listdir',cmdnum, parameters=[newparent])
        
        cmdnum=cmdnum+1
        try:
            with open(self.write_command_loc+cmdfilename,'w+') as f:
                pass
        except:
                pass
                
        #Wait to hear what the listener finds
        while True:
            #If we get a file back with a list of the contents, replace the old listbox contents with new ones.
            if cmdfilename in self.listener.queue:
                self.listbox.delete(0,'end')
                with open(self.controller.read_command_loc+cmdfilename,'r') as f:
                    next=f.readline()
                    while next!='':
                        self.listbox.insert(END,next.strip('\n'))
                        next=f.readline()
                self.listener.queue.remove(cmdfilename)
                
                #Since we succeeded, set current parent to the new one path entry text to the new parent.
                self.current_parent=newparent
                self.path_entry.delete(0,'end')

                #newparent could be set to always have C:\\ as the first 3 characters, and those characters will already be in self.path_entry.
                #self.path_entry.insert('end',newparent[3:])

                self.path_entry.insert('end',newparent)
                if select!=None:
                    self.select(select)
                break
            elif 'listdirfailed' in self.listener.queue:
                self.listener.queue.remove('listdirfailed')
                
                if self.current_parent==None:
                    self.current_parent='C:\\Users'
                if buttons==None:
                    buttons={
                        'yes':{
                            self.mkdir:[newparent]
                        },
                        'no':{
                            self.expand:[None,self.current_parent]
                        }
                    }
                dialog=ErrorDialog(self.controller,title='Error',label=newparent+'\ndoes not exist. Do you want to create this directory?',buttons=buttons)
                
                return True
                break
            
                
            time.sleep(0.1)
    def select(self,text):
        if '\\' in text:
            text=text.split('\\')[0]
        index = self.listbox.get(0, 'end').index(text)
        self.listbox.selection_set(index)
        self.listbox.see(index)
        
    def ok(self):
        self.target.delete(0,'end')

        if len(self.listbox.curselection())>0 and self.path_entry.get()==self.current_parent:
            i=self.listbox.curselection()
            self.target.insert(0,self.current_parent+'\\'+self.listbox.get(i))
            self.top.destroy()
        elif self.path_entry.get()==self.current_parent:
            self.target.insert(0,self.current_parent)
            self.top.destroy()
        else:
            buttons={
                'yes':{
                    self.mkdir:[self.path_entry.get()],
                    self.expand:[None,'\\'.join(self.path_entry.get().split('\\')[0:-1])],
                    self.select:[self.path_entry.get().split('\\')[-1]],
                    self.ok:[]
                },
                'no':{
                }
            }
            self.expand(newparent=self.path_entry.get(), buttons=buttons)


class InputDialog(Dialog):
    def __init__(self, controller, fexplorer,label='Enter input', title='Enter input'):
        super().__init__(controller,label=label,title=title, buttons={'ok':{self.get:[]},'cancel':{}},button_width=15)
        self.dir_entry=Entry(self.top,width=40,bg=self.entry_background)
        self.dir_entry.pack(padx=(10,10))
        self.listener=self.controller.listener


        self.fexplorer=fexplorer


    def get(self):
        subdir=self.dir_entry.get()
        if subdir[0:3]!='C:\\':
            self.fexplorer.mkdir(self.fexplorer.current_parent+'\\'+subdir) 
        else:self.fexplorer.mkdir(subdir)
        
        # while True:
        #     print(self.listener.queue)
        #     if 'mkdirsuccess' in self.listener.queue:
        #         self.listener.queue.remove('mkdirsuccess')
        #         self.log('Directory created:\n\t'+self.fexplorer.current_parent+'\\'+subdir)
        #         self.top.destroy()
        #         self.fexplorer.expand(newparent=self.fexplorer.current_parent, select=subdir)
        #         return True
        #     elif 'mkdirfailed' in self.listener.queue:
        #         print('fail!')
        #         self.listener.queue.remove('mkdirfailed')
        #         self.top.destroy()
        #         dialog=ErrorDialog(self.controller,label='Error: failed to create directory.\n'+self.fexplorer.current_parent+'\\'+subdir)
        #         return False
        #     time.sleep(0.2)
        # 
        # thread = Thread(target =self.wait)
        # thread.start()  

    


class Listener(threading.Thread):
    def __init__(self, read_command_loc, test=False):
        threading.Thread.__init__(self)
        self.read_command_loc=read_command_loc
        self.saved_files=[]
        self.controller=None
        self.connection_checker=ConnectionChecker(read_command_loc,'not main',controller=self.controller)
        self.new_dialogs=True
        
        self.unexpected_files=[]
        self.donelookingforunexpected=False
        self.wait_for_unexpected_count=0
                
        self.queue=[]
    
    def run(self):
        cmdfiles0=os.listdir(self.read_command_loc)    
        while True:
            self.connection_checker.check_connection(False)
                                    
            cmdfiles=os.listdir(self.read_command_loc)
            if cmdfiles==cmdfiles0:
                pass
            else:
                for cmdfile in cmdfiles:
                    if cmdfile not in cmdfiles0:
                        cmd, params=decrypt(cmdfile)

                        print('listener sees this command: '+cmd)
                        if 'savedfile' in cmd:
                            self.saved_files.append(params[0])
                            
                        elif 'failedtosavefile' in cmd:
                            self.listener.queue.append('failedtosavefile')
                            
                        elif 'processsuccess' in cmd:
                            self.queue.append('processsuccess')
                            
                        elif 'processerrorfileexists' in cmd:
                            self.queue.append('processerrorfileexists')
                        
                        elif 'processerrorwropt' in cmd:
                            self.queue.append('processerrorwropt')
                        
                        elif 'processerror' in cmd:
                            self.queue.append('processerror')
                        
                        elif 'wrsuccess' in cmd:
                            self.queue.append('wrsuccess')
                        
                        elif 'donelookingforunexpected' in cmd:
                            self.queue.append('donelookingforunexpected')
                        
                        elif 'saveconfigerror' in cmd:
                            self.queue.append('saveconfigfailure')
                        
                        elif 'saveconfigsuccess' in cmd:
                            self.queue.append('saveconfigsuccess')
                        
                        elif 'noconfig' in cmd:
                            print("Spectrometer computer doesn't have a file configuration saved (python restart over there?). Setting to current configuration.")
                            self.queue.append('noconfig')
                        
                        elif 'nonumspectra' in cmd:
                            print("Spectrometer computer doesn't have an instrument configuration saved (python restart over there?). Setting to current configuration.")
                            self.queue.append('noconfig')
                        
                        elif 'saveconfigfailedfileexists' in cmd:
                            self.queue.append('saveconfigfailurefileexists')
                        elif 'savespecfailedfileexists' in cmd:
                            self.queue.append('savespecfailedfileexists')
                        
                        elif 'listdir' in cmd:
                            if 'listdirfailed' in cmd:
                                self.queue.append('listdirfailed')
                            else:
                                self.queue.append(cmdfile)                        
                       
                        elif 'mkdirsuccess' in cmd:
                            self.queue.append('mkdirsuccess')
                       
                        elif 'mkdirfailedfileexists' in cmd:
                            self.queue.append('mkdirfailedfileexists')
                        elif 'mkdirfailed' in cmd:
                            self.queue.append('mkdirfailed')
                        
                        elif 'iconfigsuccess' in cmd:
                            self.queue.append('iconfigsuccess')
                        
                        elif 'iconfigfailure' in cmd:
                            self.queue.append('iconfigfailure')
                        
                        elif 'unexpectedfile' in cmd:
                            if self.new_dialogs:
                                try:
                                    dialog=ErrorDialog(self.controller, title='Untracked Files',label='There is an untracked file in the data directory.\nDoes this belong here?\n\n'+params[0])
                                except:
                                    print('Ignoring an error in Listener when I make a new error dialog')
                            else:
                                self.unexpected_files.append(params[0])
                        else:
                            print('unexpected cmd: '+cmdfile)
                #This line always prints twice if it's uncommented, I'm not sure why.
                #print('forward!')

            cmdfiles0=list(cmdfiles)
                            
            time.sleep(0.5)
    
    def set_controller(self,controller):
        self.controller=controller
            
    def find_file(path):
        i=0
        found=False
        while i<10 and found==False:
            if path in self.saved_files:
                found=True
            i=i+1
        return found
        
def decrypt(encrypted):
    cmd=encrypted.split('&')[0]
    params=encrypted.split('&')[1:]
    i=0
    for param in params:
        params[i]=param.replace('+','\\').replace('=',':')
        params[i]=params[i].replace('++','+')
        i=i+1
    return cmd,params
    
def encrypt(cmd, num, parameters=[]):
    print(num)
    filename=cmd+str(num)
    for param in parameters:
        param=param.replace('/','+')
        param=param.replace('\\','+')
        param=param.replace(':','=')
        filename=filename+'&'+param
    return filename
    
def rm_reserved_chars(input):
    return input.strip('&').strip('+').strip('=')


if __name__=='__main__':
    main()