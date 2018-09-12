#The controller runs the main thread controlling the program.
#It creates and starts a View object, which extends Thread and will show a pygame window.

dev=True
test=True
online=False
computer='new'

import os
import sys
import platform

global OFFLINE
OFFLINE=False

from tkinter import *
from tkinter import messagebox
importlib=True
try:
    import importlib
except:
    importlib=False
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


import http.client as httplib

#Which computer are you using? This should probably be new. I don't know why you would use the old one.
computer='new'

#Figure out where this file is hanging out and tell python to look there for custom modules. This will depend on what operating system you are using.

global opsys
opsys=platform.system()
if opsys=='Darwin': opsys='Mac' #For some reason Macs identify themselves as Darwin. I don't know why but I think this is more intuitive.

global package_loc
package_loc=''

global CMDNUM
CMDNUM=0

global INTERVAL
INTERVAL=0.25

if opsys=='Windows':
    #If I am running this script from my IDE, __file__ is not defined. In that case, I'll get an exception, and I'll go with my own hard-coded file location instead.
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
    #If I am running this script from my IDE, __file__ is not defined. In that case, I'll get an exception, and I'll go with my own hard-coded file location instead.
    try:
        rel_package_loc='/'.join(__file__.split('/')[:-1])+'/'
        if rel_package_loc[0]=='/':
            package_loc=rel_package_loc
        else: package_loc=os.getcwd()+'/'+rel_package_loc
    except:
        print('Developer mode!')
        dev=True
        package_loc='/home/khoza/Python/WWU-AutoSpec/wwu-autospec/'
elif opsys=='Mac':
    try:
        rel_package_loc='/'.join(__file__.split('/')[:-1])+'/'
        if rel_package_loc[0]=='/':
            package_loc=rel_package_loc
        else: package_loc=os.getcwd()+'/'+rel_package_loc
    except:
        print('Developer mode!')
        dev=True
        package_loc='/home/khoza/Python/WWU-AutoSpec/wwu-autospec/'
    
sys.path.append(package_loc)

#import goniometer_model
import goniometer_view
import plotter

#This is needed because otherwise changes won't show up until you restart the shell. Not needed if you aren't changing the modules.
if dev:
    try:
        # importlib.reload(goniometer_model)
        # from goniometer_model import Model
        importlib.reload(goniometer_view)
        from goniometer_view import View
        from goniometer_view import TestView
        from goniometer_view import TestViewOld
        importlib.reload(plotter)
        from plotter import Plotter
    except:
        print('Not reloading modules')
#Server and share location. Can change if spectroscopy computer changes.
server=''
global NUMLEN
global tk_master
tk_master=None

NUMLEN=500
if computer=='old':
    #Number of digits in spectrum number for spec save config
    NUMLEN=3
    #Time added to timeouts to account for time to read/write files
    BUFFER=15
    server='melissa' #old computer
elif computer=='new':
    #Number of digits in spectrum number for spec save config
    NUMLEN=5
    #Time added to timeouts to account for time to read/write files
    BUFFER=15
    server='geol-chzc5q2' #new computer

pi_server='hozapi'
spec_share='specshare'
spec_share_Mac='SpecShare'
data_share='users' #Not used. Maybe later?
data_share_Mac='Users'
pi_share='pishare'
pi_share_Mac='PiShare'

if opsys=='Linux':
    spec_share_loc='/run/user/1000/gvfs/smb-share:server='+server+',share='+spec_share+'/'
    data_share_loc='/run/user/1000/gvfs/smb-share:server='+server+',share='+data_share+'/'
    pi_share_loc='/run/user/1000/gvfs/smb-share:server='+pi_server+',share='+pi_share+'/'
    delimiter='/'
    spec_write_loc=spec_share_loc+'commands/from_control/'
    pi_write_loc=pi_share_loc+'commands/from_control/'
    spec_read_loc=spec_share_loc+'commands/from_spec/'
    pi_read_loc=pi_share_loc+'/commands/from_pi/'
    config_loc=package_loc+'config/'
    log_loc=package_loc+'log/'
elif opsys=='Windows':
    spec_share_loc='\\\\'+server.upper()+'\\'+spec_share+'\\'
    pi_share_loc='\\\\'+server.upper()+'\\'+pi_share+'\\'
    data_share_loc='\\\\'+server.upper()+'\\'+data_share+'\\'
    spec_write_loc=spec_share_loc+'commands\\from_control\\'
    pi_write_loc=pi_share_loc+'commands\\from_control\\'
    spec_read_loc=spec_share_loc+'commands\\from_spec\\'
    pi_read_loc=pi_share_loc+'commands\\from_spec\\'
    config_loc=package_loc+'config\\'
    log_loc=package_loc+'log\\'
elif opsys=='Mac':
    spec_share_loc='/Volumes/'+spec_share_Mac+'/'
    pi_share_loc='/Volumes/'+pi_share_Mac+'/'
    data_share_loc='/Volumes/'+data_share_Mac+'/'
    delimiter='/'
    spec_write_loc=spec_share_loc+'commands/from_control/'
    pi_write_loc=pi_share_loc+'commands/from_control/'
    spec_read_loc=spec_share_loc+'commands/from_spec/'
    pi_read_loc=pi_share_loc+'commands/from_spec/'
    config_loc=package_loc+'config/'
    log_loc=package_loc+'log/'
    
if not os.path.isdir(config_loc):
    print(config_loc)
    os.mkdir(config_loc)

def donothing():
    pass
def exit_func():
    print('exit!')
    exit()
    
def retry_func():
     os.execl(sys.executable, os.path.abspath(__file__), *sys.argv) 

def main():
    #Check if you are connected to the server. 
    print('part 1')
    spec_connection_checker=SpecConnectionChecker(spec_read_loc, func=main_part_2)
    connected = spec_connection_checker.check_connection(True)

def main_part_2():
    print('part 2!')
    pi_connection_checker=PiConnectionChecker(pi_read_loc, func=main_part_3)
    connected=pi_connection_checker.check_connection(True)

def main_part_3():
    print('part 3!')
    #Clean out your read and write directories for commands. Prevents confusion based on past instances of the program.
    if not OFFLINE:
        delme=os.listdir(spec_write_loc)
        for file in delme:
            os.remove(spec_write_loc+file)
        delme=os.listdir(spec_read_loc)
        for file in delme:
            os.remove(spec_read_loc+file)
    
        delme=os.listdir(pi_write_loc)
        for file in delme:
            os.remove(pi_write_loc+file)
        delme=os.listdir(pi_read_loc)
        for file in delme:
            os.remove(pi_read_loc+file)
    
    #Create a listener, which listens for commands, and a controller, which manages the model (which writes commands) and the view.
    #spec_listener=SpecListener(spec_read_loc)
    spec_listener=SpecListener(spec_read_loc)
    pi_listener=PiListener(pi_read_loc)

    icon_loc=package_loc+'exception'#test_icon.xbm'
    control=Controller(spec_listener, pi_listener,spec_share_loc, spec_read_loc,spec_write_loc, pi_write_loc, config_loc,data_share_loc,opsys, icon_loc)

