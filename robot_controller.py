#The controller runs the main thread controlling the program.
#It creates and starts a View object, which extends Thread and will show a pygame window.

dev=True
test=True
online=False

from tkinter import *
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


#From pyzo shell, looks in /home/khoza/Python for modules
#From terminal, it will look in current directory
if dev: sys.path.append('auto_goniometer')

import robot_model
import robot_view
import plotter

global PROCESS_COUNT
global SPECTRUM_COUNT
share_loc='/run/user/1000/gvfs/smb-share:server=melissa,share=kathleen'
config_loc='/home/khoza/Python/auto_goniometer/config'
#This is needed because otherwise changes won't show up until you restart the shell.
if dev:
    imp.reload(robot_model)
    from robot_model import Model
    imp.reload(robot_view)
    from robot_view import View
    imp.reload(plotter)
    from plotter import Plotter
    
# def go():          
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
#     model.go(incidence, emission)

def main():
    global spec_save_path
    spec_save_path=''
    global spec_basename
    spec_basename=''
    global spec_num
    spec_num=None
    
    def go():    
        if not auto.get():
            take_spectrum()
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
            model.go(incidence, emission)
        
            if spec_save_config.get():
                file=open('spec_save','w')
                file.write(spec_save_path_entry.get()+'\n')
                file.write(spec_basename_entry.get()+'\n')
                file.write(spec_startnum_entry.get()+'\n')

    def take_spectrum():
        global spec_save_path
        global spec_basename
        global spec_num
        
        try:
            incidence=int(light_start_entry.get())
            emission=int(detector_start_entry.get())
        except:
            print('Invalid input')
            return
        if incidence<0 or incidence>90 or emission<0 or emission>90:
            print('Invalid input')
            return

        if spec_save_path_entry.get() != spec_save_path or spec_basename_entry.get() != spec_basename or spec_num==None or spec_startnum_entry.get() !=str(int(spec_num)+1):
            print('setting path')
            spec_save_path=spec_save_path_entry.get()
            spec_basename = spec_basename_entry.get()
            spec_num=spec_startnum_entry.get()
            print(spec_num)
            model.set_save_path(spec_save_path, spec_basename, spec_num)
        else: spec_num=str(int(spec_num)+1)
        model.take_spectrum(incidence,emission)
        increment_num()
        if spec_save_config.get():
            print('save config')
            file=open(config_loc+'/spec_save','w')
            file.write(spec_save_path_entry.get()+'\n')
            file.write(spec_basename_entry.get()+'\n')
            file.write(spec_startnum_entry.get()+'\n')

            input_path_entry.delete(0,'end')
            input_path_entry.insert(0,spec_save_path_entry.get())
    def increment_num():
        try:
            num=int(spec_startnum_entry.get())+1
            spec_startnum_entry.delete(0,'end')
            spec_startnum_entry.insert(0,str(num))
        except:
            return
    
    def move():
        try:
            incidence=int(man_light_entry.get())
            emission=int(man_detector_entry.get())
        except:
            print('Invalid input')
            return
        if incidence<0 or incidence>90 or emission<0 or emission>90:
            print('Invalid input')
            return
        model.move_light(i)
        model.move_detector(e)
        
    def process_cmd():
        try:
            model.process(input_path_entry.get(), output_path_entry.get(), output_file_entry.get())
        except:
            pass
        if process_save_dir.get():
            file=open(config_loc+'/process_directories','w')
            file.write(input_path_entry.get()+'\n')
            file.write(output_path_entry.get()+'\n')
            file.write(output_file_entry.get()+'\n')
            
    def plot():
        filename=plot_input_path_entry.get()
        filename=filename.replace('C:\\Kathleen','/run/user/1000/gvfs/smb-share:server=melissa,share=kathleen/')
        filename=filename.replace('\\','/')
        title=plot_title_entry.get()
        caption=plot_caption_entry.get()
        plotter.plot_spectra(title,filename,caption)
    
    
    def auto_cycle_check():
        if auto.get():
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
        
    if dev: plt.close('all')

    view=View()
    view.start()
    
    master=Tk()
    notebook=ttk.Notebook(master)
    plotter=Plotter(master)

    model=Model(view, plotter, False, False)
    

        
    master_bg='white'
    master.configure(background = master_bg)
    master.title('Control')
   
    padx=3
    pady=3
    border_color='light gray'
    bg='white'
    button_width=15
    
    process_config=open(config_loc+'/process_directories','r')
    input_path=''
    output_path=''
    try:
        input_path=process_config.readline().strip('\n')
        output_path=process_config.readline().strip('\n')
    except:
        print('invalid config')
    print('found process config??')
    print(input_path)
    print(output_path)

    spec_save_config=open(config_loc+'/spec_save','r')
    spec_save_path=''
    spec_basename=''
    spec_startnum=''
    
    try:
        spec_save_path=spec_save_config.readline().strip('\n')
        spec_basename=spec_save_config.readline().strip('\n')
        spec_startnum=spec_save_config.readline().strip('\n')
    except:
        print('invalid config')
    
    auto_frame=Frame(notebook, bg=bg)

    spec_save_path_label=Label(auto_frame,padx=padx,pady=pady,bg=bg,text='Save directory:')
    spec_save_path_label.pack(padx=padx,pady=pady)
    spec_save_path_entry=Entry(auto_frame, width=50,bd=3)
    spec_save_path_entry.insert(0, spec_save_path)
    spec_save_path_entry.pack(padx=padx, pady=pady)

    spec_save_frame=Frame(auto_frame, bg=bg)
    spec_save_frame.pack()
    
    spec_basename_label=Label(spec_save_frame,pady=pady,bg=bg,text='Base name:')
    spec_basename_label.pack(side=LEFT,pady=(5,15),padx=(0,0))
    spec_basename_entry=Entry(spec_save_frame, width=10,bd=3)
    spec_basename_entry.pack(side=LEFT,padx=(5,5), pady=pady)
    spec_basename_entry.insert(0,spec_basename)
    
    spec_startnum_label=Label(spec_save_frame,padx=padx,pady=pady,bg=bg,text='Number:')
    spec_startnum_label.pack(side=LEFT,pady=pady)
    spec_startnum_entry=Entry(spec_save_frame, width=10,bd=3)
    spec_startnum_entry.insert(0,spec_startnum)
    spec_startnum_entry.pack(side=RIGHT, pady=pady)
    
    spec_save_config=IntVar()
    spec_save_config_check=Checkbutton(auto_frame, text='Save file configuration', bg=bg, pady=pady,highlightthickness=0, variable=spec_save_config)
    spec_save_config_check.pack(pady=(5,15))
    spec_save_config_check.select()
    
    auto_check_frame=Frame(auto_frame, bg=bg)
    auto_check_frame.pack(pady=(15,5))
    auto=IntVar()
    auto_check=Checkbutton(auto_check_frame, text='Automatically iterate through viewing geometries', bg=bg, pady=pady,highlightthickness=0, variable=auto, command=auto_cycle_check)
    auto_check.pack(side=LEFT, pady=(5,15))
    
    top_frame=Frame(auto_frame,padx=padx,pady=pady,bd=2,highlightbackground=border_color,highlightcolor=border_color,highlightthickness=0,bg=bg)
    top_frame.pack(fill=BOTH)
    light_frame=Frame(top_frame,bg=bg)
    light_frame.pack(side=LEFT)
    light_label=Label(light_frame,padx=padx, pady=pady,bg=bg,text='Light Source')
    light_label.pack()
    
    light_labels_frame = Frame(light_frame,bg=bg,padx=padx,pady=pady)
    light_labels_frame.pack(side=LEFT)
    
    light_start_label=Label(light_labels_frame,padx=padx,pady=pady,bg=bg,text='Start:')
    light_start_label.pack(pady=(0,8))
    light_end_label=Label(light_labels_frame,bg=bg,padx=padx,pady=pady,text='End:',fg='lightgray')
    light_end_label.pack(pady=(0,5))

    light_increment_label=Label(light_labels_frame,bg=bg,padx=padx,pady=pady,text='Increment:',fg='lightgray')
    light_increment_label.pack(pady=(0,5))

    
    light_entries_frame=Frame(light_frame,bg=bg,padx=padx,pady=pady)
    light_entries_frame.pack(side=RIGHT)
    

    
    light_start_entry=Entry(light_entries_frame,bd=3,width=10)
    light_start_entry.pack(padx=padx,pady=pady)
    light_start_entry.insert(0,'10')
    
    light_end_entry=Entry(light_entries_frame,bd=1,width=10, highlightbackground='white')
    light_end_entry.pack(padx=padx,pady=pady)    
    light_increment_entry=Entry(light_entries_frame,bd=1,width=10,highlightbackground='white')
    light_increment_entry.pack(padx=padx,pady=pady)
    
    detector_frame=Frame(top_frame,bg=bg)
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
    
    auto_check_frame=Frame(auto_frame, bg=bg)
    auto_check_frame.pack()
    auto_process=IntVar()
    auto_process_check=Checkbutton(auto_check_frame, text='Process data', bg=bg, highlightthickness=0)
    auto_process_check.pack(side=LEFT)
    
    auto_plot=IntVar()
    auto_plot_check=Checkbutton(auto_check_frame, text='Plot spectra', bg=bg, highlightthickness=0)
    auto_plot_check.pack(side=LEFT)
    
    gen_bg=bg
    
    gen_frame=Frame(auto_frame,padx=padx,pady=pady,bd=2,highlightbackground=border_color,highlightcolor=border_color,highlightthickness=0,bg=gen_bg)
    gen_frame.pack(side=BOTTOM)
    
    go_button=Button(gen_frame, text='Go!', padx=padx, pady=pady, width=button_width,bg='light gray', command=go)
    go_button.pack(padx=padx,pady=pady, side=LEFT)
    pause_button=Button(gen_frame, text='Pause', padx=padx, pady=pady, width=button_width, bg='light gray', command=plot)
    pause_button.pack(padx=padx,pady=pady, side=LEFT)
    cancel_button=Button(gen_frame, text='Cancel', padx=padx, pady=pady,width=button_width, bg='light gray', command=go)
    cancel_button.pack(padx=padx,pady=pady, side=LEFT)
    
    
    #***************************************************************
    # Frame for manual control
    
    man_frame=Frame(notebook, bg=bg, pady=2*pady)
    man_frame.pack()
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
    
    timer_frame=Frame(man_frame, bg=bg)
    timer_frame.pack()
    timer_check_frame=Frame(timer_frame, bg=bg)
    timer_check_frame.pack(pady=(15,5))
    timer=IntVar()
    timer_check=Checkbutton(timer_check_frame, text='Use a timer to take spectra at set intervals at each geometry', bg=bg, pady=pady,highlightthickness=0, variable=timer)
    timer_check.pack(side=LEFT, pady=(5,15))
    timer_spectra_label=Label(timer_frame,padx=padx,pady=pady,bg=bg,text='Total duration (min):')
    timer_spectra_label.pack(side=LEFT, padx=padx,pady=(0,8))
    timer_spectra_entry=Entry(timer_frame, width=10)
    timer_spectra_entry.pack(side=LEFT)
    timer_interval_label=Label(timer_frame, padx=padx,pady=pady,bg=bg, text='Interval (min):')
    timer_interval_label.pack(side=LEFT, padx=(10,0))
    timer_interval_entry=Entry(timer_frame, width=10,text='0')
   # timer_interval_entry.insert(0,'-1')
    timer_interval_entry.pack(side=LEFT, padx=(0,20))
    
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
    



    process_frame=Frame(notebook, bg=bg, pady=2*pady)
    process_frame.pack()
    input_frame=Frame(process_frame, bg=bg)
    input_frame.pack()
    input_path_label=Label(process_frame,padx=padx,pady=pady,bg=bg,text='Input directory:')
    input_path_label.pack(padx=padx,pady=pady)
    input_path_entry=Entry(process_frame, width=50)
    input_path_entry.insert(0, input_path)
    input_path_entry.pack()
    
    output_frame=Frame(process_frame, bg=bg)
    output_frame.pack()
    output_path_label=Label(process_frame,padx=padx,pady=pady,bg=bg,text='Output directory:')
    output_path_label.pack(padx=padx,pady=pady)
    output_path_entry=Entry(process_frame, width=50)
    output_path_entry.insert(0, output_path)
    output_path_entry.pack()
    
    output_file_frame=Frame(process_frame, bg=bg)
    output_file_frame.pack()
    output_file_label=Label(process_frame,padx=padx,pady=pady,bg=bg,text='Output file name:')
    output_file_label.pack(padx=padx,pady=pady)
    output_file_entry=Entry(process_frame, width=50)
    output_file_entry.insert(0, output_path)
    output_file_entry.pack()
    
    
    process_check_frame=Frame(process_frame, bg=bg)
    process_check_frame.pack(pady=(15,5))
    process_save_dir=IntVar()
    process_save_dir_check=Checkbutton(process_check_frame, text='Save file configuration', bg=bg, pady=pady,highlightthickness=0, variable=process_save_dir)
    process_save_dir_check.pack(side=LEFT, pady=(5,15))
    process_save_dir_check.select()
    process_plot=IntVar()
    process_plot_check=Checkbutton(process_check_frame, text='Plot spectra', bg=bg, pady=pady,highlightthickness=0)
    process_plot_check.pack(side=LEFT, pady=(5,15))
    
    process_button=Button(process_frame, text='Process', padx=padx, pady=pady, width=int(button_width*1.6),bg='light gray', command=process_cmd)
    process_button.pack()
    
    #********************** Plot frame ******************************
    
    plot_frame=Frame(notebook, bg=bg, pady=2*pady)
    process_frame.pack()
    plot_input_frame=Frame(plot_frame, bg=bg)
    plot_input_frame.pack()
    plot_input_path_label=Label(plot_frame,padx=padx,pady=pady,bg=bg,text='Path to .tsv file:')
    plot_input_path_label.pack(padx=padx,pady=pady)
    plot_input_path_entry=Entry(plot_frame, width=50)
    plot_input_path_entry.insert(0, input_path)
    plot_input_path_entry.pack()
    
    plot_title_frame=Frame(plot_frame, bg=bg)
    plot_title_frame.pack()
    plot_title_label=Label(plot_frame,padx=padx,pady=pady,bg=bg,text='Plot title:')
    plot_title_label.pack(padx=padx,pady=pady)
    plot_title_entry=Entry(plot_frame, width=50)
    plot_title_entry.insert(0, output_path)
    plot_title_entry.pack()
    
    plot_caption_frame=Frame(plot_frame, bg=bg)
    plot_caption_frame.pack()
    plot_caption_label=Label(plot_frame,padx=padx,pady=pady,bg=bg,text='Plot caption:')
    plot_caption_label.pack(padx=padx,pady=pady)
    plot_caption_entry=Entry(plot_frame, width=50)
    plot_caption_entry.insert(0, output_path)
    plot_caption_entry.pack()
    
    
    # pr_check_frame=Frame(process_frame, bg=bg)
    # process_check_frame.pack(pady=(15,5))
    # process_save_dir=IntVar()
    # process_save_dir_check=Checkbutton(process_check_frame, text='Save file configuration', bg=bg, pady=pady,highlightthickness=0, variable=process_save_dir)
    # process_save_dir_check.pack(side=LEFT, pady=(5,15))
    # process_save_dir_check.select()
    # process_plot=IntVar()
    # process_plot_check=Checkbutton(process_check_frame, text='Plot spectra', bg=bg, pady=pady,highlightthickness=0)
    # process_plot_check.pack(side=LEFT, pady=(5,15))
    
    plot_button=Button(plot_frame, text='Plot', padx=padx, pady=pady, width=int(button_width*1.6),bg='light gray', command=plot)
    plot_button.pack()


    notebook.add(auto_frame, text='Spectrometer control')
    notebook.add(man_frame, text='Timer control')
    notebook.add(process_frame, text='Data processing')
    notebook.add(plot_frame, text='Plot')
    #notebook.add(val_frame, text='Validation tools')
    #checkbox: Iterate through a range of geometries
    #checkbox: Choose a single geometry
    #checkbox: Take one spectrum
    #checkbox: Use a timer to collect a series of spectra
    #Timer interval: 
    #Number of spectra to collect:
    notebook.pack()
    master.mainloop()
    


    print('time to move light!')
    view.join()
    print('****************************************************************************')



