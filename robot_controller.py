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

#This is needed because otherwise changes won't show up until you restart the shell.
if dev:
    imp.reload(robot_model)
    from robot_model import Model
    imp.reload(robot_view)
    from robot_view import View
    imp.reload(plotter)
    from plotter import Plotter
    
def go():          
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
    model.go(incidence, emission)

def main():
    def go():          
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
    
    def take_spectrum():
        try:
            incidence=int(man_light_entry.get())
            emission=int(man_detector_entry.get())
        except:
            print('Invalid input')
            return
        if incidence<0 or incidence>90 or emission<0 or emission>90:
            print('Invalid input')
            return
        model.take_spectrum(incidence,emission)
    
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
    
    auto_frame=Frame(notebook, bg=bg)
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
    light_end_label=Label(light_labels_frame,bg=bg,padx=padx,pady=pady,text='End:')
    light_end_label.pack(pady=(0,5))

    light_increment_label=Label(light_labels_frame,bg=bg,padx=padx,pady=pady,text='Increment:')
    light_increment_label.pack(pady=(0,5))

    
    light_entries_frame=Frame(light_frame,bg=bg,padx=padx,pady=pady)
    light_entries_frame.pack(side=RIGHT)
    

    
    light_start_entry=Entry(light_entries_frame,bd=3,width=10)
    light_start_entry.pack(padx=padx,pady=pady)
    light_start_entry.insert(0,'10')
    
    light_end_entry=Entry(light_entries_frame,bd=3,width=10)
    light_end_entry.pack(padx=padx,pady=pady)
    light_end_entry.insert(0,'10')
    
    light_increment_entry=Entry(light_entries_frame,bd=3,width=10)
    light_increment_entry.pack(padx=padx,pady=pady)
    light_increment_entry.insert(0,'10')

    
    detector_frame=Frame(top_frame,bg=bg)
    detector_frame.pack(side=RIGHT)
    
    detector_label=Label(detector_frame,padx=padx, pady=pady,bg=bg,text='Detector')
    detector_label.pack()
    
    detector_labels_frame = Frame(detector_frame,bg=bg,padx=padx,pady=pady)
    detector_labels_frame.pack(side=LEFT)
    
    detector_start_label=Label(detector_labels_frame,padx=padx,pady=pady,bg=bg,text='Start:')
    detector_start_label.pack(pady=(0,8))
    detector_end_label=Label(detector_labels_frame,bg=bg,padx=padx,pady=pady,text='End:')
    detector_end_label.pack(pady=(0,5))

    detector_increment_label=Label(detector_labels_frame,bg=bg,padx=padx,pady=pady,text='Increment:')
    detector_increment_label.pack(pady=(0,5))

    
    detector_entries_frame=Frame(detector_frame,bg=bg,padx=padx,pady=pady)
    detector_entries_frame.pack(side=RIGHT)
    detector_start_entry=Entry(detector_entries_frame,bd=3,width=10)
    detector_start_entry.pack(padx=padx,pady=pady)
    detector_start_entry.insert(0,'0')
    
    detector_end_entry=Entry(detector_entries_frame,bd=3,width=10)
    detector_end_entry.pack(padx=padx,pady=pady)
    detector_end_entry.insert(0,'0')
    
    detector_increment_entry=Entry(detector_entries_frame,bd=3,width=10)
    detector_increment_entry.pack(padx=padx,pady=pady)
    detector_increment_entry.insert(0,'10')
    
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
    pause_button=Button(gen_frame, text='Pause', padx=padx, pady=pady, width=button_width, bg='light gray', command=go)
    pause_button.pack(padx=padx,pady=pady, side=LEFT)
    cancel_button=Button(gen_frame, text='Cancel', padx=padx, pady=pady,width=button_width, bg='light gray', command=go)
    cancel_button.pack(padx=padx,pady=pady, side=LEFT)
    
    
    #***************************************************************
    # Frame for manual control
    
    man_frame=Frame(notebook, bg=bg, pady=2*pady)
    man_frame.pack()
    entries_frame=Frame(man_frame, bg=bg)
    entries_frame.pack(fill=BOTH, expand=True)
    man_light_label=Label(entries_frame,padx=padx, pady=pady,bg=bg,text='Instrument positions:')
    man_light_label.pack()
    man_light_label=Label(entries_frame,padx=padx,pady=pady,bg=bg,text='Incidence:')
    man_light_label.pack(side=LEFT, padx=(30,5),pady=(0,8))
    man_light_entry=Entry(entries_frame, width=10)
    man_light_entry.insert(0,'10')
    man_light_entry.pack(side=LEFT)
    man_detector_label=Label(entries_frame, padx=padx,pady=pady,bg=bg, text='Emission:')
    man_detector_label.pack(side=LEFT, padx=(10,0))
    man_detector_entry=Entry(entries_frame, width=10,text='0')
    man_detector_entry.insert(0,'10')
    man_detector_entry.pack(side=LEFT)
    
    check_frame=Frame(man_frame, bg=bg)
    check_frame.pack()
    process=IntVar()
    process_check=Checkbutton(check_frame, text='Process data', bg=bg, pady=pady,highlightthickness=0)
    process_check.pack(side=LEFT, pady=(5,15))
    
    plot=IntVar()
    plot_check=Checkbutton(check_frame, text='Plot spectrum', bg=bg, pady=pady,highlightthickness=0)
    plot_check.pack(side=LEFT, pady=(5,15))

    move_button=Button(man_frame, text='Move', padx=padx, pady=pady, width=int(button_width*1.6),bg='light gray', command=go)
    move_button.pack(padx=padx,pady=pady, side=LEFT)
    spectrum_button=Button(man_frame, text='Take a spectrum', padx=padx, pady=pady, width=int(button_width*1.6), bg='light gray', command=take_spectrum)
    spectrum_button.pack(padx=padx,pady=pady, side=LEFT)
    


    notebook.add(auto_frame, text='Automatic control')
    notebook.add(man_frame, text='Manual control')
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