class Controller():
    def __init__(self, spec_listener, pi_listener,spec_share_loc, spec_read_loc, spec_write_loc, pi_write_loc,config_loc, data_share_loc,opsys,icon):
        self.spec_listener=spec_listener
        self.spec_listener.set_controller(self)
        self.spec_listener.start()
        
        self.pi_listener=pi_listener
        self.pi_listener.set_controller(self)
        self.pi_listener.start()
        
        self.data_share_loc=data_share_loc
        self.spec_read_loc=spec_read_loc
        self.spec_share_loc=spec_share_loc
        self.spec_write_loc=spec_write_loc
        self.pi_write_loc=pi_write_loc
        self.spec_commander=SpecCommander(self.spec_write_loc)
        self.pi_commander=PiCommander(self.pi_write_loc)
        
        self.remote_directory_worker=RemoteDirectoryWorker(self.spec_commander, self.spec_read_loc, self.spec_listener)
        
        self.config_loc=config_loc
        self.opsys=opsys
        self.log_filename=None
        
        
        #The queue is a list of dictionaries commands:parameters
        #The commands are supposed to be executed in order, assuming each one succeeds.
        #CommandHandlers tell the controller when it's time to do the next one
        self.queue=[]
        
        #One wait dialog open at a time. CommandHandlers check whether to use an existing one or make a new one.
        self.wait_dialog=None
        
        # try:
        #     with open(self.config_loc+'geom','r') as f:
        #         self.last_i=int(f.readline().strip('\n'))
        #         self.last_e=int(f.readline().strip('\n'))
        # except:
        #     self.last_i=None
        #     self.last_e=None
        
        self.min_i=-50
        self.max_i=50
        self.i=None
        self.final_i=None
        self.i_interval=None
        
        self.min_e=-75
        self.max_e=75
        self.e=None
        self.final_e=None
        self.e_interval=None
        
        self.required_angular_separation=15
        
        
        
        #These will get set via user input.
        self.spec_save_path=''
        self.spec_basename=''
        self.spec_num=None
        self.spec_config_count=None
        self.take_spectrum_with_bad_i_or_e=False
        self.wr_time=None
        self.opt_time=None
        self.angles_change_time=None
        self.current_label=''
        self.i_e_pair_frames=[]
        self.incidence_entries=[]
        self.incidence_labels=[]
        self.emission_entries=[]
        self.emission_labels=[]
        self.active_incidence_entries=[]
        self.active_emission_entries=[]
        self.active_i_e_pair_frames=[]
        self.i_e_removal_buttons=[]
        
        
        #Yay formatting. Might not work for Macs.
        self.bg='#333333'
        self.textcolor='light gray'
        self.buttontextcolor='white'
        self.bd=2
        self.padx=3
        self.pady=3
        self.border_color='light gray'
        self.button_width=15
        self.buttonbackgroundcolor='#888888'
        self.highlightbackgroundcolor='#222222'
        self.entry_background='light gray'
        self.listboxhighlightcolor='white'
        self.selectbackground='#555555'
        self.selectforeground='white'
        self.check_bg='#444444'
        
        
        #Tkinter notebook GUI
        self.master=Tk()
        self.master.configure(background = self.bg)

        self.master.title('Control')
        self.master.minsize(1050,750)
        #When the window closes, send a command to set the geometry to i=0, e=30.
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.tk_master=self.master #this gets used when deciding whether to open a new master when giving a no connection dialog or something. I can't remember. 
        self.notebook_frame=Frame(self.master)
        self.notebook_frame.pack(side=LEFT,fill=BOTH, expand=True)
        self.notebook=ttk.Notebook(self.notebook_frame)
        self.tk_buttons=[]
        self.entries=[]
        self.radiobuttons=[]
        
        #view_frame=Frame(self.master)
        self.test_view=TestView(self)

        #The plotter, surprisingly, plots things.
        self.plotter=Plotter(self.master)
        
        
        #The commander is in charge of sending all the commands for the spec compy to read


        #If the user has saved spectra with this program before, load in their previously used directories.
        input_dir=''
        output_dir=''
        try:
            with open(self.config_loc+'process_directories.txt','r') as process_config:
                input_dir=process_config.readline().strip('\n')
                output_dir=process_config.readline().strip('\n')
        except:
            with open(self.config_loc+'process_directories.txt','w+') as f:
                f.write('C:\\Users\n')
                f.write('C:\\Users\n')

            input_dir='C:\\Users'
            output_dir='C:\\Users'
    
        try:
            with open(self.config_loc+'spec_save.txt','r') as spec_save_config:
                self.spec_save_path=spec_save_config.readline().strip('\n')
                self.spec_basename=spec_save_config.readline().strip('\n')
                self.spec_startnum=str(int(spec_save_config.readline().strip('\n'))+1)
                while len(self.spec_startnum)<NUMLEN:
                    self.spec_startnum='0'+self.spec_startnum
        except:
            with open(self.config_loc+'spec_save.txt','w+') as f:
                f.write('C:\\Users\n')
                f.write('basename\n')
                f.write('-1\n')

                self.spec_save_path='C:\\Users'
                self.spec_basename='basename'
                self.spec_startnum='0'
                while len(self.spec_startnum)<NUMLEN:
                    self.spec_startnum='0'+self.spec_startnum
        self.notebook_frames=[]
        self.control_frame=Frame(self.notebook, bg=self.bg)
        self.notebook_frames.append(self.control_frame)
        self.control_frame.pack()
        self.save_config_frame=Frame(self.control_frame,bg=self.bg,highlightthickness=1)
        self.save_config_frame.pack(fill=BOTH,expand=True)
        self.spec_save_label=Label(self.save_config_frame,padx=self.padx,pady=self.pady,bg=self.bg,fg=self.textcolor,text='Spectra save configuration:')
        self.spec_save_label.pack(pady=(15,5))
        self.spec_save_path_label=Label(self.save_config_frame,padx=self.padx,pady=self.pady,bg=self.bg,fg=self.textcolor,text='Directory:')
        self.spec_save_path_label.pack(padx=self.padx)
        
        self.spec_save_dir_frame=Frame(self.save_config_frame,bg=self.bg)
        self.spec_save_dir_frame.pack()
        
        self.spec_save_dir_browse_button=Button(self.spec_save_dir_frame,text='Browse',command=self.choose_spec_save_dir)
        self.tk_buttons.append(self.spec_save_dir_browse_button)
        self.spec_save_dir_browse_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.spec_save_dir_browse_button.pack(side=RIGHT, padx=(3,15))
        
        self.spec_save_dir_var = StringVar()
        self.spec_save_dir_var.trace('w', self.validate_spec_save_dir)
        self.spec_save_dir_entry=Entry(self.spec_save_dir_frame, width=50,bd=self.bd,bg=self.entry_background, selectbackground=self.selectbackground,selectforeground=self.selectforeground,textvariable=self.spec_save_dir_var)
        self.entries.append(self.spec_save_dir_entry)
        self.spec_save_dir_entry.insert(0, self.spec_save_path)
        self.spec_save_dir_entry.pack(padx=(15,5), pady=self.pady, side=RIGHT)
        self.spec_save_frame=Frame(self.save_config_frame, bg=self.bg)
        self.spec_save_frame.pack()
        
        self.spec_basename_label=Label(self.spec_save_frame,pady=self.pady,bg=self.bg,fg=self.textcolor,text='Base name:')
        self.spec_basename_label.pack(side=LEFT,pady=(5,15),padx=(0,0))
        
        self.spec_basename_var = StringVar()
        self.spec_basename_var.trace('w', self.validate_basename)
        self.spec_basename_entry=Entry(self.spec_save_frame, width=10,bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground,textvariable=self.spec_basename_var)
        self.entries.append(self.spec_basename_entry)
        self.spec_basename_entry.pack(side=LEFT,padx=(5,5), pady=self.pady)
        self.spec_basename_entry.insert(0,self.spec_basename)
        

        
        self.spec_startnum_label=Label(self.spec_save_frame,padx=self.padx,pady=self.pady,bg=self.bg,fg=self.textcolor,text='Number:')
        self.spec_startnum_label.pack(side=LEFT,pady=self.pady)
        
        self.startnum_var = StringVar()
        self.startnum_var.trace('w', self.validate_startnum)
        self.spec_startnum_entry=Entry(self.spec_save_frame, width=10,bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground,textvariable=self.startnum_var)
        self.entries.append(self.spec_startnum_entry)
        self.spec_startnum_entry.insert(0,self.spec_startnum)
        self.spec_startnum_entry.pack(side=RIGHT, pady=self.pady)      
        

            
        self.log_frame=Frame(self.control_frame, bg=self.bg,highlightthickness=1)
        self.log_frame.pack(fill=BOTH,expand=True)
        self.logfile_label=Label(self.log_frame,padx=self.padx,pady=self.pady,bg=self.bg,fg=self.textcolor,text='Log file:')
        self.logfile_label.pack(padx=self.padx,pady=(10,0))
        self.logfile_entry_frame=Frame(self.log_frame, bg=self.bg)
        self.logfile_entry_frame.pack()
        
        self.logfile_var = StringVar()
        self.logfile_var.trace('w', self.validate_logfile)
        self.logfile_entry=Entry(self.logfile_entry_frame, width=50,bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground,textvariable=self.logfile_var)
        self.entries.append(self.logfile_entry)
        self.logfile_entry.pack(padx=self.padx, pady=(5,15))
        self.logfile_entry.enabled=False
        

        
        self.select_logfile_button=Button(self.logfile_entry_frame, fg=self.textcolor,text='Select existing',command=self.chooselogfile, width=13, height=1,bg=self.buttonbackgroundcolor)
        self.tk_buttons.append(self.select_logfile_button)
        self.select_logfile_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor)
        self.select_logfile_button.pack(side=LEFT,padx=(50,5), pady=(0,10))
        
        self.new_logfile_button=Button(self.logfile_entry_frame, fg=self.textcolor,text='New log file',command=self.newlog, width=13, height=1)
        self.tk_buttons.append(self.new_logfile_button)
        self.new_logfile_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.new_logfile_button.pack(side=LEFT,padx=self.padx, pady=(0,10))
        
        self.spec_save_config=IntVar()
        self.spec_save_config_check=Checkbutton(self.save_config_frame, fg=self.textcolor,text='Save file configuration', bg=self.bg, pady=self.pady,highlightthickness=0, variable=self.spec_save_config, selectcolor=self.check_bg)
        #self.spec_save_config_check.pack(pady=(0,5))
        self.spec_save_config_check.select()
        


        
        
        self.instrument_config_frame=Frame(self.control_frame, bg=self.bg, highlightthickness=1)
        self.spec_settings_label=Label(self.instrument_config_frame,padx=self.padx,pady=self.pady,bg=self.bg,fg=self.textcolor,text='Instrument Configuration:')
        self.spec_settings_label.pack(padx=self.padx,pady=(10,10))
        self.instrument_config_frame.pack(fill=BOTH,expand=True)
        self.i_config_label_entry_frame=Frame(self.instrument_config_frame,bg=self.bg)
        self.i_config_label_entry_frame.pack()
        self.instrument_config_label=Label(self.i_config_label_entry_frame, fg=self.textcolor,text='Number of spectra to average:', bg=self.bg)
        self.instrument_config_label.pack(side=LEFT,padx=(20,0))
        self.instrument_config_entry=Entry(self.i_config_label_entry_frame, width=10, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.entries.append(self.instrument_config_entry)
        self.instrument_config_entry.insert(0, 5)
        self.instrument_config_entry.pack(side=LEFT)
        

        # self.viewing_geom_options_frame_top=Frame(self.control_frame,bg=self.bg)
        # self.viewing_geom_options_frame_top.pack(fill=BOTH,expand=True)     
        # self.viewing_geom_options_label=Label(self.viewing_geom_options_frame_top,text='Viewing geometry options:', fg=self.textcolor, bg=self.bg)
        # self.viewing_geom_options_label.pack(pady=(15,0))
        self.viewing_geom_options_frame=Frame(self.control_frame,bg=self.bg)
        self.viewing_geom_options_frame.pack(fill=BOTH,expand=True)
        
        self.viewing_geom_options_frame_left=Frame(self.viewing_geom_options_frame, bg=self.bg,highlightthickness=1)
        self.viewing_geom_options_frame_left.pack(side=LEFT,fill=BOTH,expand=True)
        

        
        self.single_mult_frame=Frame(self.viewing_geom_options_frame,bg=self.bg,highlightthickness=1)
        self.single_mult_frame.pack(side=RIGHT, fill=BOTH,expand=True)
        self.angle_control_label=Label(self.single_mult_frame,text='Geometry specification:      ',bg=self.bg, fg=self.textcolor)
        self.angle_control_label.pack(padx=(5,5),pady=(10,5))
        
        self.individual_range=IntVar()
        self.individual_radio=Radiobutton(self.single_mult_frame, text='Individual         ',bg=self.bg,fg=self.textcolor,highlightthickness=0,variable=self.individual_range,value=0,selectcolor=self.check_bg,command=self.set_individual_range)
        self.radiobuttons.append(self.individual_radio)
        self.individual_radio.pack()
        
        self.range_radio=Radiobutton(self.single_mult_frame, text='Range with interval\n(Automatic only)',bg=self.bg, fg=self.textcolor,highlightthickness=0,variable=self.individual_range,value=1,selectcolor=self.check_bg,command=self.set_individual_range)
        self.radiobuttons.append(self.range_radio)
        self.range_radio.configure(state = DISABLED)
        self.range_radio.pack()
        
        self.gon_control_label_frame=Frame(self.viewing_geom_options_frame_left, bg=self.bg)
        self.gon_control_label_frame.pack()
        self.gon_control_label=Label(self.gon_control_label_frame,text='\nGoniometer control:         ',bg=self.bg, fg=self.textcolor)
        self.gon_control_label.pack(side=LEFT,padx=(10,5))
        
        self.manual_radio_frame=Frame(self.viewing_geom_options_frame_left, bg=self.bg)
        self.manual_radio_frame.pack()
        self.manual_automatic=IntVar()
        self.manual_radio=Radiobutton(self.manual_radio_frame,text='Manual            ',bg=self.bg,fg=self.textcolor,highlightthickness=0,variable=self.manual_automatic, value=0,selectcolor=self.check_bg,command=self.set_manual_automatic)
        self.radiobuttons.append(self.manual_radio)
        self.manual_radio.pack(side=LEFT,padx=(10,10),pady=(5,5))
        
        self.automation_radio_frame=Frame(self.viewing_geom_options_frame_left, bg=self.bg)
        self.automation_radio_frame.pack()
        self.automation_radio=Radiobutton(self.automation_radio_frame,text='Automatic         ',bg=self.bg,fg=self.textcolor,highlightthickness=0,variable=self.manual_automatic,value=1,selectcolor=self.check_bg,command=self.set_manual_automatic)
        self.radiobuttons.append(self.automation_radio)
        self.automation_radio.pack(side=LEFT,padx=(10,10))
        self.filler_label=Label(self.viewing_geom_options_frame_left,text='',bg=self.bg)
        self.filler_label.pack()

        
        
        self.viewing_geom_frame=Frame(self.control_frame,bg=self.bg, highlightthickness=1)
        self.viewing_geom_frame.pack(fill=BOTH,expand=True)     

        self.viewing_geom_options_label=Label(self.viewing_geom_frame,text='Viewing geometry:', fg=self.textcolor, bg=self.bg)
        self.viewing_geom_options_label.pack(pady=(15,10))
        
        self.individual_angles_frame=Frame(self.viewing_geom_frame, bg=self.bg,highlightbackground=self.border_color)
        self.individual_angles_frame.pack()
        self.add_i_e_pair()


        
        self.range_frame=Frame(self.viewing_geom_frame,padx=self.padx,pady=self.pady,bd=2,highlightbackground=self.border_color,highlightcolor=self.border_color,highlightthickness=0,bg=self.bg)
        #self.range_frame.pack()
        self.light_frame=Frame(self.range_frame,bg=self.bg)
        self.light_frame.pack(side=LEFT,padx=(5,30))
        self.light_label=Label(self.light_frame,padx=self.padx, pady=self.pady,bg=self.bg,fg=self.textcolor,text='Incidence angles:')
        self.light_label.pack()
        
        light_labels_frame = Frame(self.light_frame,bg=self.bg,padx=self.padx,pady=self.pady)
        light_labels_frame.pack(side=LEFT)
        
        light_start_label=Label(light_labels_frame,padx=self.padx,pady=self.pady,bg=self.bg,fg=self.textcolor,text='Next:')
        light_start_label.pack(pady=(0,8))
        light_end_label=Label(light_labels_frame,bg=self.bg,padx=self.padx,pady=self.pady,fg=self.textcolor,text='Last:')
        light_end_label.pack(pady=(0,5))
    
        light_increment_label=Label(light_labels_frame,bg=self.bg,padx=self.padx,pady=self.pady,fg=self.textcolor,text='Increment:')
        light_increment_label.pack(pady=(0,5))
    
        
        light_entries_frame=Frame(self.light_frame,bg=self.bg,padx=self.padx,pady=self.pady)
        light_entries_frame.pack(side=RIGHT)
        
        self.light_start_entry=Entry(light_entries_frame,width=10, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.entries.append(self.light_start_entry)
        self.light_start_entry.pack(padx=self.padx,pady=self.pady)
        
        self.light_end_entry=Entry(light_entries_frame,width=10, highlightbackground='white', bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.entries.append(self.light_end_entry)
        self.light_end_entry.pack(padx=self.padx,pady=self.pady)    
        self.light_increment_entry=Entry(light_entries_frame,width=10,highlightbackground='white', bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.entries.append(self.light_increment_entry)
        self.light_increment_entry.pack(padx=self.padx,pady=self.pady)
        
        detector_frame=Frame(self.range_frame,bg=self.bg)
        detector_frame.pack(side=RIGHT)
        
        detector_label=Label(detector_frame,padx=self.padx, pady=self.pady,bg=self.bg,fg=self.textcolor,text='Emission angles:')
        detector_label.pack()
        
        detector_labels_frame = Frame(detector_frame,bg=self.bg,padx=self.padx,pady=self.pady)
        detector_labels_frame.pack(side=LEFT,padx=(30,5))
        
        detector_start_label=Label(detector_labels_frame,padx=self.padx,pady=self.pady,bg=self.bg,fg=self.textcolor,text='Next:')
        detector_start_label.pack(pady=(0,8))
        detector_end_label=Label(detector_labels_frame,bg=self.bg,padx=self.padx,pady=self.pady,fg=self.textcolor,text='Last:')
        detector_end_label.pack(pady=(0,5))
    
        detector_increment_label=Label(detector_labels_frame,bg=self.bg,padx=self.padx,pady=self.pady,fg=self.textcolor,text='Increment:')
        detector_increment_label.pack(pady=(0,5))
    
        
        detector_entries_frame=Frame(detector_frame,bg=self.bg,padx=self.padx,pady=self.pady)
        detector_entries_frame.pack(side=RIGHT)
        self.detector_start_entry=Entry(detector_entries_frame,bd=self.bd,width=10,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.entries.append(self.detector_start_entry)
        self.detector_start_entry.pack(padx=self.padx,pady=self.pady)
        
        self.detector_end_entry=Entry(detector_entries_frame,bd=self.bd,width=10,highlightbackground='white',bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.entries.append(self.detector_end_entry)
        self.detector_end_entry.pack(padx=self.padx,pady=self.pady)
        
        self.detector_increment_entry=Entry(detector_entries_frame,bd=self.bd,width=10, highlightbackground='white',bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.entries.append(self.detector_increment_entry)
        self.detector_increment_entry.pack(padx=self.padx,pady=self.pady)
        
        
        self.spectrum_label_frame=Frame(self.control_frame,bg=self.bg, highlightthickness=1)
        self.spectrum_label_frame.pack(fill=BOTH,expand=True)
        self.label_label=Label(self.spectrum_label_frame, padx=self.padx,pady=self.pady,bg=self.bg, fg=self.textcolor,text='Label for this sample:')
        self.label_label.pack(pady=(10,10))
        self.label_entry=Entry(self.spectrum_label_frame, width=50, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.entries.append(self.label_entry)
        self.label_entry.pack(pady=(0,15))

        
        # self.auto_check_frame=Frame(self.control_frame, bg=self.bg)
        # self.auto_process=IntVar()
        # self.auto_process_check=Checkbutton(self.auto_check_frame, fg=self.textcolor,text='Process data', bg=self.bg, highlightthickness=0,selectcolor=self.check_bg)
        # self.auto_process_check.pack(side=LEFT)
        
        # self.auto_plot=IntVar()
        # self.auto_plot_check=Checkbutton(self.auto_check_frame, fg=self.textcolor,text='Plot spectra', bg=self.bg, highlightthickness=0,selectcolor=self.check_bg)
        # self.auto_plot_check.pack(side=LEFT)
        # 
        self.gen_frame=Frame(self.control_frame, bg=self.bg,highlightthickness=1)
        self.gen_frame.pack(fill=BOTH,expand=True)
        
        self.action_button_frame=Frame(self.gen_frame, bg=self.bg)
        self.action_button_frame.pack()
        
        button_width=20
        self.opt_button=Button(self.action_button_frame, fg=self.textcolor,text='Optimize', padx=self.padx, pady=self.pady,width=self.button_width, bg='light gray', command=self.opt_button_cmd, height=2)
        self.tk_buttons.append(self.opt_button)
        self.opt_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.opt_button.pack(padx=self.padx,pady=self.pady, side=LEFT)
        self.wr_button=Button(self.action_button_frame, fg=self.textcolor,text='White Reference', padx=self.padx, pady=self.pady, width=self.button_width, bg='light gray', command=self.wr_button_cmd, height=2)
        self.tk_buttons.append(self.wr_button)
        self.wr_button.pack(padx=self.padx,pady=self.pady, side=LEFT)
        self.wr_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
    
        self.spec_button=Button(self.action_button_frame, fg=self.textcolor,text='Take Spectrum', padx=self.padx, pady=self.pady, width=self.button_width,height=2,bg='light gray', command=self.spec_button_cmd)
        self.tk_buttons.append(self.spec_button)
        self.spec_button.pack(padx=self.padx,pady=self.pady, side=LEFT)
        self.spec_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        
        self.acquire_button=Button(self.action_button_frame, fg=self.textcolor,text='Acquire Data', padx=self.padx, pady=self.pady, width=self.button_width,height=2,bg='light gray', command=self.acquire)
        self.tk_buttons.append(self.acquire_button)
        self.acquire_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        
        #***************************************************************
        
        self.dumb_frame=Frame(self.notebook, bg=self.bg, pady=2*self.pady)
        self.dumb_frame.pack()

        self.timer_title_frame=Frame(self.dumb_frame, bg=self.bg)
        self.timer_title_frame.pack(pady=(10,0))
        self.timer_label0=Label(self.timer_title_frame, fg=self.textcolor,text='Timer:                                                   ', bg=self.bg)
        self.timer_label0.pack(side=LEFT)
        self.timer_frame=Frame(self.dumb_frame, bg=self.bg, pady=self.pady)
        self.timer_frame.pack()
        self.timer_check_frame=Frame(self.timer_frame, bg=self.bg)
        self.timer_check_frame.pack(pady=self.pady)
        self.timer=IntVar()
        self.timer_check=Checkbutton(self.timer_check_frame, fg=self.textcolor,text='Collect sets of spectra using a timer           ', bg=self.bg, pady=self.pady,highlightthickness=0, variable=self.timer,selectcolor=self.check_bg)
        self.timer_check.pack(side=LEFT, pady=self.pady)
        
        self.timer_duration_frame=Frame(self.timer_frame, bg=self.bg)
        self.timer_duration_frame.pack()
        self.timer_spectra_label=Label(self.timer_duration_frame,padx=self.padx,pady=self.pady,bg=self.bg,fg=self.textcolor,text='Total duration (min):')
        self.timer_spectra_label.pack(side=LEFT, padx=self.padx,pady=(0,8))
        self.timer_spectra_entry=Entry(self.timer_duration_frame, bd=1,width=10,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.timer_spectra_entry.pack(side=LEFT)
        self.filler_label=Label(self.timer_duration_frame,bg=self.bg,fg=self.textcolor,text='              ')
        self.filler_label.pack(side=LEFT)
        
        self.timer_interval_frame=Frame(self.timer_frame, bg=self.bg)
        self.timer_interval_frame.pack()
        self.timer_interval_label=Label(self.timer_interval_frame, padx=self.padx,pady=self.pady,bg=self.bg, fg=self.textcolor,text='Interval (min):')
        self.timer_interval_label.pack(side=LEFT, padx=(10,0))
        self.timer_interval_entry=Entry(self.timer_interval_frame,bd=self.bd,width=10,fg=self.textcolor,text='0',bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
    # self.timer_interval_entry.insert(0,'-1')
        self.timer_interval_entry.pack(side=LEFT, padx=(0,20))
        self.filler_label=Label(self.timer_interval_frame,bg=self.bg,fg=self.textcolor,text='                   ')
        self.filler_label.pack(side=LEFT)
        
        self.failsafe_title_frame=Frame(self.dumb_frame, bg=self.bg)
        self.failsafe_title_frame.pack(pady=(10,0))
        self.failsafe_label0=Label(self.failsafe_title_frame, fg=self.textcolor,text='Failsafes:                                              ', bg=self.bg)
        self.failsafe_label0.pack(side=LEFT)
        self.failsafe_frame=Frame(self.dumb_frame, bg=self.bg, pady=self.pady)
        self.failsafe_frame.pack(pady=self.pady)

        
        self.wrfailsafe=IntVar()
        self.wrfailsafe_check=Checkbutton(self.failsafe_frame, fg=self.textcolor,text='Prompt if no white reference has been taken.    ', bg=self.bg, pady=self.pady,highlightthickness=0, variable=self.wrfailsafe,selectcolor=self.check_bg)
        self.wrfailsafe_check.pack()#side=LEFT, pady=self.pady)
        self.wrfailsafe_check.select()
        
        self.wr_timeout_frame=Frame(self.failsafe_frame, bg=self.bg)
        self.wr_timeout_frame.pack(pady=(0,10))
        self.wr_timeout_label=Label(self.wr_timeout_frame, fg=self.textcolor,text='Timeout (minutes):', bg=self.bg)
        self.wr_timeout_label.pack(side=LEFT, padx=(10,0))
        self.wr_timeout_entry=Entry(self.wr_timeout_frame, bd=self.bd,width=10,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.wr_timeout_entry.pack(side=LEFT, padx=(0,20))
        self.wr_timeout_entry.insert(0,'8')
        self.filler_label=Label(self.wr_timeout_frame,bg=self.bg,fg=self.textcolor,text='              ')
        self.filler_label.pack(side=LEFT)
        
        
        self.optfailsafe=IntVar()
        self.optfailsafe_check=Checkbutton(self.failsafe_frame, fg=self.textcolor,text='Prompt if the instrument has not been optimized.', bg=self.bg, pady=self.pady,highlightthickness=0,selectcolor=self.check_bg, variable=self.optfailsafe)
        self.optfailsafe_check.pack()#side=LEFT, pady=self.pady)
        self.optfailsafe_check.select()
        
        self.opt_timeout_frame=Frame(self.failsafe_frame, bg=self.bg)
        self.opt_timeout_frame.pack()
        self.opt_timeout_label=Label(self.opt_timeout_frame, fg=self.textcolor,text='Timeout (minutes):', bg=self.bg)
        self.opt_timeout_label.pack(side=LEFT, padx=(10,0))
        self.opt_timeout_entry=Entry(self.opt_timeout_frame,bd=self.bd, width=10,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.opt_timeout_entry.pack(side=LEFT, padx=(0,20))
        self.opt_timeout_entry.insert(0,'60')
        self.filler_label=Label(self.opt_timeout_frame,bg=self.bg,fg=self.textcolor,text='              ')
        self.filler_label.pack(side=LEFT)
        
        self.anglesfailsafe=IntVar()
        self.anglesfailsafe_check=Checkbutton(self.failsafe_frame, fg=self.textcolor,text='Check validity of emission and incidence angles.', bg=self.bg, pady=self.pady,highlightthickness=0,selectcolor=self.check_bg, variable=self.anglesfailsafe)
        self.anglesfailsafe_check.pack(pady=(6,5))#side=LEFT, pady=self.pady)
        self.anglesfailsafe_check.select()
        
        self.labelfailsafe=IntVar()
        self.labelfailsafe_check=Checkbutton(self.failsafe_frame, fg=self.textcolor,text='Require a label for each spectrum.', bg=self.bg, pady=self.pady,highlightthickness=0, selectcolor=self.check_bg,variable=self.labelfailsafe)
        self.labelfailsafe_check.pack(pady=(6,5))#side=LEFT, pady=self.pady)
        self.labelfailsafe_check.select()
        
        self.anglechangefailsafe=IntVar()
        self.anglechangefailsafe_check=Checkbutton(self.failsafe_frame, selectcolor=self.check_bg,fg=self.textcolor,text='Remind me to check the goniometer if\nincidence and/or emission angles change.', bg=self.bg, pady=self.pady,highlightthickness=0, variable=self.anglechangefailsafe)
        self.anglechangefailsafe_check.pack(pady=(6,5))#side=LEFT, pady=self.pady)
        self.anglechangefailsafe_check.select()
        
        self.wr_anglesfailsafe=IntVar()
        self.wr_anglesfailsafe_check=Checkbutton(self.failsafe_frame,selectcolor=self.check_bg, fg=self.textcolor,text='Require a new white reference at each viewing geometry', bg=self.bg, pady=self.pady, highlightthickness=0, variable=self.wr_anglesfailsafe)
        self.wr_anglesfailsafe_check.pack(pady=(6,5))
        self.wr_anglesfailsafe_check.select()
        
        
    
        #********************** Process frame ******************************
    
        self.process_frame=Frame(self.notebook, bg=self.bg, pady=2*self.pady)
        self.process_frame.pack()

        self.input_dir_label=Label(self.process_frame,padx=self.padx,pady=self.pady,bg=self.bg,fg=self.textcolor,text='Input directory:')
        self.input_dir_label.pack(padx=self.padx,pady=self.pady)
        
        self.input_frame=Frame(self.process_frame, bg=self.bg)
        self.input_frame.pack()
        
        self.process_input_browse_button=Button(self.input_frame,text='Browse',command=self.choose_process_input_dir)
        self.process_input_browse_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.process_input_browse_button.pack(side=RIGHT, padx=self.padx)
        
        
        self.input_dir_var = StringVar()
        self.input_dir_var.trace('w', self.validate_input_dir)
         
        self.input_dir_entry=Entry(self.input_frame, width=50,bd=self.bd, textvariable=self.input_dir_var,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.input_dir_entry.insert(0, input_dir)
        self.input_dir_entry.pack(side=RIGHT,padx=self.padx)
        

        self.output_dir_label=Label(self.process_frame,padx=self.padx,pady=self.pady,bg=self.bg,fg=self.textcolor,text='Output directory:')
        self.output_dir_label.pack(padx=self.padx,pady=self.pady)
        
        self.output_frame=Frame(self.process_frame, bg=self.bg)
        self.output_frame.pack()
        self.process_output_browse_button=Button(self.output_frame,text='Browse',command=self.choose_process_output_dir)
        self.process_output_browse_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.process_output_browse_button.pack(side=RIGHT, padx=self.padx)
        
        self.output_dir_entry=Entry(self.output_frame, width=50,bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.output_dir_entry.insert(0, output_dir)
        self.output_dir_entry.pack(side=RIGHT,padx=self.padx)
        
        self.output_file_frame=Frame(self.process_frame, bg=self.bg)
        self.output_file_frame.pack()
        self.output_file_label=Label(self.process_frame,padx=self.padx,pady=self.pady,bg=self.bg,fg=self.textcolor,text='Output file name:')
        self.output_file_label.pack(padx=self.padx,pady=self.pady)
        self.output_file_entry=Entry(self.process_frame, width=50,bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.output_file_entry.pack()
        
        
        self.process_check_frame=Frame(self.process_frame, bg=self.bg)
        self.process_check_frame.pack(pady=(15,5))
        self.process_save_dir=IntVar()
        self.process_save_dir_check=Checkbutton(self.process_check_frame, selectcolor=self.check_bg,fg=self.textcolor,text='Save file configuration', bg=self.bg, pady=self.pady,highlightthickness=0, variable=self.process_save_dir)
        self.process_save_dir_check.pack(side=LEFT, pady=(5,15))
        self.process_save_dir_check.select()
        # self.process_plot=IntVar()
        # self.process_plot_check=Checkbutton(self.process_check_frame, fg=self.textcolor,text='Plot spectra', bg=self.bg, pady=self.pady,highlightthickness=0)
        # self.process_plot_check.pack(side=LEFT, pady=(5,15))
        
        self.process_button=Button(self.process_frame, fg=self.textcolor,text='Process', padx=self.padx, pady=self.pady, width=int(button_width*1.6),bg='light gray', command=self.process_cmd)
        self.process_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.process_button.pack()

        
        #********************** Plot frame ******************************
        
        self.plot_frame=Frame(self.notebook, bg=self.bg, pady=2*self.pady)
        self.plot_frame.pack()
        
        self.plot_title_label=Label(self.plot_frame,padx=self.padx,pady=self.pady,bg=self.bg,fg=self.textcolor,text='Plot title:')
        self.plot_title_label.pack(padx=self.padx,pady=(15,5))
        self.plot_title_entry=Entry(self.plot_frame, width=50,bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.plot_title_entry.pack(pady=(5,20))


        
        self.local_remote_frame=Frame(self.plot_frame, bg=self.bg)
        self.local_remote_frame.pack()
        
        self.plot_input_dir_label=Label(self.local_remote_frame,padx=self.padx,pady=self.pady,bg=self.bg,fg=self.textcolor,text='Path to .tsv file:')
        self.plot_input_dir_label.pack(side=LEFT,padx=self.padx,pady=self.pady)
        
        self.local=IntVar()
        self.local_check=Checkbutton(self.local_remote_frame, fg=self.textcolor,text=' Local',selectcolor=self.check_bg, bg=self.bg, pady=self.pady, variable=self.local,highlightthickness=0, highlightbackground=self.bg,command=self.local_plot_cmd)
        self.local_check.pack(side=LEFT,pady=(5,5),padx=(5,5))

        
        self.remote=IntVar()
        self.remote_check=Checkbutton(self.local_remote_frame, fg=self.textcolor,text=' Remote', bg=self.bg, pady=self.pady,highlightthickness=0, variable=self.remote, command=self.remote_plot_cmd,selectcolor=self.check_bg)
        self.remote_check.pack(side=LEFT, pady=(5,5),padx=(5,5))
        self.remote_check.select()
        

        self.plot_file_frame=Frame(self.plot_frame, bg=self.bg)
        self.plot_file_frame.pack(pady=(5,10))
        self.plot_file_browse_button=Button(self.plot_file_frame,text='Browse',command=self.choose_plot_file)
        self.plot_file_browse_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.plot_file_browse_button.pack(side=RIGHT, padx=self.padx)
        
        self.plot_input_dir_entry=Entry(self.plot_file_frame, width=50,bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.plot_input_dir_entry.insert(0, input_dir)
        self.plot_input_dir_entry.pack(side=RIGHT)
        
        # self.no_wr_frame=Frame(self.plot_frame, bg=self.bg)
        # self.no_wr_frame.pack()

        

                
        self.load_labels_frame=Frame(self.plot_frame, bg=self.bg)
        self.load_labels_frame.pack()
        self.load_labels=IntVar()
        self.load_labels_check=Checkbutton(self.load_labels_frame, selectcolor=self.check_bg,fg=self.textcolor,text='Load labels from log file', bg=self.bg, pady=self.pady,highlightthickness=0, variable=self.load_labels, command=self.load_labels_cmd)
        self.load_labels_check.pack(pady=(5,5))
        
        self.plot_logfile_frame=Frame(self.plot_frame, bg=self.bg)
        self.plot_logfile_frame.pack()
        self.select_plot_logfile_button=Button(self.plot_logfile_frame, fg=self.textcolor,text='Browse',command=self.chooseplotlogfile, height=1,bg=self.buttonbackgroundcolor)
        self.select_plot_logfile_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor)
        self.plot_logfile_entry=Entry(self.plot_logfile_frame, width=50,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        
        self.no_wr=IntVar()
        self.no_wr_check=Checkbutton(self.plot_frame,selectcolor=self.check_bg, fg=self.textcolor,text='Exclude white references', bg=self.bg, pady=self.pady,highlightthickness=0, variable=self.no_wr, command=self.no_wr_cmd)
        self.no_wr_check.pack(pady=(5,5))
        self.no_wr_check.select()
        

        
        
        #self.load_labels_entry.pack()
        
        
        # pr_check_frame=Frame(self.process_frame, bg=self.bg)
        # self.process_check_frame.pack(pady=(15,5))
        # self.process_save_dir=IntVar()
        # self.process_save_dir_check=Checkbutton(self.process_check_frame, fg=self.textcolor,text='Save file configuration', bg=self.bg, pady=self.pady,highlightthickness=0, variable=self.process_save_dir)
        # self.process_save_dir_check.pack(side=LEFT, pady=(5,15))
        # self.process_save_dir_check.select()
        # self.process_plot=IntVar()
        # self.process_plot_check=Checkbutton(self.process_check_frame, fg=self.textcolor,text='Plot spectra', bg=self.bg, pady=self.pady,highlightthickness=0)
        # self.process_plot_check.pack(side=LEFT, pady=(5,15))
        
        self.plot_button=Button(self.plot_frame, fg=self.textcolor,text='Plot', padx=self.padx, pady=self.pady, width=int(button_width*1.6),bg='light gray', command=self.plot)
        self.plot_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.plot_button.pack(pady=(20,20))
    
        #************************Console********************************
        self.console_frame=Frame(self.test_view.embed, bg=self.border_color, height=200, highlightthickness=2,highlightcolor=self.bg)
        self.console_frame.pack(fill=BOTH, expand=True, padx=(1,1))
        #self.console_frame.configure(height=400)
        self.console_title_label=Label(self.console_frame,padx=self.padx,pady=self.pady,bg=self.border_color,fg='black',text='Console',font=("Helvetica", 11))
        self.console_title_label.pack(pady=(5,5))
        self.text_frame=Frame(self.console_frame)
        self.scrollbar = Scrollbar(self.text_frame)
        self.notebook_width=self.notebook.winfo_width()
        self.notebook_height=self.notebook.winfo_width()
        self.console_log = Text(self.text_frame, width=self.notebook_width,bg=self.bg, fg=self.textcolor)
        self.scrollbar.pack(side=RIGHT, fill=Y)
    
        self.scrollbar.config(command=self.console_log.yview)
        self.console_log.configure(yscrollcommand=self.scrollbar.set)
        self.console_entry=Entry(self.console_frame, width=self.notebook_width,bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
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
        #self.notebook.add(self.console_frame,text='Console')
        #self.notebook.add(val_frame, fg=self.textcolor,text='Validation tools')
        #checkbox: Iterate through a range of geometries
        #checkbox: Choose a single geometry
        #checkbox: Take one spectrum
        #checkbox: Use a self.timer to collect a series of spectra
        #self.timer interval: 
        #Number of spectra to collect:
        self.notebook.pack(fill=BOTH, expand=True)
        

        #test=TestView(self.master)
        # frame=Frame(self.control_frame)
        # frame.pack()
        # button=Button(frame, text=':D',command=self.move_test)
        # button.pack()
        # self.next_pos=20
        #test_view.run()


        self.test_view.draw_circle(1000,700)


        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        thread = Thread(target =self.bind)
        thread.start()
        self.master.mainloop()
        
        #self.view.join()
        
    def move_test(self):
        print(self.next_pos)
        self.test_view.move_light(self.next_pos)
        if self.next_pos<80:
            self.next_pos+=10
        else:
            self.next_pos-=10
        
    def bind(self):
        #self.test_view.flip()
        time.sleep(0.25)
        self.master.bind("<Configure>", self.resize)
        window=PretendEvent(self.master,self.master.winfo_height(),self.master.winfo_width())
        self.resize(window)
        time.sleep(0.2)
        self.log('Spec compy connected.')
        self.log('Raspberry pi connected.')
        
        #self.master.configure(width=1300, height=800)

    def on_closing(self):
        self.test_view.quit()
        self.master.destroy()
    def local_plot_cmd(self):
        if self.local.get() and not self.remote.get():
            return
        elif self.remote.get() and not self.local.get():
            return
        elif not self.remote.get():
            self.remote_check.select()
        else:
            self.remote_check.deselect()
        
    def remote_plot_cmd(self):
        if self.local.get() and not self.remote.get():
            return
        elif self.remote.get() and not self.local.get():
            return
        elif not self.local.get():
            self.local_check.select()
        else:
            self.local_check.deselect()
        
    def no_wr_cmd(self):
        pass
        
    def load_labels_cmd(self):
        if self.load_labels.get():
            self.select_plot_logfile_button.pack(side=RIGHT,padx=(5,2), pady=(0,0))
            self.plot_logfile_entry.pack(side=RIGHT)

            if self.plot_logfile_entry.get()=='':
                try:
                    self.plot_logfile_entry.insert(0,self.log_filename)
                except:
                    print('no log file')
        else:
            self.plot_logfile_entry.pack_forget()
            self.select_plot_logfile_button.pack_forget()

    def chooseplotlogfile(self):
        filename = askopenfilename(initialdir=log_loc,title='Select log file to load labels from')
        self.plot_logfile_entry.delete(0,'end')
        self.plot_logfile_entry.insert(0, filename)  
        
              
    def chooselogfile(self):
        self.log_filename = askopenfilename(initialdir=log_loc,title='Select existing log file to append to')
        self.logfile_entry.delete(0,'end')
        self.logfile_entry.insert(0, self.log_filename)

        
    def newlog(self):
        try:
            log = asksaveasfile(mode='w', defaultextension=".txt",title='Create a new log file')
        except:
            pass
        if log is None: # asksaveasfile returns `None` if dialog closed with "cancel".
            return
        self.log_filename=log.name
        log.write(str(datetime.datetime.now())+'\n')
        self.logfile_entry.delete(0,'end')
        self.logfile_entry.insert(0, self.log_filename)
        
    def move_sample():
        self.pi_commander.move_sample()
        
    
    #     
    # def go(self):
    #     #self.queue.append({self.optimize:[]})
    #     ok=self.check_mandatory_input()
    #     
    #     self.queue.append({self.white_reference:[True]})
    #     self.queue.append({self.take_spectrum:[True]})
    #     self.queue.append({self.move_sample:[])
    #     self.queue.append({self.take_spectrum:[True]})
    #     self.optimize()
        # if self.manual.get==0:
        #     self.take_spectrum()
            
        # else:
        #     #TODO: recursive calls to take_spectrum. Pass dict of i, e entries. Take spectrum using first set of entries then if it succeeds, have it call itself with the first set of entries removed from the dict.
        #     incidenc
        #     self.model.go(incidence, emission)
            
            
        # elif self.individual_range.get()==0:

        #     self.take_spectrum

        #   else:
        #     incidence={'start':-1,'end':-1,'increment':-1}
        #     emission={'start':-1,'end':-1,'increment':-1}
        #     try:
        #         incidence['start']=int(light_start_entry.get())
        #         incidence['end']=int(light_end_entry.get())
        #         incidence['increment']=int(light_increment_entry.get())
        #         
        #         emission['start']=int(detector_start_entry.get())
        #         emission['end']=int(detector_end_entry.get())
        #         emission['increment']=int(detector_increment_entry.get())
        #     except:
        #         print('Invalid input')
        #         return
        #   self.model.go(incidence, emission)
        # 
        # if self.spec_save_config.get():
        #     print('writing to spec_save')
        #     file=open('spec_save.txt','w')
        #     file.write(self.spec_save_dir_entry.get()+'\n')
        #     file.write(self.spec_basename_entry.get()+'\n')
        #     file.write(self.spec_startnum_entry.get()+'\n')
             
    #If the user has failsafes activated, check that requirements are met. Always require a valid number of spectra.
    def check_optional_input(self, func, args=[]):
            label=''
            now=int(time.time())
            incidence=self.incidence_entries[0].get()
            emission=self.emission_entries[0].get()
            
            if self.manual_automatic.get()==0:

                if self.optfailsafe.get():
                    try:
                        opt_limit=int(float(self.opt_timeout_entry.get()))*60
                    except:
                        opt_limit=sys.maxsize
                    if self.opt_time==None:
                        label+='The instrument has not been optimized.\n\n'
                    elif now-self.opt_time>opt_limit: 
                        minutes=str(int((now-self.opt_time)/60))
                        seconds=str((now-self.opt_time)%60)
                        if int(minutes)>0:
                            label+='The instrument has not been optimized for '+minutes+' minutes '+seconds+' seconds.\n\n'
                        else: label+='The instrument has not been optimized for '+seconds+' seconds.\n\n'
                

                if self.wrfailsafe.get() and func!=self.wr:
    
                    try:
                        wr_limit=int(float(self.wr_timeout_entry.get()))*60
                    except:
                        wr_limit=sys.maxsize
                    if self.wr_time==None:
                        label+='No white reference has been taken.\n\n'
                    elif self.opt_time!=None and self.opt_time>self.wr_time:
                            label+='No white reference has been taken since the instrument was optimized.\n\n'
                    elif int(self.instrument_config_entry.get()) !=int(self.spec_config_count):
                        label+='No white reference has been taken while averaging this number of spectra.\n\n'
                    elif self.spec_config_count==None:
                        label+='No white reference has been taken while averaging this number of spectra.\n\n'
                    elif now-self.wr_time>wr_limit: 
                        minutes=str(int((now-self.wr_time)/60))
                        seconds=str((now-self.wr_time)%60)
                        if int(minutes)>0:
                            label+=' No white reference has been taken for '+minutes+' minutes '+seconds+' seconds.\n\n'
                        else: label+=' No white reference has been taken for '+seconds+' seconds.\n\n'
                if self.wr_anglesfailsafe.get() and func!=self.wr:
    
                    if self.angles_change_time!=None and self.wr_time!=None:
                        if self.angles_change_time>self.wr_time+1:
                            label+=' No white reference has been taken at this viewing geometry.\n\n'
                        elif emission!=self.e or incidence!=self.i:
                            label+=' No white reference has been taken at this viewing geometry.\n\n'
                        
                if self.anglesfailsafe.get():
                    valid_i=validate_int_input(incidence,self.min_i,self.max_i)
                    valid_e=validate_int_input(emission,self.min_e,self.max_e)
                    valid_separation=self.validate_distance(incidence,emission)
                    # if not valid_i and not valid_e:
                    #     label+='The emission ('+str(self.min_e)+'to '+str(self.max_e)+') and incidence ('+str(self.min_i)+'to '+str(self.max_i)+') angles are invalid.\n\n'
                    if not valid_i:
                        label+='The incidence angle is invalid (Min:'+str(self.min_i)+', Max:'+str(self.max_i)+').\n\n'
                    if not valid_e:
                        label+='The emission angle is invalid (Min:'+str(self.min_e)+', Max:'+str(self.max_i)+').\n\n'
                    if valid_e and valid_i:
                        if not valid_separation:
                            label+='Incidence and emission need to be at least '+str(self.required_angular_separation)+' degrees apart.\n\n'
                        
                if self.anglechangefailsafe.get():
                    anglechangealert=False
                    if self.angles_change_time==None and emission!='' and incidence !='':
                        label+='This is the first time emission and incidence angles are being set,\n'
                        anglechangealert=True
                    elif self.e==None and emission!='':
                        label+='This is the first time the emission angle is being set,\n'
                        anglechangealert=True
                        if incidence!=self.i and incidence!='':
                            label+='and the incidence angle has changed since last spectrum,\n'
                        anglechangealert=True
                    elif self.i==None and incidence!='':
                        label+='This is the first time the incidence angle is being set,\n'
                        anglechangealert=True
                        if emission!=self.e and emission !='':
                            label+='and the emission angle has changed since last spectrum,\n' 
                        anglechangealert=True
                    if anglechangealert==False and emission!=self.e and emission !='' and incidence !=self.i and incidence!='':
                        if self.e!=None and self.i!=None:
                            label+='The emission and incidence angles have changed since last spectrum,\n'
                            anglechangealert=True
                    elif anglechangealert==False and emission!=self.e and emission !='':
                        label+='The emission angle has changed since last spectrum,\n'
                        anglechangealert=True
                    elif anglechangealert==False and incidence!=self.i and incidence!='':
                        label+='The incidence angle has changed since last spectrum,\n' 
                        anglechangealert=True
                        
                    if anglechangealert:#and onlyanglechange:
                        label+='so the goniometer arm(s) may need to change to match.\n\n'
                        pass
                   
            if self.labelfailsafe.get():
                if self.label_entry.get()=='':
                    label +='This spectrum has no label.\n\n'

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
        def inner_mkdir(new):
            try:
                os.makedirs(new)
            except:
                dialog=ErrorDialog(self, title='Error',label='Error: failed to create log directory.\n Creating new log file in current working directory.',topmost=False)
                self.logfile_entry.delete(0,'end')
                dialog.top.lower()
                dialog.top.tkraise(self.master)
            self.check_logfile()

        if self.logfile_entry.get()=='':
            self.log_filename='log_'+datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')+'.txt'
            with open(self.log_filename,'w+') as log:
                log.write(str(datetime.datetime.now())+'\n')
            if opsys=='Linux':
                self.logfile_entry.insert(0,os.getcwd()+'/'+self.log_filename)
            elif opsys=='Windows':
                self.logfile_entry.insert(0,os.getcwd()+'\\'+self.log_filename)
            elif opsys=='Mac':
                self.logfile_entry.insert(0,os.getcwd()+'/'+self.log_filename)


        elif self.logfile_entry.get()!=self.log_filename:
            dir=None
            if opsys=='Linux':
                if '/' in self.logfile_entry.get()[1:]:
                    dir='/'.join(self.logfile_entry.get().split('/')[:-1])
                else:
                    self.logfile_entry.insert(0,os.getcwd()+'/')
            elif opsys=='Windows':
                if '\\' in self.logfile_entry.get()[1:]:
                    dir='\\'.join(self.logfile_entry.get().split('\\')[:-1])
                else:
                    self.logfile_entry.insert(0,os.getcwd()+'\\')
            elif opsys=='Mac':
                if '/' in self.logfile_entry.get()[1:]:
                    dir='/'.join(self.logfile_entry.get().split('/')[:-1])
                else:
                    self.logfile_entry.insert(0,os.getcwd()+'/')
            if dir!=None:
                if not os.path.isdir(dir):
                    inner_mkdir(dir)
                    return

            if not os.path.isfile(self.logfile_entry.get()):
                try:
                    if '.' not in self.logfile_entry.get():
                        self.logfile_entry.insert('end','.txt')
                    with open(self.logfile_entry.get(),'w+') as log:
                        log.write(str(datetime.datetime.now())+'\n')
                    self.log_filename=self.logfile_entry.get()

                except:
                    dialog=ErrorDialog(self,label='Error: Could not open log file for writing.\nCreating new log file in current working directory', topmost=False)
                    dialog.top.lower()
                    dialog.top.tkraise(self.master)

                    self.logfile_entry.delete(0,'end')
                    self.check_logfile()
            else:
                self.log_filename=self.logfile_entry.get()

            
    def opt(self):
        self.check_logfile()
        try:
            new_spec_config_count=int(self.instrument_config_entry.get())
            if new_spec_config_count<1 or new_spec_config_count>32767:
                raise(Exception)
        except:
            dialog=ErrorDialog(self,label='Error: Invalid number of spectra to average.\nEnter a value from 1 to 32767')
            return 
            
        if self.spec_config_count==None or str(new_spec_config_count) !=str(self.spec_config_count):
            self.queue.insert(0, {self.opt:[]})
            self.configure_instrument()
            return
            
        self.spec_commander.optimize()
        handler=OptHandler(self)

    def test(self,arg=False):
        print(arg)
        
    #Check whether the current save configuration is different from the last one saved. If it is, send commands to the spec compy telling it so.
    def check_save_config(self):
        new_spec_save_dir=self.spec_save_dir_entry.get()
        new_spec_basename=self.spec_basename_entry.get()
        try:
            new_spec_num=int(self.spec_startnum_entry.get())
        except:
            return 'invalid'
 
        if new_spec_save_dir=='' or new_spec_basename=='' or new_spec_num=='':
            return 'invalid'
        
        if new_spec_save_dir != self.spec_save_path or new_spec_basename != self.spec_basename or self.spec_num==None or new_spec_num!=self.spec_num:
            return 'not_set'
        else:
            return 'set'
            
    def check_mandatory_input(self):
        save_config_status=self.check_save_config()
        if save_config_status=='invalid':
            dialog=ErrorDialog(self,label='Error: Please enter a valid save configuration.')
            return False
            
        try:
            new_spec_config_count=int(self.instrument_config_entry.get())
            if new_spec_config_count<1 or new_spec_config_count>32767:
                raise(Exception)
        except:
            dialog=ErrorDialog(self,label='Error: Invalid number of spectra to average.\nEnter a value from 1 to 32767')
            return False
            
        if self.manual_automatic.get()==1:
            for index in range(len(self.active_incidence_entries)):
                i=self.active_incidence_entries[index].get()
                e=self.active_emission_entries[index].get()
                valid_i=validate_int_input(i,-90,90)
                valid_e=validate_int_input(e,-90,90)
                if not valid_i or not valid_e:
                    dialog=ErrorDialog(self,label='Error: Invalid viewing geometry:\n\nincidence = '+str(i)+'\nemission = '+str(e),width=300, height=130)
                    return False
        return True
        
            
    def set_and_animate_geom(self):
            self.set_geom()
            valid_i=validate_int_input(self.i,-90,90)
            if valid_i:
                self.test_view.move_light(int(self.i))
            valid_e=validate_int_input(self.e,-90,90)
            if valid_e:
                self.test_view.move_detector(int(self.e))
    #Check that all input is valid, the save configuration is set, and the instrument is configured.
    #This gets called once when the user clicks something, but not for subsequent actions.
    def setup(self, nextaction):
        self.check_logfile()
        

        
        if self.manual_automatic.get()==0:
            thread=Thread(target=self.set_and_animate_geom)
            thread.start()

        #Requested save config is guaranteed to be valid because of input checks above.
        save_config_status=self.check_save_config()
        if self.check_save_config()=='not_set':
            print('going to set save config')
            self.complete_queue_item()
            self.queue.insert(0,nextaction)
            self.queue.insert(0,{self.set_save_config:[]})
            self.set_save_config()#self.take_spectrum,[True])
            return False

        #Requested instrument config is guaranteed to be valid because of input checks above.
        new_spec_config_count=int(self.instrument_config_entry.get())
        if self.spec_config_count==None or str(new_spec_config_count) !=str(self.spec_config_count):
            self.complete_queue_item()
            self.queue.insert(0,nextaction)
            self.queue.insert(0,{self.configure_instrument:[]})
            self.configure_instrument()
            return False
            
        if self.spec_save_config.get():
            file=open(self.config_loc+'spec_save.txt','w')
            file.write(self.spec_save_dir_entry.get()+'\n')
            file.write(self.spec_basename_entry.get()+'\n')
            file.write(self.spec_startnum_entry.get()+'\n')

            self.input_dir_entry.delete(0,'end')
            self.input_dir_entry.insert(0,self.spec_save_dir_entry.get())
        

        return True
    #Action will be either wr or take a spectrum
    def acquire(self, override=False, setup_complete=False, action=None, garbage=False):
        print('Acquiring!')

        if not setup_complete:
            #Set all entries to active
            self.active_incidence_entries=list(self.incidence_entries)
            self.active_emission_entries=list(self.emission_entries)
            self.active_i_e_pair_frames=list(self.i_e_pair_frames)
            


        if action==None: #If this was called by the user clicking acquire
            action=self.acquire
            self.queue.append({self.acquire:[]})
            if self.individual_range.get()==1:
                self.range_setup()
                
        if not override:
            ok=self.check_mandatory_input()
            if not ok:
                return
            
            #If input isn't valid and the user asks to continue, take_spectrum will be called again with override set to True  
            valid_input=self.check_optional_input(action,[True,False])
            if not valid_input:
                return         
                
        if not setup_complete:
            setup=self.setup({action:[True, False]})
            #If things were not already set up (instrument config, etc) then the compy will take care of that and call take_spectrum again after it's done.
            if not setup:
                return
                
            

        #Highlight whatever i, e pair is being currently used if there are multiple to do.
        elif self.individual_range.get()==0 and len(self.incidence_entries)>1:
            self.active_i_e_pair_frames[0].configure(bg='white')
            pass


        
        if action==self.take_spectrum:
            startnum_str=str(self.spec_startnum_entry.get())
            while len(startnum_str)<NUMLEN:
                startnum_str='0'+startnum_str
            
            self.spec_commander.take_spectrum(self.spec_save_path, self.spec_basename, startnum_str)
            if not garbage:
                handler=SpectrumHandler(self)
            else:
                handler=SpectrumHandler(self,title='Collecting garbage...',label='Collecting garbage spectrum...')
                

        elif action==self.wr:
            self.spec_commander.white_reference()
            handler=WhiteReferenceHandler(self)
            
        elif action==self.acquire:
        
            self.build_queue()
            self.next_in_queue()
                        
    def set_geom(self):
        self.angles_change_time=time.time()
        self.i=int(self.active_incidence_entries[0].get())
        self.e=int(self.active_emission_entries[0].get())

        
    def set_text(self,widget, text):
        widget.configure(state='normal')
        widget.delete(0,'end')
        widget.insert(0,text)
        widget.configure(state='disabled')
    def next_geom(self): 

        


        #This only gets called from automatic mode, so the question is just ind. vs range.
       # if self.individual_range.get()==0:
            
        self.active_incidence_entries.pop(0)
        self.active_emission_entries.pop(0)
        
        
        if self.individual_range.get()==0:
            self.active_i_e_pair_frames.pop(0)
        
        next_i=int(self.active_incidence_entries[0].get())
        next_e=int(self.active_incidence_entries[0].get())

        self.complete_queue_item()
        #Update goniometer position. Don't run the arms into each other.
        if next_e>self.e:
            self.queue.insert(0,{self.move_light:[]})
            self.queue.insert(0,{self.move_detector:[]})

        else:
            self.queue.insert(0,{self.move_detector:[]})
            self.queue.insert(0,{self.move_light:[]})

        self.next_in_queue()
                   
        
    def move_light(self):
        self.pi_commander.move_light(self.active_incidence_entries[0].get())
        handler=MotionHandler(self,label='Moving light source...')
        self.test_view.move_light(int(self.active_incidence_entries[0].get()))
        self.set_geom()
        
    def move_detector(self):
        self.pi_commander.move_detector(self.active_emission_entries[0].get())
        handler=MotionHandler(self,label='Moving detector...')
        self.test_view.move_detector(int(self.active_emission_entries[0].get()))
        self.set_geom()
        
    def move_tray(self):
        self.pi_commander.move_tray()
        handler=MotionHandler(self,label='Moving sample tray...')
        
    def build_queue(self):
        self.queue=[]

        if True:#self.individual_range.get()==0:
            #For each (i, e), opt, white reference, save the white reference, move the tray, take a  spectrum, then move the tray back, then update geom to next.
            for entry in self.active_incidence_entries:
                self.queue.append({self.opt:[]})
                self.queue.append({self.wr:[True,True]})
                self.queue.append({self.take_spectrum:[True,True,False]})
                self.queue.append({self.move_tray:[]})
                self.queue.append({self.take_spectrum:[True,True,True]})
                self.queue.append({self.delete_placeholder_spectrum:[]})
                self.queue.append({self.take_spectrum:[True,True,False]})
                self.queue.append({self.move_tray:[]})
                self.queue.append({self.next_geom:[]})
                
            #No update geometry call after last spectrum
            self.queue.pop(-1)

        #Put in calls to move light and detector for the first geometry (this happens in next_indv geom, or repeatedly here if you are specifying a range)
        next_i=int(self.active_incidence_entries[0].get())
        next_e=int(self.active_emission_entries[0].get())
        
        if next_e>int(self.e):
            self.queue.insert(0,{self.move_detector:[]})
            self.queue.insert(0,{self.move_light:[]})
        else:
            self.queue.insert(0,{self.move_light:[]})
            self.queue.insert(0,{self.move_detector:[]})
            
    def range_setup(self):
        print('RANGE SETUP')
        self.active_incidence_entries=[]
        self.active_emission_entries=[]
        
        first_i=int(self.light_start_entry.get())
        final_i=int(self.light_end_entry.get())
        i_interval=int(self.light_increment_entry.get())
        incidences=[]
        if final_i>first_i:
            incidences=np.arange(first_i,final_i,i_interval)
        else:
            incidences=np.arange(first_i,final_i,-1*i_interval)
        incidences=list(incidences)
        incidences.append(final_i)

    
        
        
        first_e=int(self.detector_start_entry.get())
        final_e=int(self.detector_end_entry.get())
        e_interval=int(self.detector_increment_entry.get())
        eimissions=[]
        if final_e>first_e:
            emissions=np.arange(first_e,final_e,e_interval)
        else:
            emissions=np.arange(first_e,final_e,-1*e_interval)
        emissions=list(emissions)
        emissions.append(final_e)
        
        for i in incidences:
            for e in emissions:
                i_entry=PrivateEntry(str(i))
                e_entry=PrivateEntry(str(e))
                self.active_incidence_entries.append(i_entry)
                self.active_emission_entries.append(e_entry)
        
        
        
        



            
    def spec_button_cmd(self):
        self.queue=[]
        self.queue.append({self.take_spectrum:[False,False]})
        self.take_spectrum()
        
    def take_spectrum(self, override=False, setup_complete=False,garbage=False):
        if garbage:
            print('GARBAGE!')
        self.acquire(override=override, setup_complete=setup_complete,action=self.take_spectrum,garbage=garbage)
    
    def wr_button_cmd(self):
        self.queue=[]
        self.queue.append({self.wr:[False,False]})
        self.queue.append({self.take_spectrum:[True,True]})
        self.wr()
        
    def opt_button_cmd(self):
        self.queue=[]
        self.queue.append({self.opt:[]})
        self.opt()
        
    def wr(self, override=False, setup_complete=False):
        
        #Label this as a white reference for the log file
        self.current_label=self.label_entry.get()
        if self.label_entry.get()!='' and 'White reference' not in self.label_entry.get():
            # self.label_entry.insert(0, 'White reference (')
            # self.label_entry.insert('end',')')
            newlabel='White reference: '+self.current_label
            self.set_text(self.label_entry,newlabel)
        elif self.label_entry.get()=='':
            self.set_text(self.label_entry,'White reference')
            #self.label_entry.insert(0,'White reference')
            
        self.acquire(override=override, setup_complete=setup_complete,action=self.wr)
    
    def check_connection(self):
        self.connection_checker.check_connection(False)
    
    def configure_instrument(self):
        self.spec_commander.configure_instrument(self.instrument_config_entry.get())
        handler=InstrumentConfigHandler(self)
        
    def set_save_config(self):
        def inner_mkdir(dir):
            status=self.remote_directory_worker.mkdir(dir)
            if status=='mkdirsuccess':
                self.set_save_config(args)
            elif status=='mkdirfailedfileexists':
                dialog=ErrorDialog(self,title='Error',label='Could not create directory:\n\n'+dir+'\n\nFile exists.')
            elif status=='mkdirfailed':
                dialog=ErrorDialog(self,title='Error',label='Could not create directory:\n\n'+dir)

        status=self.remote_directory_worker.get_dirs(self.spec_save_dir_entry.get())

        if status=='listdirfailed':
            buttons={
                'yes':{
                    inner_mkdir:[self.spec_save_dir_entry.get()]
                },
                'no':{
                }
            }
            dialog=ErrorDialog(self,title='Directory does not exist',label=self.spec_save_dir_entry.get()+'\ndoes not exist. Do you want to create this directory?',buttons=buttons)
            return
        elif status=='listdirfailedpermission':
            dialog=ErrorDialog(self,label='Error: Permission denied for\n'+self.spec_save_dir_entry.get())
            return
        
        elif status=='timeout':
            print('foo')
            dialog=ErrorDialog(self, label='Error: Operation timed out.\n\nCheck that the automation script is running on the spectrometer computer\nand the spectrometer is connected.')
            return
            
        self.spec_commander.check_writeable(self.spec_save_dir_entry.get())
            
        t=2*BUFFER
        while t>0:
            if 'yeswriteable' in self.spec_listener.queue:
                self.spec_listener.queue.remove('yeswriteable')
                break
            elif 'notwriteable' in self.spec_listener.queue:
                self.spec_listener.queue.remove('notwriteable')
                dialog=ErrorDialog(self, label='Error: Permission denied.\nCannot write to specified directory.')
                return
            time.sleep(INTERVAL)
            t=t-INTERVAL
        if t<=0:
            dialog=ErrorDialog(self,label='TIMEOUT')
            return
        
        
        spec_num=self.spec_startnum_entry.get()
        while len(spec_num)<NUMLEN:
            spec_num='0'+spec_num
        self.spec_commander.set_save_path(self.spec_save_dir_entry.get(), self.spec_basename_entry.get(), self.spec_startnum_entry.get())

        handler=SaveConfigHandler(self)
            
            
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
            return
        if incidence<0 or incidence>90 or emission<0 or emission>90:
            return
        # self.model.move_light(i)
        # self.model.move_detector(e)
        
    def process_cmd(self):
        output_file=self.output_file_entry.get()
        if output_file=='':
            dialog=ErrorDialog(self, label='Error: Enter an output file name')
            return
        if '.' not in output_file: output_file=output_file+'.tsv'
        #error=self.model.process(self.input_dir_entry.get(), self.output_dir_entry.get(), output_file)
        # if error!=None:
        #     dialog=ErrorDialog(self, label='Error sending process command:\n'+error.strerror)
        self.spec_commnader.process(self.input_dir_entry.get(), self.output_dir_entry.get(), output_file)
        
        if self.process_save_dir.get():
            file=open(self.config_loc+'/process_directories','w')
            file.write(self.input_dir_entry.get()+'\n')
            file.write(self.output_dir_entry.get()+'\n')
            file.write(output_file+'\n')
            self.plot_input_dir_entry.delete(0,'end')
            plot_file=self.output_dir_entry.get()+'\\'+output_file
            self.plot_input_dir_entry.insert(0,plot_file)
           
        self.queue.insert(0,{self.process_cmd:[]})
        process_handler=ProcessHandler(self)
            
    def plot(self):
        filename=self.plot_input_dir_entry.get()
        # filename=filename.replace('C:\\SpecShare',self.spec_share_loc)
        # filename=filename.replace('C:\\Users',self.data_share_loc)
        if self.opsys=='Windows' or self.remote.get(): filename=filename.replace('\\','/')
        
        if self.remote.get():
            self.spec_commander.get_data(filename)

            t=3*BUFFER
            while True:
                if 'datacopied' in self.spec_listener.queue:
                    self.spec_listener.queue.remove('datacopied')
                    filename=self.spec_share_loc+'temp.tsv'
                    break
                elif 'datafailure' in self.spec_listener.queue:
                    self.spec_listener.queue.remove('datafailure')
                    dialog=ErrorDialog(self,label='Error: Failed to acquire data.\nDoes the file exist? Do you have permission to use it?')
                    return
                time.sleep(INTERVAL)
                t=t-INTERVAL
        
        title=self.plot_title_entry.get()
        caption=''#self.plot_caption_entry.get()
        labels={}
        nextfile=None
        nextnote=None
        try:
            if self.load_labels.get():
                with open(self.plot_logfile_entry.get()) as log:
                    for line in log:
                        if 'filename' in line:
                            if '\\' in line:
                                line=line.split('\\')
                            else:
                                line=line.split('/')
                            nextfile=line[-1].strip('\n')
                            nextfile=nextfile.split('.')
                            nextfile=nextfile[0]+nextfile[1]
                        elif 'Label' in line:
                            nextnote=line.split('Label: ')[-1]
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
        # global user_cmds
        # global user_cmd_index
        if keypress_event.keycode==36:
            cmd=self.console_entry.get()
            if cmd !='':
                # user_cmds.insert(0,cmd)
                # user_cmd_index=-1
                self.console_log.insert(END,'>>> '+cmd+'\n')
                self.console_entry.delete(0,'end')
                
                params=cmd.split(' ')
                if params[0].lower()=='clear':
                    self.console_log.delete('1.0',END)
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
        r=RemoteFileExplorer(self,label='Select a directory to save raw spectral data.\nThis must be to a drive mounted on the spectrometer control computer.\n E.g. R:\RiceData\MarsGroup\Kathleen\spectral_data', target=self.spec_save_dir_entry)
        
    def choose_process_input_dir(self):
        r=RemoteFileExplorer(self,label='Select the directory containing the data you want to process.\nThis must be to a drive mounted on the spectrometer control computer.\n E.g. R:\RiceData\MarsGroup\Kathleen\spectral_data',target=self.input_dir_entry)
        
    def choose_process_output_dir(self):
        r=RemoteFileExplorer(self,label='Select the directory where you want to save your processed data.\nThis must be to a drive mounted on the spectrometer control computer.\n E.g. R:\RiceData\MarsGroup\Kathleen\spectral_data',target=self.output_dir_entry)
    
    # def validate_basename(self,*args):
    #     basename=limit_len(self.spec_basename_entry.get())
    #     basename=rm_reserved_chars(basename)
    #     self.spec_basename_entry.set(basename)
    # 
    # def validate_startnum(self,*args):
    #     num=spec_startnum.get()
    #     valid=validate_int_input(num,999,0)
    #     if not valid:
    #         spec_startnum.set('')
    #     else:
    #         while len(num)<NUMLEN:
    #             num=0+num
    #     self.spec_startnum_entry.delete(0,'end')
    #     self.spec_startnum_entry.insert(0,num)
    
    def remove_i_e_pair(self,index):
        self.incidence_labels.pop(index)
        self.incidence_entries.pop(index)
        #self.active_incidence_entries.pop(index)
        self.emission_entries.pop(index)
        #self.active_emission_entries.pop(index)
        self.emission_labels.pop(index)
        self.i_e_removal_buttons.pop(index)
        #self.active_i_e_pair_frames.pop(index)
        self.i_e_pair_frames.pop(index).destroy()


        for i, button in enumerate(self.i_e_removal_buttons):
            button.configure(command=lambda x=i:self.remove_i_e_pair(x))
        if self.manual_automatic.get()==1:
            self.add_i_e_pair_button.configure(state=NORMAL)
        if len(self.incidence_entries)==1:
            self.i_e_removal_buttons[0].pack_forget()
    
    def add_i_e_pair(self):
        try:
            self.add_i_e_pair_button.pack_forget()
        except:
            self.add_i_e_pair_button=Button(self.individual_angles_frame, text='Add', command=self.add_i_e_pair,width=7, fg=self.buttontextcolor, bg=self.buttonbackgroundcolor,bd=self.bd)
            self.tk_buttons.append(self.add_i_e_pair_button)
            self.add_i_e_pair_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor,state=DISABLED)
            
        self.i_e_pair_frames.append(Frame(self.individual_angles_frame, bg=self.bg))
        self.i_e_pair_frames[-1].pack(pady=(5,0))
        self.incidence_labels.append(Label(self.i_e_pair_frames[-1],bg=self.bg,fg=self.textcolor,text='Incidence:'))
        self.incidence_labels[-1].pack(side=LEFT, padx=(5,5),pady=(0,8))
        
        self.incidence_entries.append(Entry(self.i_e_pair_frames[-1], width=10, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground))
        self.entries.append(self.incidence_entries[-1])
        self.incidence_entries[-1].pack(side=LEFT)
        
        if True:#len(self.emission_labels)==0:
            self.emission_labels.append(Label(self.i_e_pair_frames[-1], padx=self.padx,pady=self.pady,bg=self.bg, fg=self.textcolor,text='Emission:'))
        else:
            self.emission_labels.append(Label(self.i_e_pair_frames[-1], padx=self.padx,pady=self.pady,bg=self.bg, fg=self.textcolor,text='               '))
        self.emission_labels[-1].pack(side=LEFT, padx=(10,0))
            
        self.emission_entries.append(Entry(self.i_e_pair_frames[-1], width=10, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground))
        self.entries.append(self.emission_entries[-1])
        self.emission_entries[-1].pack(side=LEFT, padx=(0,20))
        
        self.i_e_removal_buttons.append(Button(self.i_e_pair_frames[-1], text='Remove', command=lambda x=len(self.i_e_removal_buttons):self.remove_i_e_pair(x),width=7, fg=self.buttontextcolor, bg=self.buttonbackgroundcolor,bd=self.bd))
        self.i_e_removal_buttons[-1].config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        if len(self.incidence_entries)>1:
            for button in self.i_e_removal_buttons:
                button.pack(side=LEFT,padx=(5,5))
        
        if len(self.incidence_entries)>10:
            self.add_i_e_pair_button.configure(state=DISABLED)
        self.add_i_e_pair_button.pack(pady=(10,10))
        
    def configure_pi(self):
        self.pi_commander.configure(self.i,self.e)
        timeout_s=BUFFER
        while timeout_s>0:
            if 'piconfigsuccess' in self.pi_listener.queue:
                self.pi_listener.queue.remove('piconfigsuccess')
                break
            time.sleep(INTERVAL)
            timeout_s-=INTERVAL
        if timeout_s<=0:
            dialog=ErrorDialog(self,label='Error: Failed to configure Raspberry Pi.\nCheck connections and/or restart scripts.')
            self.i=None
            self.e=None
            self.manual_automatic.set(0)
            self.complete_queue_item()
            return
        else:
            self.test_view.move_light(int(self.i))
            self.test_view.move_detector(int(self.e))
            self.complete_queue_item()
            if len(self.queue)>0:
                self.next_in_queue()
            else:
                self.unfreeze()
        
    def set_manual_automatic(self,override=False,force=-1):
        #TODO: save individually specified angles to config file
        
        if self.manual_automatic.get()==0 or force==0:
            if force==0:
                self.manual_automatic.set(0)
            self.range_frame.pack_forget()
            self.individual_angles_frame.pack()
            self.range_radio.configure(state = DISABLED)
            self.individual_range.set(0)
            
            while len(self.incidence_entries)>1:
                self.remove_i_e_pair(len(self.incidence_entries)-1)
            self.add_i_e_pair_button.configure(state=DISABLED)
           
            self.opt_button.pack(padx=self.padx,pady=self.pady, side=LEFT)
            self.wr_button.pack(padx=self.padx,pady=self.pady, side=LEFT) 
            self.spec_button.pack(padx=self.padx,pady=self.pady, side=LEFT)


            self.acquire_button.pack_forget()
        else:
            if force==1:
                self.manual_automatic.set(1)
            self.add_i_e_pair_button.configure(state=NORMAL)
            self.acquire_button.pack(padx=self.padx,pady=self.pady)
            self.spec_button.pack_forget()
            self.opt_button.pack_forget()
            self.wr_button.pack_forget()
            self.range_radio.configure(state = NORMAL)
            
            self.queue=[]
            valid_i=validate_int_input(self.i,-60,60)
            valid_e=validate_int_input(self.e,-75,75)
            if not valid_i or not valid_e:
                self.queue.append({self.configure_pi:[]})
                #self.queue.append({self.set_manual_automatic:[True]})
                dialog=IntInputDialog(self,title='Setup Required',label='Setup required: Unknown goniometer state.\n\nPlease enter the current viewing geometry and rotate the\nsample tray to the white reference position.\n',values={'Incidence':[self.i,self.min_i,self.max_i],'Emission':[self.e,self.min_e,self.max_e]},buttons={'ok':{self.next_in_queue:[]},'cancel':{self.set_manual_automatic:[override,0]}})
            else:
                dialog=Dialog(self,title='Setup Required',label='Please rotate the sample tray to the white reference position.',buttons={'ok':{}})
                
    
            

    
    def set_individual_range(self):
        #TODO: save individually specified angles to config file
        if self.individual_range.get()==0:
            self.range_frame.pack_forget()
            self.individual_angles_frame.pack()
        else:
            self.individual_angles_frame.pack_forget()
            self.range_frame.pack()
    
    def validate_input_dir(self,*args):
        pos=self.input_dir_entry.index(INSERT)
        input_dir=rm_reserved_chars(self.input_dir_entry.get())
        if len(input_dir)<len(self.input_dir_entry.get()):
            pos=pos-1
        self.input_dir_entry.delete(0,'end')
        self.input_dir_entry.insert(0,input_dir)
        self.input_dir_entry.icursor(pos)
        
    def validate_output_dir(self):
        pos=self.output_dir_entry.index(INSERT)
        output_dir=rm_reserved_chars(self.output_dir_entry.get())
        if len(output_dir)<len(self.output_dir_entry.get()):
            pos=pos-1
        self.output_dir_entry.delete(0,'end')
        self.output_dir_entry.insert(0,output_dir)
        self.output_dir_entry.icursor(pos)
        
    def validate_output_filename(self,*args):
        pos=self.output_filename_entry.index(INSERT)
        filename=rm_reserved_chars(self.spec_output_filename_entry.get())
        filename=filename.strip('/').strip('\\')
        self.output_filename_entry.delete(0,'end')
        self.output_filename_entry.insert(0,filename)
        self.output_filename_entry.icursor(pos)
        
    def validate_spec_save_dir(self,*args):
        pos=self.spec_save_dir_entry.index(INSERT)
        spec_save_dir=rm_reserved_chars(self.spec_save_dir_entry.get())
        if len(spec_save_dir)<len(self.spec_save_dir_entry.get()):
            pos=pos-1
        self.spec_save_dir_entry.delete(0,'end')
        self.spec_save_dir_entry.insert(0,spec_save_dir)
        self.spec_save_dir_entry.icursor(pos)
    
    def validate_logfile(self,*args):
        pos=self.logfile_entry.index(INSERT)
        logfile=rm_reserved_chars(self.logfile_entry.get())
        if len(logfile)<len(self.logfile_entry.get()):
            pos=pos-1
        self.logfile_entry.delete(0,'end')
        self.logfile_entry.insert(0,logfile)
        self.logfile_entry.icursor(pos)

    def validate_basename(self,*args):
        pos=self.spec_basename_entry.index(INSERT)
        basename=rm_reserved_chars(self.spec_basename_entry.get())
        basename=basename.strip('/').strip('\\')
        self.spec_basename_entry.delete(0,'end')
        self.spec_basename_entry.insert(0,basename)
        self.spec_basename_entry.icursor(pos)
        
    def validate_startnum(self,*args):
        pos=self.spec_startnum_entry.index(INSERT)
        num=numbers_only(self.spec_startnum_entry.get())
        if len(num)>NUMLEN:
            num=num[0:NUMLEN]
        if len(num)<len(self.spec_startnum_entry.get()):
            pos=pos-1
        self.spec_startnum_entry.delete(0,'end')
        self.spec_startnum_entry.insert(0,num)
        self.spec_startnum_entry.icursor(pos)
        
    def validate_distance(self,i,e):
        try:
            i=int(i)
            e=int(e)
        except:
            return False
        if np.abs(i-e)<self.required_angular_separation:
            return False
        else:
            return True
        
    def clear(self):
        if self.manual_automatic.get()==0:
            self.unfreeze()
            self.active_incidence_entries[0].delete(0,'end')
            self.active_emission_entries[0].delete(0,'end')
            self.label_entry.delete(0,'end')
            
    def next_in_queue(self):
        dict=self.queue[0]
        for func in dict:
            args=dict[func]
            func(*args)
            
    def refresh(self):
        time.sleep(0.25)
        self.test_view.flip()
        self.master.update()
            
    def resize(self,window):
        if window.widget==self.master:
            reserve_width=500
            try:
                c_height=self.console_frame.winfo_height()
                width=self.console_frame.winfo_width()
                g_height=self.test_view.double_embed.winfo_height()
                if c_height<int(window.height/3)-10:
                    self.test_view.double_embed.configure(height=int(2*window.height/3))
                    self.console_frame.configure(height=int(window.height/3)+10)
                elif c_height>int(window.height/3)+10:
                    print('resize!')
                    self.test_view.double_embed.configure(height=int(2*window.height/3))
                    self.console_frame.configure(height=int(window.height/3)-10)

                    self.console_frame.configure(width=window.width-reserve_width)
                thread = Thread(target =self.refresh)
                thread.start()
                self.test_view.draw_circle(window.width-self.control_frame.winfo_width()-2,int(2*window.height/3)-10)
                self.test_view.flip()
            except AttributeError:
                #Happens when the program is just starting up and there is no view yet
                pass
            except ValueError:
                pass

    def finish_move(self):
        self.test_view.draw_circle()
          
    def complete_queue_item(self):
        self.queue.pop(0)

    def delete_placeholder_spectrum(self):
        lastnumstr=str(int(self.spec_startnum_entry.get())-1)
        while len(lastnumstr)<NUMLEN:
            lastnumstr='0'+lastnumstr
            
        self.spec_commander.delete_spec(self.spec_save_dir_entry.get(),self.spec_basename_entry.get(),lastnumstr)
        
        t=BUFFER
        while t>0:
            if 'rmsuccess' in self.spec_listener.queue:
                self.spec_listener.queue.remove('rmsuccess')
                self.log('\nSaved and deleted a garbage spectrum ('+self.spec_basename_entry.get()+lastnumstr+'.asd).')
                break
            elif 'rmfailure' in self.spec_listener.queue:
                self.spec_listener.queue.remove('rmfailure')
                self.log('\nError: Failed to remove placeholder spectrum ('+self.spec_basename_entry.get()+lastnumstr+'.asd. This data is likely garbage.')
                break
            t=t-INTERVAL
            time.sleep(INTERVAL)
        if t<=0:
            self.log('\nError: Operation timed out removing placeholder spectrum ('+self.spec_basename_entry.get()+lastnumstr+'.asd. This data is likely garbage.')
        self.complete_queue_item()
        self.next_in_queue()
        
    def rm_current(self):
        self.spec_commander.delete_spec(self.spec_save_dir_entry.get(),self.spec_basename_entry.get(),self.spec_startnum_entry.get())

        t=BUFFER
        while t>0:
            if 'rmsuccess' in self.spec_listener.queue:
                self.spec_listener.queue.remove('rmsuccess')

                return True
            elif 'rmfailure' in self.spec_listener.queue:
                self.spec_listener.queue.remove('rmfailure')
                return False
            t=t-INTERVAL
            time.sleep(INTERVAL)
        return False
        
    def choose_plot_file(self):
        file=self.plot_input_dir_entry.get()
        if self.remote.get():
            plot_file_explorer=RemoteFileExplorer(self, target=self.plot_input_dir_entry,title='Select a file',label='Select a file to plot',directories_only=False)
        else:
            if os.path.isdir(file):
                file = askopenfilename(initialdir=file,title='Select a file to plot')
            else:
                file=askopenfilename(initialdir=os.getcwd(),title='Select a file to plot')
            self.plot_input_dir_entry.delete(0,'end')
            self.plot_input_dir_entry.insert(0, file)
            
    def log(self, info_string, write_to_file=False):
        self.master.update()
        space=self.console_log.winfo_width()
        space=str(int(space/8.5))
        if int(space)<20:
            space=str(20)
        datestring=''
        datestringlist=str(datetime.datetime.now()).split('.')[:-1]
        for d in datestringlist:
            datestring=datestring+d
            
        while info_string[0]=='\n':
            info_string=info_string[1:]
            
        if '\n' in info_string:
            lines=info_string.split('\n')

            lines[0]=('{1:'+space+'}{0}').format(datestring,lines[0])
            for i in range(len(lines)):
                if i==0:
                    continue
                else:
                    lines[i]=('{1:'+space+'}{0}').format('',lines[i])
            info_string='\n'.join(lines)
        else:
            info_string=('{1:'+space+'}{0}').format(datestring,info_string)
            
        if info_string[-2:-1]!='\n':
            info_string+='\n'

        self.console_log.insert(END,info_string+'\n')
        self.console_log.see(END)
        if write_to_file:
            with open(self.log_filename,'a') as log:
                log.write(info_string)
                
    def freeze(self):
        for button in self.tk_buttons:
            button.configure(state='disabled')
        for entry in self.entries:
            entry.configure(state='disabled')
        for radio in self.radiobuttons:
            radio.configure(state='disabled')

    def unfreeze(self):
        for button in self.tk_buttons:
            button.configure(state='normal')
        for entry in self.entries:
            entry.configure(state='normal')
        for radio in self.radiobuttons:
            radio.configure(state='normal')
            
        if self.manual_automatic.get()==0:
            self.range_radio.configure(state='disabled')
            self.add_i_e_pair_button.configure(state='disabled')
            
    # def on_closing(self):
    #     if self.manual_automatic.get()==1:
    #         print('hi!')
    #         self.incidence_entries[0].delete(0,'end')
    #         self.incidence_entries[0].insert(0,'0')
    #         self.emission_entries[0].delete(0,'end')
    #         self.emission_entries[0].insert(0,'30')
    #         self.active_incidence_entries=[self.incidence_entries[0]]
    #         self.active_emission_entries=[self.emission_entries[0]]
    #         self.set_geom()
    #         
    #         self.queue=[]
    #         if self.e==None or self.i==None:
    #             self.master.destroy()
    #             exit()
    #         if int(self.e)<0:
    #             self.queue.append({self.detector_close:[]})
    #             self.queue.append({self.light_close:[]})
    #         else:
    #             self.queue.append({self.light_close:[]})  
    #             self.queue.append({self.detector_close:[]})
  
 #  #           self.next_in_queue()
    #     else:
    #         self.master.destroy()

            
            #dialog=Dialog(self, title='Please reset geometry on exit',label='Please manually set the goniometer to\n\nincidence=0\nemission=30',buttons={'ok':{self.master.destroy:[]}},width=500,height=250)
            
                    
    def light_close(self):
        self.pi_commander.move_light(self.active_incidence_entries[0].get())
        handler=CloseHandler(self)
        self.test_view.move_light(int(self.active_incidence_entries[0].get()))
    def detector_close(self):
        self.pi_commander.move_detector(self.active_emission_entries[0].get())
        handler=CloseHandler(self)
        self.test_view.move_detector(int(self.active_emission_entries[0].get()))

    
class Dialog:
    def __init__(self, controller, title, label, buttons, width=None, height=None,allow_exit=True, button_width=20, info_string=None, grab=True):
        
        self.controller=controller
        self.grab=grab
        if True:#self.grab:
            try:
                self.controller.freeze()
            except:
                print('failed to freeze')
        
        try:
            self.textcolor=self.controller.textcolor
            self.bg=self.controller.bg
            self.buttonbackgroundcolor=self.controller.buttonbackgroundcolor
            self.highlightbackgroundcolor=self.controller.highlightbackgroundcolor
            self.entry_background=self.controller.entry_background
            self.buttontextcolor=self.controller.buttontextcolor
            self.console_log=self.controller.console_log
            self.listboxhighlightcolor=self.controller.listboxhighlightcolor
            self.selectbackground=self.controller.selectbackground
            self.selectforeground=self.controller.selectforeground
        except:
            self.textcolor='black'
            self.bg='white'
            self.buttonbackgroundcolor='light gray'
            self.highlightbackgroundcolor='white'
            self.entry_background='white'
            self.buttontextcolor='black'
            self.console_log=None
            self.listboxhighlightcolor='light gray'
            self.selectbackground='light gray'
            self.selectforeground='black'
            

        
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
                
            #self.controller.master.iconify() 
            # if self.grab:
            #     pass
            #     try:
            #         self.top.grab_set()
            #     except:
            #         print('failed to grab')
        
        self.top.attributes('-topmost', 1)
        self.top.attributes('-topmost', 0)
                


        self.label_frame=Frame(self.top, bg=self.bg)
        self.label_frame.pack(side=TOP)
        self.__label = tk.Label(self.label_frame, fg=self.textcolor,text=label, bg=self.bg)
        self.set_label_text(label, log_string=info_string)
        self.__label.pack(pady=(10,10), padx=(10,10))
    
        self.button_width=button_width
        self.buttons=buttons
        self.set_buttons(buttons)

        self.top.wm_title(title)
        self.allow_exit=allow_exit
        self.top.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        if start_mainloop:
            self.top.mainloop()
            
        if controller!=None and info_string!=None:
            self.log(info_string)
    
    @property
    def label(self):
        return self.__label.cget('text')
        
    @label.setter
    def label(self, val):
        self.__label.configure(text=val)
        
        
    def set_title(self, newtitle):
        self.top.wm_title(newtitle)
    def set_label_text(self, newlabel, log_string=None):
        self.__label.config(fg=self.textcolor,text=newlabel)
        if log_string != None and self.controller!=None:
            self.log(log_string)
            #self.controller.console_log.insert(END, info_string)
        
    def set_buttons(self, buttons, button_width=None):
        self.buttons=buttons
        if button_width==None:
            button_width=self.button_width
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
            elif 'cancel_queue' in button.lower():
                self.cancel_queue_button=Button(self.button_frame, fg=self.textcolor,text='Cancel',command=self.cancel_queue, width=self.button_width)
                self.cancel_queue_button.pack(side=LEFT, padx=(10,10), pady=(10,10))
                self.tk_buttons.append(self.cancel_button)
            elif 'retry' in button.lower():
                self.retry_button=Button(self.button_frame, fg=self.textcolor,text='Retry',command=self.retry, width=self.button_width)
                self.retry_button.pack(side=LEFT, padx=(10,10), pady=(10,10))
                self.tk_buttons.append(self.retry_button)
            elif 'exit' in button.lower():
                self.exit_button=Button(self.button_frame, fg=self.textcolor,text='Exit',command=self.exit, width=self.button_width)
                self.exit_button.pack(side=LEFT, padx=(10,10), pady=(10,10))
                self.tk_buttons.append(self.exit_button)
            elif 'work offline' in button.lower():
                self.offline_button=Button(self.button_frame, fg=self.textcolor,text='Work offline',command=self.work_offline, width=self.button_width)
                self.offline_button.pack(side=LEFT, padx=(10,10), pady=(10,10))
                self.tk_buttons.append(self.offline_button)
            elif 'pause' in button.lower():
                self.pause_button=Button(self.button_frame,fg=self.textcolor,text='Pause',command=self.pause,width=self.button_width)
                self.pause_button.pack(side=LEFT,padx=(10,10),pady=(10,10))
                self.tk_buttons.append(self.pause_button)
        
            elif 'continue' in button.lower():
                self.continue_button=Button(self.button_frame,fg=self.textcolor,text='Continue',command=self.cont,width=self.button_width)
                self.continue_button.pack(side=LEFT,padx=(10,10),pady=(10,10))
                self.tk_buttons.append(self.continue_button)
                
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
        if self.allow_exit:
            self.controller.unfreeze()
            self.top.destroy()
            
    def close(self):
        #Might fail if controller==None (happens if server isn't connected at startup)
        try:
            self.controller.unfreeze()
        except:
            pass
        self.top.destroy()
    
    def retry(self):
        self.close()
        dict=self.buttons['retry']
        self.execute(dict,False)
        
    def exit(self):
        self.top.destroy()
        exit()
        
    def cont(self):
        dict=self.buttons['continue']
        self.execute(dict,close=False)
        
    def pause(self):
        dict=self.buttons['pause']
        self.execute(dict,close=False)

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
        
    def cancel_queue(self):
        dict=self.buttons['cancel_queue']
        self.execute(dict,close=False)
        
    def execute(self,dict,close=True):
        for func in dict:
            args=dict[func]
            func(*args)

        if close:
            self.close()
    
    def work_offline(self):
        self.close()
        dict=self.buttons['work offline']
        self.execute(dict,close=False)
        
class WaitDialog(Dialog):
    def __init__(self, controller, title='Working...', label='Working...', buttons={}):
        super().__init__(controller, title, label,buttons,width=400, height=150, allow_exit=False)
        
        self.frame=Frame(self.top, bg=self.bg, width=200, height=30)
        self.frame.pack()
  
        style=ttk.Style()
        style.configure('Horizontal.TProgressbar', background='white')
        self.pbar = ttk.Progressbar(self.frame, mode='indeterminate', name='pb2', style='Horizontal.TProgressbar' )
        self.pbar.start([10])
        self.pbar.pack(padx=(10,10),pady=(10,10))
        
        
    def interrupt(self,label):
        self.set_label_text(label)
        self.pbar.stop()
        self.set_buttons({'ok':{}})#self.controller.unfreeze:[]}})
        
    def reset(self, title='Working...', label='Working...', buttons={}):
        self.set_label_text(label)
        self.set_buttons(buttons)
        self.set_title(title)
        self.pbar.start([10])

class CommandHandler():
    def __init__(self, controller, title='Working...', label='Working...', buttons={}, timeout=30):
        self.controller=controller
        self.label=label
        self.title=title
        #Either update the existing wait dialog, or make a new one.
        if label=='test':
            print('testy test!')
        try:
            self.controller.wait_dialog.reset(title=title, label=label, buttons=buttons)
        except:
            self.controller.wait_dialog=WaitDialog(controller,title,label)
        self.wait_dialog=self.controller.wait_dialog 
        self.controller.freeze()
        
        if self.controller.manual_automatic.get()==1 and len(self.controller.queue)>1:
            buttons={
                'pause':{
                    self.pause:[]
                },
                'cancel_queue':{
                    self.cancel:[]
                }
            }
            self.wait_dialog.set_buttons(buttons)

        

        
        #We'll keep track of elapsed time so we can cancel the operation if it takes too long
        self.t0=time.clock()
        self.t=time.clock()
        self.timeout_s=timeout
        
        
        #The user can pause or cancel if we're executing a list of commands.
        self.pause=False
        self.cancel=False

        #A Listener object is always running a loop in a separate thread. It  listens for files dropped into a command folder and changes its attributes based on what it finds.
        self.timeout_s=timeout
        

        #Start the wait function, which will watch the listener to see what attributes change and react accordingly. If this isn't in its own thread, the dialog box doesn't pop up until after it completes.
        thread = Thread(target =self.wait)
        thread.start()
        
    @property
    def timeout_s(self):
        return self.__timeout_s
        
    @timeout_s.setter
    def timeout_s(self, val):
        self.__timeout_s=val
        
    def wait(self):
        while True:
            print('waiting in super...')
            self.timeout_s-=1
            if self.timeout<0:
                self.timeout()
            time.sleep(1)
               
    def timeout(self, log_string=None, retry=True):
        if log_string==None:
            self.controller.log('Error: Operation timed out')
        else:
            self.controller.log(log_string)
            
        self.wait_dialog.interrupt('Error: Operation timed out')
        if retry:
            buttons={
                'retry':{
                    self.controller.next_in_queue:[]
                },
                'cancel':{
                    self.finish:[]
                }
            }
            self.wait_dialog.set_buttons(buttons)

    def finish(self):
        self.wait_dialog.close()
        

    def pause(self):
        self.pause=True
        self.wait_dialog.label='Pausing...'
    
    def cancel(self):
        self.cancel=True
        self.wait_dialog.label='Canceling...'
        
    def interrupt(self,label, info_string=None, retry=False):
        self.allow_exit=True
        self.wait_dialog.interrupt(label)
        if info_string!=None:
            self.log(info_string)
        if retry:
            buttons={
                'retry':{
                    self.controller.next_in_queue:[]
                },
                'cancel':{
                    self.finish:[]
                }
            }
            self.wait_dalog.set_buttons(buttons)
        self.controller.freeze()

        
    def remove_retry(self):
        self.controller.wait_dialog=None
        removed=self.controller.rm_current()
        if removed: 
            self.controller.log('Warning: overwriting '+self.controller.spec_save_path+'\\'+self.controller.spec_basename+self.controller.spec_startnum+'.asd.')
            
            #If we are retrying taking a spectrum or white references, don't do input checks again.
            if self.controller.take_spectrum in self.controller.queue[0]:
                garbage=self.controller.queue[0][self.controller.take_spectrum][2]
                self.controller.queue[0]={self.controller.take_spectrum:[True,True,garbage]}
            elif self.controller.wr in self.controller.queue[0]:
                self.controller.queue[0]={self.controller.wr:[True,True]}
            self.controller.next_in_queue()
        else:
            dialog=ErrorDialog(self.controller,label='Error: Failed to remove file. Choose a different base name,\nspectrum number, or save directory and try again.')
            #self.wait_dialog.set_buttons({'ok':{}})
            
    def success(self,close=True):
        
        self.controller.complete_queue_item()
        if self.cancel:
            self.interrupt('Canceled.')
        elif self.pause:
            buttons={
                'continue':{
                    self.controller.next_in_queue:[]
                },
                'cancel':{
                    self.finish:[]
                }
            }
            self.interrupt('Paused.')
            self.wait_dialog.set_buttons(buttons)
        elif len(self.controller.queue)>0:
            self.controller.next_in_queue()
        else:
            self.interrupt('Success!')
            
    def set_text(self,widget, text):
        widget.configure(state='normal')
        widget.delete(0,'end')
        widget.insert(0,text)
        widget.configure(state='disabled')
            

class InstrumentConfigHandler(CommandHandler):
    def __init__(self, controller, title='Configuring instrument...', label='Configuring instrument...', timeout=20):
        self.listener=controller.spec_listener
        super().__init__(controller, title, label,timeout=timeout)

    def wait(self):
        while self.timeout_s>0:
            if 'iconfigsuccess' in self.listener.queue:
                self.listener.queue.remove('iconfigsuccess')
                self.success()
                return
            elif 'iconfigfailure' in self.listener.queue:
                self.listener.queue.remove('iconfigfailure')
                self.interrupt('Error: Failed to configure instrument.',retry=True)
                self.controller.log('Error: Failed to configure instrument.')
                return
                
            time.sleep(INTERVAL)
            self.timeout_s-=INTERVAL
        self.timeout()

    def success(self):
        self.controller.spec_config_count=self.controller.instrument_config_entry.get()

        self.controller.log('Instrument configured to average  '+str(self.controller.spec_config_count)+' spectra.')

        super(InstrumentConfigHandler, self).success()
        
class OptHandler(CommandHandler):
    def __init__(self, controller, title='Optimizing...', label='Optimizing...'):

        if controller.spec_config_count!=None:
            timeout_s=int(controller.spec_config_count)/9+10+BUFFER
        else:
            timeout_s=1000
        self.listener=controller.spec_listener
        super().__init__(controller, title, label,timeout=timeout_s)

    def wait(self):
        while self.timeout_s>0:
            if 'nonumspectra' in self.listener.queue:
                self.listener.queue.remove('nonumspectra')
                self.controller.queue.append(self.controller.configure_instrument)
                self.controller.configure_instrument()
                #self.finish()
                return
                
            if 'optsuccess' in self.listener.queue:
                self.listener.queue.remove('optsuccess')
                self.success()
                return
            elif 'optfailure' in self.listener.queue:
                self.listener.queue.remove('optfailure')
                self.interrupt('Error: There was a problem with\noptimizing the instrument.',retry=True)
                self.controller.log('Error: There was a problem with optimizing the instrument.')
                return
            time.sleep(INTERVAL)
            self.timeout_s-=INTERVAL
        self.timeout()
                
    def success(self):
        self.controller.opt_time=int(time.time())
        self.controller.log('Instrument optimized.')# \n\ti='+self.controller.active_incidence_entries[0].get()+'\n\te='+self.controller.active_emission_entries[0].get())
        super(OptHandler, self).success()

        
class WhiteReferenceHandler(CommandHandler):
    def __init__(self, controller, title='White referencing...',
    label='White referencing...'):
        timeout_s=int(controller.spec_config_count)/9+6+BUFFER
        self.listener=controller.spec_listener
        super().__init__(controller, title, label,timeout=timeout_s)
        

    def wait(self):
        while self.timeout_s>0:
            if 'wrsuccess' in self.listener.queue:
                self.listener.queue.remove('wrsuccess')
                self.success()
                return
            elif 'nonumspectra' in self.listener.queue:
                self.listener.queue.remove('nonumspectra')
                self.controller.queue.append({self.controller.configure_instrument:[]})
                self.controller.configure_instrument()
                return
            elif 'noconfig' in self.listener.queue:
                self.listener.queue.remove('noconfig')
                self.controller.queue.append({self.controller.set_save_config:[]})
                self.controller.set_save_config()
                return
                
            elif 'wrfailedfileexists' in self.listener.queue:
                self.listener.queue.remove('wrfailedfileexists')
                self.interrupt('Error: File exists.\nDo you want to overwrite this data?')
                buttons={
                    'yes':{
                        self.remove_retry:[]
                    },
                    'no':{
                    }
                }
                    
                self.wait_dialog.set_buttons(buttons,button_width=20)
                return
            time.sleep(INTERVAL)
            self.timeout_s-=INTERVAL
        self.timeout()
                
    def success(self):
        self.controller.wr_time=int(time.time())
        super(WhiteReferenceHandler, self).success()
            
class ProcessHandler(CommandHandler):
    def __init__(self, controller, title='Processing...', label='Processing...'):
        self.listener=controller.spec_listener
        super().__init__(controller, title, label,timeout=60+BUFFER)

    def wait(self):
        while self.timeout_s>0:
            if 'processsuccess' in self.listener.queue:
                self.listener.queue.remove('processsuccess')
                self.log('Files processed.\n\t'+self.controller.output_dir_entry.get()+'/'+self.controller.output_file_entry.get())
                self.interrupt('Success!')
                return
                
            elif 'processerrorfileexists' in self.listener.queue:
                self.controller.listener.queue.remove('processerrorfileexists')
                self.interrupt('Error processing files: Output file already exists')
                self.log('Error processing files: output file exists.')
                return
                
            elif 'processerrorwropt' in self.listener.queue:
                self.listener.queue.remove('processerrorwropt')
                self.interrupt('Error processing files.\nDid you optimize and white reference before collecting data?')
                self.log('Error processing files')
                return
                
            elif 'processerror' in self.listener.queue:
                self.listener.queue.remove('processerror')
                self.interrupt('Error processing files.\nAre you sure directories exist?\n')
                self.log('Error processing files')
                return
                
            time.sleep(INTERVAL)
            self.timeout_s-=INTERVAL
        self.timeout()
        
        
        
class CloseHandler(CommandHandler):
    def __init__(self, controller, title='Closing...', label='Setting to default geometry and closing...', buttons={'cancel':{}}):
        self.listener=controller.pi_listener
        print('handling close!')
        super().__init__(controller, title, label,timeout=60+BUFFER)
        
    def wait(self):
        while self.timeout_s>0:
            if 'donemoving' in self.listener.queue:
                self.listener.queue.remove('donemoving')
                self.success()
                return

            time.sleep(INTERVAL)
            self.timeout_s-=INTERVAL
        
        self.timeout()
    def success(self):
        print('success')
        print(self.controller.queue)
        self.controller.complete_queue_item()
        if len(self.controller.queue)==0:
            self.interrupt('Finished. Ready to exit')
            self.wait_dialog.set_buttons({'exit':{exit_func:[]}})
        else:
            self.controller.next_in_queue()
            
class MotionHandler(CommandHandler):
    def __init__(self, controller, title='Moving...', label='Moving...', buttons={'cancel':{}}):
        self.listener=controller.pi_listener
        super().__init__(controller, title, label,timeout=45+BUFFER)


    def wait(self):
        while self.timeout_s>0:
            if 'donemoving' in self.listener.queue:
                self.listener.queue.remove('donemoving')
                self.success()
                return

            time.sleep(INTERVAL)
            self.timeout_s-=INTERVAL
        
        self.timeout()
        
    def success(self):
        if 'detector' in self.label:
            self.controller.log('Goniometer moved to an emission angle of'+self.controller.active_emission_entries[0].get()+' degrees.')
        elif 'light' in self.label:
            self.controller.log('Goniometer moved to an incidence angle of'+self.controller.active_incidence_entries[0].get()+' degrees.')
            
        elif 'tray' in self.label:
            self.controller.log('Sample tray moved.')
        else:
            self.controller.log('Something moved! Who knows what?')
        super(MotionHandler,self).success()
        
        
class SaveConfigHandler(CommandHandler):
    def __init__(self, controller, title='Setting Save Configuration...', label='Setting save configuration...', timeout=30):
        self.listener=controller.spec_listener
        self.keep_around=False
        self.unexpected_files=[]
        self.listener.new_dialogs=False
        super().__init__(controller, title, label=label,timeout=timeout)
        
    def wait(self):
        t=30
        while 'donelookingforunexpected' not in self.listener.queue and t>0:
            t=t-INTERVAL
            time.sleep(INTERVAL)
        if t<=0:
            self.timeout()
            return
            
        if len(self.listener.unexpected_files)>0:
            self.keep_around=True
            self.unexpected_files=list(self.listener.unexpected_files)
            self.listener.unexpected_files=[]
            
        self.listener.new_dialogs=True
        self.listener.queue.remove('donelookingforunexpected')

        
        while self.timeout_s>0:
            self.timeout_s-=INTERVAL
            if 'saveconfigsuccess' in self.listener.queue:
                self.listener.queue.remove('saveconfigsuccess')
                self.success()
                return
                
            elif 'saveconfigfailedfileexists' in self.listener.queue:
                self.listener.queue.remove('saveconfigfailedfileexists')
                self.interrupt('Error: File exists.\nDo you want to overwrite this data?')
                buttons={
                    'yes':{
                        self.remove_retry:[]
                    },
                    'no':{
                        self.finish:[]
                    }
                }
                    
                self.wait_dialog.set_buttons(buttons,button_width=20)
                return

            elif 'saveconfigfailed' in self.listener.queue:
                self.listener.queue.remove('saveconfigfailed')
                self.interrupt('Error: There was a problem with\nsetting the save configuration.\nIs the spectrometer connected?',retry=True)
                self.log('Error: There was a problem setting the save configuration.')
                self.controller.spec_save_path=''
                self.controller.spec_basename=''
                self.controller.spec_num=None
                return
                
            time.sleep(INTERVAL)
            
        self.timeout(log_string='Error: Operation timed out while waiting to set save configuration.')
        

    def success(self):
        self.controller.spec_save_path=self.controller.spec_save_dir_entry.get()
        self.controller.spec_basename = self.controller.spec_basename_entry.get()
        spec_num=self.controller.spec_startnum_entry.get()
        self.controller.spec_num=int(spec_num)
        
        self.allow_exit=True
        self.controller.log('Save configuration set.\n\tDirectory: '+self.controller.spec_save_dir_entry.get()+'\n\tBasename: '+self.controller.spec_basename_entry.get())
        
        if self.keep_around:
            dialog=WaitDialog(self.controller, title='Warning: Untracked Files',buttons={'ok':[]})
            dialog.top.geometry('400x300')
            dialog.interrupt('Save configuration was set successfully,\nbut there are untracked files in the\ndata directory. Do these belong here?')
            
            self.controller.log('Untracked files in data directory:\n'+'\n\t'.join(self.unexpected_files))
            
            listbox=ScrollableListbox(dialog.top,self.wait_dialog.bg,self.wait_dialog.entry_background, self.wait_dialog.listboxhighlightcolor,)
            for file in self.unexpected_files:
                listbox.insert(END,file)
                
            listbox.config(height=1)

        super(SaveConfigHandler, self).success()
        

                
            
    
class SpectrumHandler(CommandHandler):
    def __init__(self, controller, title='Saving Spectrum...', label='Saving spectrum...'):
        timeout=int(controller.spec_config_count)/9+BUFFER
        self.listener=controller.spec_listener
        super().__init__(controller, title, label, timeout=timeout)
        
    def wait(self):
        #old_files=list(self.controller.listener.saved_files)
        while self.timeout_s>0:
                

            if 'failedtosavefile' in self.listener.queue:
                self.interrupt('Error: Failed to save file.\nAre you sure the spectrometer is connected?',retry=True)
                self.listener.queue.remove('failedtosavefile')
                return

            elif 'noconfig' in self.listener.queue:
                self.listener.queue.remove('noconfig')
                self.controller.queue.append({self.controller.set_save_config:[]})
                self.controller.set_save_config()#self.controller.take_spectrum, [True])
                return
                
            elif 'nonumspectra' in self.listener.queue:
                self.listener.queue.remove('nonumspectra')
                self.controller.queue.append({self.controller.configure_instrument:[]})
                self.controller.configure_instrument()
                return
                
            elif 'savedfile' in self.listener.queue:
                self.listener.queue.remove('savedfile')

                self.success()
                return
            elif 'savespecfailedfileexists' in self.listener.queue:
                self.listener.queue.remove('savespecfailedfileexists')
                self.interrupt('Error: File exists.\nDo you want to overwrite this data?')
                
                buttons={
                    'yes':{
                        self.remove_retry:[]
                    },
                    'no':{}
                }
                    
                self.wait_dialog.set_buttons(buttons,button_width=20)
                return
                
            time.sleep(INTERVAL)
            self.timeout_s-=INTERVAL
            
        self.timeout(log_string='Error: Operation timed out while waiting to save spectrum',retry=True)

        
    def success(self):
        self.controller.spec_num+=1
        self.controller.spec_startnum_entry.delete(0,'end')
        spec_num_string=str(self.controller.spec_num)
        while len(spec_num_string)<NUMLEN:
            spec_num_string='0'+spec_num_string
        self.set_text(self.controller.spec_startnum_entry,spec_num_string)
        self.allow_exit=True
        numstr=str(self.controller.spec_num-1)
        while len(numstr)<NUMLEN:
            numstr='0'+numstr
            
        if 'White reference' in self.controller.label_entry.get():
            info_string='White reference saved.'
        else:
            info_string='Spectrum saved.'

        info_string+='\n\tSpectra averaged: ' +str(self.controller.spec_config_count)+'\n\ti: '+self.controller.active_incidence_entries[0].get()+'\n\te: '+self.controller.active_emission_entries[0].get()+'\n\tfilename: '+self.controller.spec_save_path+'\\'+self.controller.spec_basename+numstr+'.asd'+'\n\tLabel: '+self.controller.label_entry.get()+'\n'
        print('Here are AAAAAAAAAAALLLLLLLLLLLLLLL remaining e')
        for entry in self.controller.active_emission_entries:
            print(entry.get())
        if 'garbage' in self.wait_dialog.label:
            pass
        else:
            self.controller.log(info_string,True)

        #Clear out 'White reference' if that was put in earlier to use for this spectrum.
        self.set_text(self.controller.label_entry,self.controller.current_label)    
        self.controller.clear()
        
        super(SpectrumHandler, self).success()
        
class ErrorDialog(Dialog):
    def __init__(self, controller, title='Error', label='Error!', buttons={'ok':{}}, listener=None,allow_exit=False, info_string=None, topmost=True, button_width=30, width=None,height=None):
        
        #buttons['ok']={controller.unfreeze:[]}
        
        self.listener=None
        if info_string==None:
            self.info_string=label+'\n'
        else:
            self.info_string=info_string
        if width==None or height==None:
            super().__init__(controller, title, label,buttons,allow_exit=False, info_string=None, button_width=button_width)#self.info_string)
        else:
            super().__init__(controller, title, label,buttons,allow_exit=False, info_string=None, button_width=button_width,width=width, height=height)
        if topmost==True:
            try:
                self.top.attributes("-topmost", True)
            except(Exception):
                print(str(Exception))

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
    def __init__(self,controller, target=None,title='Select a directory',label='Select a directory',buttons={'ok':{},'cancel':{}}, directories_only=True):

        super().__init__(controller, title=title, buttons=buttons,label=label, button_width=20)
        
        self.timeout_s=BUFFER
        self.controller=controller
        self.remote_directory_worker=self.controller.remote_directory_worker
        self.listener=self.controller.spec_listener
        self.target=target
        self.current_parent=None
        self.directories_only=directories_only
        
        self.nav_frame=Frame(self.top,bg=self.bg)
        self.nav_frame.pack()
        self.new_button=Button(self.nav_frame, fg=self.textcolor,text='New Folder',command=self.askfornewdir, width=10)
        self.new_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.new_button.pack(side=RIGHT, pady=(5,5),padx=(0,10))

        self.path_entry_var = StringVar()
        self.path_entry_var.trace('w', self.validate_path_entry_input)
        self.path_entry=Entry(self.nav_frame, width=50,bg=self.entry_background,textvariable=self.path_entry_var,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.path_entry.pack(padx=(5,5),pady=(5,5),side=RIGHT)
        self.back_button=Button(self.nav_frame, fg=self.textcolor,text='<-',command=self.back,width=1)
        self.back_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.back_button.pack(side=RIGHT, pady=(5,5),padx=(10,0))
        
        # self.scroll_frame=Frame(self.top,bg=self.bg)
        # self.scroll_frame.pack(fill=BOTH, expand=True)
        # self.scrollbar = Scrollbar(self.scroll_frame, orient=VERTICAL)
        # self.listbox = Listbox(self.scroll_frame,yscrollcommand=self.scrollbar.set, selectmode=SINGLE,bg=self.entry_background, selectbackground=self.listboxhighlightcolor, height=15)

        #   self.scrollbar.config(command=self.listbox.yview)
        # self.scrollbar.pack(side=RIGHT, fill=Y,padx=(0,10))
        # self.listbox.pack(side=LEFT,expand=True, fill=BOTH,padx=(10,0))
        self.listbox=ScrollableListbox(self.top,self.bg,self.entry_background, self.listboxhighlightcolor,)
        self.listbox.bind("<Double-Button-1>", self.expand)
        self.path_entry.bind('<Return>',self.go_to_path)
        
        if target.get()=='':
            self.expand(newparent='C:\\Users')
            self.current_parent='C:\\Users'
        else:
            if directories_only:
                self.expand(newparent=target.get().replace('/','\\'))
            else:
                path=target.get().replace('/','\\')
                if '\\' in path:
                    path_el=path.split('\\')
                    if '.' in path_el[-1]:
                        path='\\'.join(path_el[:-1])
                    self.expand(newparent=path)
                else:
                    self.expand(newparent=path)
            
    def validate_path_entry_input(self,*args):
        text=self.path_entry.get()
        text=rm_reserved_chars(text)

        self.path_entry.delete(0,'end')
        self.path_entry.insert(0,text)      
        
    def askfornewdir(self):
        input_dialog=InputDialog(self.controller, self)

    def mkdir(self, newdir):
        status=self.remote_directory_worker.mkdir(newdir)

        if status=='mkdirsuccess':
            self.expand(None,'\\'.join(newdir.split('\\')[0:-1]))
            self.select(newdir.split('\\')[-1])
        elif status=='mkdirfailedfileexists':
            dialog=ErrorDialog(self.controller,title='Error',label='Could not create directory:\n\n'+newdir+'\n\nFile exists.')
            self.expand(newparent=self.current_parent)
        elif status=='mkdirfailed':
            dialog=ErrorDialog(self.controller,title='Error',label='Could not create directory:\n\n'+newdir)
            self.expand(newparent=self.current_parent)
        
    def back(self):
        if len(self.current_parent)<4:
            return
        parent='\\'.join(self.current_parent.split('\\')[0:-1])
        self.expand(newparent=parent)
        
    def go_to_path(self, source):
        parent=self.path_entry.get().replace('/','\\')
        self.path_entry.delete(0,'end')
        self.expand(newparent=parent)
        
    
    def expand(self, source=None, newparent=None, buttons=None,select=None, timeout=5,destroy=False):
        global CMDNUM
        if newparent==None:
            index=self.listbox.curselection()[0]
            if self.listbox.itemcget(index, 'foreground')=='darkblue':
                return
            newparent=self.current_parent+'\\'+self.listbox.get(index)
        if newparent[1:2]!=':' or len(newparent)>2 and newparent[1:3]!=':\\':
            dialog=ErrorDialog(self.controller,title='Error: Invalid input',label='Error: Invalid input.\n\n'+newparent+'\n\nis not a valid filename.')
            return
        if newparent[-1]=='\\':
            newparent=newparent[:-1]
        #Send a command to the spec compy asking it for directory contents
        if self.directories_only==True:
            status=self.remote_directory_worker.get_contents(newparent)
        else:
            status=self.remote_directory_worker.get_contents(newparent)
        
        #if we succeeded, the status will be a list of the contents of the directory
        if type(status)==list:

            self.listbox.delete(0,'end')
            for dir in status:
                if dir[0:2]=='~:':
                    self.listbox.insert(END,dir[2:])
                    self.listbox.itemconfig(END, fg='darkblue')
                else:
                    self.listbox.insert(END,dir)

            self.current_parent=newparent
            
            self.path_entry.delete(0,'end')
            self.path_entry.insert('end',newparent)
            if select!=None:
                self.select(select)
            
            if destroy:
                self.close()

                
        elif status=='listdirfailed':
            if self.current_parent==None:
                self.current_parent='\\'.join(newparent.split('\\')[:-1])
                if self.current_parent=='':
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
        elif status=='listdirfailedpermission':
            dialog=ErrorDialog(self.controller,label='Error: Permission denied for\n'+newparent)
            return
        elif status=='timeout':
            dialog=ErrorDialog(self.controller, label='Error: Operation timed out.\nCheck that the automation script is running on the spectrometer computer.')
            
    def select(self,text):
        if '\\' in text:
            text=text.split('\\')[0]
            

        try:
            index = self.listbox.get(0, 'end').index(text)
        except:
            #time.sleep(0.5)
            print('except')
            #self.select(text)
            index=0

        self.listbox.selection_set(index)
        self.listbox.see(index)
        
    def ok(self):
        index=self.listbox.curselection()
        if len(index)>0 and self.directories_only:
            if self.listbox.itemcget(index[0], 'foreground')=='darkblue':
                index=[]
        elif len(index)==0 and not self.directories_only:
            return
                
        self.target.delete(0,'end')

        if self.directories_only:
            if len(index)>0 and self.path_entry.get()==self.current_parent:
    
                self.target.insert(0,self.current_parent+'\\'+self.listbox.get(index[0]))
                self.close()
            elif self.path_entry.get()==self.current_parent:
                self.target.insert(0,self.current_parent)
                self.close()
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
                self.expand(newparent=self.path_entry.get(), buttons=buttons, destroy=True)
                self.target.insert(0,self.current_parent)
        else:
            if len(self.listbox.curselection())>0 and self.path_entry.get()==self.current_parent and  self.listbox.itemcget(index[0], 'foreground')=='darkblue':
    
                self.target.insert(0,self.current_parent+'\\'+self.listbox.get(index[0]))
                self.close()
    

            
class RemoteDirectoryWorker():
    def __init__(self, spec_commander, read_command_loc, listener):
        self.read_command_loc=read_command_loc
        self.spec_commander=spec_commander
        self.listener=listener
        self.timeout_s=BUFFER
    
    def wait_for_contents(self,cmdfilename):
        #Wait to hear what the listener finds
        print('something wrong here!')
        print(cmdfilename)
        while self.timeout_s>0:
            #If we get a file back with a list of the contents, replace the old listbox contents with new ones.
            if cmdfilename in self.listener.queue:
                contents=[]
                with open(self.read_command_loc+cmdfilename,'r') as f:
                    next=f.readline().strip('\n')
                    while next!='':
                        contents.append(next)
                        next=f.readline().strip('\n')
                self.listener.queue.remove(cmdfilename)
                return contents
                
            elif 'listdirfailed' in self.listener.queue:
                self.listener.queue.remove('listdirfailed')
                return 'listdirfailed'
                
            elif 'listdirfailedpermission' in self.listener.queue:
                self.listener.queue.remove('listdirfailedpermission')
                return 'listdirfailedpermission'
            
            elif 'listfilesfailed' in self.listener.queue:
                self.listener.queue.remove('listfilesfailed')
                return 'listfilesfailed'
            
            time.sleep(INTERVAL)
            self.timeout_s-=INTERVAL 
        print('rats timed out')
        return 'timeout'
        
        
    #Assume parent has already been validated, but don't assume it exists
    def get_dirs(self,parent):
        cmdfilename=self.spec_commander.listdir(parent)
        return self.wait_for_contents(cmdfilename)
                
    def get_contents(self,parent):
        cmdfilename=self.spec_commander.list_contents(parent)
        return self.wait_for_contents(cmdfilename)
        
    def mkdir(self, newdir):
        self.spec_commander.mkdir(newdir)
                
        while True:
            if 'mkdirsuccess' in self.listener.queue:
                self.listener.queue.remove('mkdirsuccess')
                return 'mkdirsuccess'
            elif 'mkdirfailedfileexists' in self.listener.queue:
                self.listener.queue.remove('mkdirfailedfileexists')
                return 'mkdirfailedfileexists'
            elif 'mkdirfailed' in self.listener.queue:
                self.listener.queue.remove('mkdirfailed')
                return 'mkdirfailed'
                
        time.sleep(INTERVAL)

class ScrollableListbox(Listbox):
    def __init__(self, frame, bg, entry_background, listboxhighlightcolor):
        
        self.scroll_frame=Frame(frame,bg=bg)
        self.scroll_frame.pack(fill=BOTH, expand=True)
        self.scrollbar = Scrollbar(self.scroll_frame, orient=VERTICAL)
        self.scrollbar.pack(side=RIGHT, fill=Y,padx=(0,10))
        self.scrollbar.config(command=self.yview)
        
        super().__init__(self.scroll_frame,yscrollcommand=self.scrollbar.set, selectmode=SINGLE,bg=entry_background, selectbackground=listboxhighlightcolor, height=15)
        self.pack(side=LEFT,expand=True, fill=BOTH,padx=(10,0))

class ScrollableListboxBroken(ttk.Treeview):
    def __init__(self, frame, bg, entry_background, listboxhighlightcolor):
        
        self.scroll_frame=Frame(frame,bg=bg)
        self.scroll_frame.pack(fill=BOTH, expand=True)
        self.scrollbar = Scrollbar(self.scroll_frame, orient=VERTICAL)
        self.scrollbar.pack(side=RIGHT, fill=Y,padx=(0,10))
        self.scrollbar.config(command=self.yview)
        
        super().__init__(self.scroll_frame,yscrollcommand=self.scrollbar.set, selectmode='browse',  height=15)
        self.pack(side=LEFT,expand=True, fill=BOTH,padx=(10,0))
        
        # background=entry_background,
        # selectbackground=listboxhighlightcolor,

                
class IntInputDialog(Dialog):
    def __init__(self,controller,title,label,values={},buttons={'ok':{},'cancel':{}}):
        super().__init__(controller,title,label,buttons,allow_exit=False)
        self.values=values
        self.entry_frame=Frame(self.top,bg=self.bg)
        self.entry_frame.pack(pady=(10,20))
        self.labels={}
        self.entries={}
        self.mins={}
        self.maxes={}
        for val in values:
            frame=Frame(self.entry_frame,bg=self.bg)
            frame.pack(pady=(5,5))
            self.labels[val]=Label(frame, text='{0:>10}'.format(val)+': ',fg=self.textcolor,bg=self.bg)
            self.labels[val].pack(side=LEFT,padx=(3,3))
            self.entries[val]=Entry(frame,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
            self.entries[val].pack(side=LEFT)
            
        self.set_buttons(buttons)
            
    def ok(self):
        bad_vals=[]
        for val in self.values:
            self.mins[val]=self.values[val][1]
            self.maxes[val]=self.values[val][2]
            valid=validate_int_input(self.entries[val].get(),self.mins[val],self.maxes[val])
            valid_sep=True
            if valid:
                #self.values[val][0]=self.entries[val].get()
                if val=='Incidence':
                    valid_sep=self.controller.validate_distance(self.entries['Incidence'].get(),self.entries['Emission'].get())
                    if valid_sep:
                        self.controller.i=self.entries[val].get()
                elif val=='Emission':
                    valid_sep=self.controller.validate_distance(self.entries['Incidence'].get(),self.entries['Emission'].get())
                    if valid_sep:
                        self.controller.e=self.entries[val].get()

            else:
                bad_vals.append(val)
        if len(bad_vals)==0 and valid_sep:
            self.top.destroy()
            dict=self.buttons['ok']
            for func in dict:
                args=dict[func]
                func(*args)
        else:
            err_str='Error: Invalid '
            if len(bad_vals)==1:
                for val in bad_vals:
                    err_str+=val.lower()+' value.\nPlease enter a number from '+str(self.mins[val]) +' to '+str(self.maxes[val])+'.'
            elif valid_sep:
                err_str+='input. Please enter the following:\n\n'
                for val in bad_vals:
                    err_str+=val+' from '+str(self.mins[val])+' to '+str(self.maxes[val])+'\n'
            else:
                err_str+='angular separation\n(must be at least '+str(self.controller.required_angular_separation)+' degrees).'
            dialog=ErrorDialog(self.controller,title='Error: Invalid Input',label=err_str)
        
            
class InputDialog(Dialog):
    def __init__(self, controller, fexplorer,label='Enter input', title='Enter input'):
        super().__init__(controller,label=label,title=title, buttons={'ok':{self.get:[]},'cancel':{}},button_width=15)
        self.dir_entry=Entry(self.top,width=40,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
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
        
class Listener(Thread):
    def __init__(self, read_command_loc, test=False):
        Thread.__init__(self)
        self.read_command_loc=read_command_loc
        self.controller=None
        self.queue=[]
        if not OFFLINE:
            self.cmdfiles0=os.listdir(self.read_command_loc)

    def run(self):
        while True:
            if not OFFLINE:
                connection=self.connection_checker.check_connection(False)
            time.sleep(INTERVAL)
            
    def listen(self):
        pass

    def set_controller(self,controller):
        self.controller=controller
        self.connection_checker.controller=controller

    
class PiListener(Listener):
    def __init__(self, read_command_loc, test=False):

        super().__init__(read_command_loc)
        self.connection_checker=PiConnectionChecker(read_command_loc,controller=self.controller, func=self.listen)
            
    def listen(self):
        self.cmdfiles=os.listdir(self.read_command_loc)  
        if self.cmdfiles==self.cmdfiles0:
            pass
        else:
            for cmdfile in self.cmdfiles:
                if cmdfile not in self.cmdfiles0:
                    cmd, params=decrypt(cmdfile)

                    print('Pi read command: '+cmd)
                    if 'donemoving' in cmd:
                        self.queue.append('donemoving')
                    elif 'piconfigsuccess' in cmd:
                        self.queue.append('piconfigsuccess')
        self.cmdfiles0=list(self.cmdfiles)

                        
                        
class SpecListener(Listener):
    def __init__(self, read_command_loc):
        super().__init__(read_command_loc)
        self.connection_checker=SpecConnectionChecker(read_command_loc,controller=self.controller, func=self.listen)
        self.unexpected_files=[]
        self.wait_for_unexpected_count=0

        self.alert_lostconnection=True
        self.new_dialogs=True
        

            
    def listen(self):
        self.cmdfiles=os.listdir(self.read_command_loc)  
        if self.cmdfiles==self.cmdfiles0:
            pass
        else:
            for cmdfile in self.cmdfiles:
                if cmdfile not in self.cmdfiles0:
                    cmd, params=decrypt(cmdfile)

                    print('Spec read command: '+cmd)
                    print('fof')
                    if 'savedfile' in cmd:
                        #self.saved_files.append(params[0])
                        self.queue.append('savedfile')
                    elif 'listdir' in cmd:
                        print('should get here!')
                        if 'listdirfailed' in cmd:
                            if 'permission' in cmd:
                                self.queue.append('listdirfailedpermission')
                            else:
                                self.queue.append('listdirfailed')
                        else:
                            print('here is the file you are looking ofr')
                            print(cmdfile)
                            self.queue.append(cmdfile)  
                    elif 'wrfailedfileexists' in cmd:
                        self.queue.append('wrfailedfileexists')
                        
                    elif 'failedtosavefile' in cmd:
                        self.queue.append('failedtosavefile')
                        
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
                        self.queue.append('saveconfigerror')
                    
                    elif 'saveconfigsuccess' in cmd:
                        self.queue.append('saveconfigsuccess')
                    
                    elif 'noconfig' in cmd:
                        print("Spectrometer computer doesn't have a file configuration saved (python restart over there?). Setting to current configuration.")
                        self.queue.append('noconfig')
                    
                    elif 'nonumspectra' in cmd:
                        print("Spectrometer computer doesn't have an instrument configuration saved (python restart over there?). Setting to current configuration.")
                        self.queue.append('nonumspectra')
                    
                    elif 'saveconfigfailedfileexists' in cmd:
                        self.queue.append('saveconfigfailedfileexists')
                    elif 'savespecfailedfileexists' in cmd:
                        self.queue.append('savespecfailedfileexists')
                    
    
                    elif 'listcontents' in cmd:
                        self.queue.append(cmdfile)  
                    
                    elif 'mkdirsuccess' in cmd:
                        self.queue.append('mkdirsuccess')
                    
                    elif 'mkdirfailedfileexists' in cmd:
                        self.queue.append('mkdirfailedfileexists')
                    elif 'mkdirfailed' in cmd:
                        self.queue.append('mkdirfailed')
                    
                    elif 'iconfigsuccess' in cmd:
                        self.queue.append('iconfigsuccess')
                        
                    elif 'datacopied' in cmd:
                        self.queue.append('datacopied')
                        
                    elif 'datafailure' in cmd:
                        self.queue.append('datafailure')
                    
                    elif 'iconfigfailure' in cmd:
                        self.queue.append('iconfigfailure')
                        
                    elif 'optsuccess' in cmd:
                        self.queue.append('optsuccess')
                    
                    elif 'optfailure' in cmd:
                        self.queue.append('optfailure')
                        
                    elif 'notwriteable' in cmd:
                        self.queue.append('notwriteable')
                        
                    elif 'yeswriteable' in cmd:
                        self.queue.append('yeswriteable')
                        
                    elif 'lostconnection' in cmd:
                        print('lostconnection')
                        os.remove(self.read_command_loc+cmdfile)
                        self.cmdfiles.remove(cmdfile)
                        if self.alert_lostconnection:
                            self.alert_lostconnection=False

                            buttons={
                                'retry':{
                                    self.set_alert_lostconnection:[True]
                                    },
                                'work offline':{
                                },
                                'exit':{
                                    exit_func:[]
                                }
                            }
                            try:
                                dialog=ErrorDialog(controller=self.controller, title='Lost Connection',label='Error: RS3 lost connection with the spectrometer.\nCheck that the spectrometer is on.',buttons=buttons,button_width=15)
                            except:
                                print('Ignoring an error in Listener when I make a new error dialog')
                    elif 'rmsuccess' in cmd:
                        self.queue.append('rmsuccess')
    
                    elif 'rmfailure' in cmd:
                        self.queue.append('rmfailure')
                        
                    elif 'piconfigsuccess' in cmd:
                        self.queue.append('piconfigsuccess')
                        
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

        self.cmdfiles0=list(self.cmdfiles)

    def set_alert_lostconnection(self,bool):
        self.alert_lostconnection=bool
        
      
def decrypt(encrypted):
    cmd=encrypted.split('&')[0]
    params=encrypted.split('&')[1:]
    i=0
    for param in params:
        params[i]=param.replace('+','\\').replace('=',':')
        params[i]=params[i].replace('++','+')
        i=i+1
    return cmd,params
    
# def encrypt(cmd, num, parameters=[]):
#     filename=cmd+str(num)
#     for param in parameters:
#         param=param.replace('/','+')
#         param=param.replace('\\','+')
#         param=param.replace(':','=')
#         filename=filename+'&'+param
#     return filename
    
def rm_reserved_chars(input):
    output= input.replace('&','').replace('+','').replace('=','').replace('$','').replace('^','').replace('*','').replace('(','').replace(',','').replace(')','').replace('@','').replace('!','').replace('#','').replace('{','').replace('}','').replace('[','').replace(']','').replace('|','').replace(',','').replace('?','').replace('~','').replace('"','').replace("'",'').replace(';','').replace('`','')
    return output
    
def numbers_only(input):
    output=''
    for digit in input:
        if digit=='1' or digit=='2' or digit=='3' or digit=='4'or digit=='5'or digit=='6' or digit=='7' or digit=='8' or digit=='9' or digit=='0':
            output+=digit
    return output
    
class Commander():
    def __init__(self, write_command_loc):
        self.write_command_loc=write_command_loc
        self.cmdnum=0
        
    def send(self,filename):
        try:
            file=open(self.write_command_loc+filename,'w')
        except OSError as e:
            if e.errno==22:
                pass
            else:
                raise e
        except Exception as e:
            raise e
        
    def encrypt(self,cmd,parameters=[]):
        filename=cmd+str(self.cmdnum)
        self.cmdnum+=1
        print(filename)
        for param in parameters:
            param=param.replace('/','+')
            param=param.replace('\\','+')
            param=param.replace(':','=')
            filename=filename+'&'+param
        return filename
    
class PiCommander(Commander):
    def __init__(self,write_command_loc):
        super().__init__(write_command_loc)
    
    def configure(self,i,e):
        filename=self.encrypt('configure',[i,e])
        self.send(filename)
        return filename

        
    def move_light(self, incidence):
        filename=self.encrypt('movelight',[incidence])
        self.send(filename)
        return filename

    def move_detector(self, emission):
        filename=self.encrypt('movedetector',[emission])
        self.send(filename)
        return filename
        
    def move_tray(self):
        filename=self.encrypt('movetray',[])
        self.send(filename)
        
    def get_current_geom(self):
        filename=self.encrypt('getcurrentgeom',[])
        self.send(filename)
    

class SpecCommander(Commander):
    def __init__(self,write_command_loc):
        super().__init__(write_command_loc)
    
    def take_spectrum(self, path, basename, num):
        filename=self.encrypt('spectrum',[path,basename,num])
        self.send(filename)
        return filename
        
    def white_reference(self):
        print('white referenc!')
        filename=self.encrypt('wr')
        print(self.cmdnum)
        self.send(filename)
        return filename
        
    def optimize(self):
        filename=self.encrypt('opt')
        self.send(filename)
        return filename
            
    def set_save_path(self, path, basename, startnum):
        filename=self.encrypt('saveconfig',[path,basename,startnum])
        self.send(filename)
        return filename
        
    def configure_instrument(self,number):
        filename=self.encrypt('instrumentconfig',[number])
        self.send(filename)
        return filename
        
    def listdir(self,parent):
        filename=self.encrypt('listdir',parameters=[parent])
        self.send(filename)
        return filename

    def list_contents(self,parent):
        filename=self.encrypt('listcontents',parameters=[parent])
        self.send(filename)
        return filename
        
    def check_writeable(self,dir):
        filename=self.encrypt('checkwriteable',[dir])
        self.send(filename)
        return filename
    
    def mkdir(self,newdir):
        filename=self.encrypt('mkdir',[newdir])
        self.send(filename)
        return filename
        
    def delete_spec(self,savedir, basename, num):
        filename=self.encrypt('rmfile',[savedir,basename,num])
        self.send(filename)
        return filename
        
    def get_data(self,filename):
        filename=self.encrypt('getdata',parameters=[filename])
        self.send(filename)
        return filename
        
    def process(self,input_dir, output_dir, output_file):
        filename=self.encrypt('process',[input_dir,output_dir,output_file])
        self.send(filename)
        
class ConnectionChecker():
    def __init__(self,dir,controller=None, func=None):
        self.dir=dir
        self.controller=controller
        self.func=func
        self.busy=False
    def alert_lost_connection(self, signum=None, frame=None):
        buttons={
            'retry':{
                self.release:[],
                self.check_connection:[False]
                },
            'work offline':{
                self.set_work_offline:[]
            },
            'exit':{
                exit_func:[]
            }
        }
        self.lost_dialog(buttons)


    def alert_not_connected(self, signum=None, frame=None):
        buttons={
            'retry':{
                self.release:[],
                self.check_connection:[True]
            },
            'work offline':{
                self.set_work_offline:[],
                self.func:[]
            },
            'exit':{
                exit_func:[]
            }
        }
        self.no_dialog(buttons)
        
    def set_work_offline(self):
        global OFFLINE
        OFFLINE=True
        
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
        if OFFLINE:
            print('offline hooray!')
            self.func()
            return True
        if self.busy:
            return

            
        self.busy=True
        connected=True
        if self.have_internet()==False:
            connected=False
        else: 
            connected=os.path.isdir(self.dir)
                
        if connected==False:
            #For some reason reconnecting only seems to work on the second attempt. This seems like a pretty poor way to handle that, but I just call check_connection twice if it fails the first time.
            if attempt>0 and firstconnection==True:
                self.alert_not_connected(None, None)
                return False
            elif attempt>0 and firstconnection==False:
                self.alert_lost_connection(None, None)
                return False
            else:
                time.sleep(0.5)
                self.release()
                self.check_connection(firstconnection, attempt=1)
        else:
            if self.func !=None:
                self.func()
            self.release()
            return True
    def release(self):
        self.busy=False

    def lost_dialog(self):
        pass
        
    def no_dialog(self):
        pass
        
class PretendEvent():
    def __init__(self, widget, width, height):
        self.widget=widget
        self.width=width
        self.height=height

class SpecConnectionChecker(ConnectionChecker):
    def __init__(self,dir,controller=None, func=None):
        print('new spec con checker!')
        super().__init__(dir,controller=controller, func=func)
            
    def lost_dialog(self,buttons):
        try:
            dialog=ErrorDialog(controller=self.controller, title='Lost Connection',label='Error: Lost connection with server.\n\nCheck you and the spectrometer computer are\nboth on the correct WiFi network and the\nSpecShare folder is mounted on your computer',buttons=buttons,button_width=15)
        except:
            pass
    def no_dialog(self,buttons):
        print('new dialog!')
        try:
            dialog=Dialog(controller=self.controller, title='Not Connected',label='Error: No connection with Spec Compy.\n\nCheck you and the spectrometer computer are\nboth on the correct WiFi network and the\nSpecShare folder is mounted on your computer',buttons=buttons,button_width=15)
        except:
            pass
class PiConnectionChecker(ConnectionChecker):
    def __init__(self,dir,controller=None, func=None):
        super().__init__(dir,controller=controller, func=func)
            
    def lost_dialog(self,buttons):
        try:
            dialog=ErrorDialog(controller=self.controller, title='Lost Connection',label='Error: Lost connection with Raspberry Pi.\n\nCheck you and the Raspberry Pi are\nboth on the correct WiFi network and the\nPiShare folder is mounted on your computer',buttons=buttons,button_width=15)
        except:
            pass
        
    def no_dialog(self,buttons):
        try:
            dialog=Dialog(controller=self.controller, title='Not Connected',label='Error: Raspberry Pi not connected.\n\nCheck you and the Raspberry Pi are\nboth on the correct WiFi network and the\nPiShare folder is mounted on your computer',buttons=buttons,button_width=15)
        except:
            pass
            
class PrivateEntry():
    def __init__(self, text):
        self.text=text
    def get(self):
        return self.text
        



if __name__=='__main__':
    main()