def draw_figure(canvas, figure, loc=(0, 0)):
    """ Draw a matplotlib figure onto a Tk canvas

    loc: location of top-left corner of figure on canvas in pixels.
    Inspired by matplotlib source: lib/matplotlib/backends/backend_tkagg.py
    """
    figure_canvas_agg = FigureCanvasAgg(figure)
    figure_canvas_agg.draw()
    figure_x, figure_y, figure_w, figure_h = figure.bbox.bounds
    figure_w, figure_h = int(figure_w), int(figure_h)
    photo = tk.PhotoImage(master=canvas, width=figure_w, height=figure_h)

    # Position: convert from top-left anchor to center anchor
    canvas.create_image(loc[0] + figure_w/2, loc[1] + figure_h/2, image=photo)

    # Unfortunately, there's no accessor for the pointer to the native renderer
    tkagg.blit(photo, figure_canvas_agg.get_renderer()._renderer, colormode=2)

    # Return a handle which contains a reference to the photo object
    # which must be kept live or else the picture disappears
    
    return photo
    
def create_window(root):
    t = tk.Toplevel(root)
    t.wm_title('hooray!')
    
    x=np.array ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    v= np.array ([16,16.31925,17.6394,16.003,17.2861,17.3131,19.1259,18.9694,22.0003,22.81226])
    p= np.array ([16.23697,     17.31653,     17.22094,     17.68631,     17.73641 ,    18.6368,
        19.32125,     19.31756 ,    21.20247  ,   22.41444   ,  22.11718  ,   22.12453])

    fig = mpl.figure.Figure(figsize=(6,6))
    a = fig.add_subplot(111)
    a.scatter(v,x,color='red')
    a.plot(p, range(2 +max(x)),color='blue')
    a.invert_yaxis()

    a.set_title ("Estimation Grid", fontsize=16)
    a.set_ylabel("Y", fontsize=14)
    a.set_xlabel("X", fontsize=14)

    canvas = FigureCanvasTkAgg(fig, master=t)
    canvas.get_tk_widget().pack()
    canvas.draw()



    



        
if __name__=="__main__":
    main()
