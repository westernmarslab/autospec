#The controller runs the main thread controlling the program.
#It creates and starts a View object, which extends Thread and will show a pygame window.

import imp
from tkinter import *
import threading
import auto_goniometer
imp.reload(auto_goniometer)

from auto_goniometer.robot_model import Model
imp.reload(auto_goniometer.robot_model)
from auto_goniometer.robot_view import View
from auto_goniometer.plotter import Plotter

import tkinter as tk
import pexpect
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

import matplotlib.backends.tkagg as tkagg
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import pygame

test=True


def main():
    plt.close('all')

    view=View()
    view.start()
    
    master=Tk()
    plotter=Plotter(master)

    model=Model(view, plotter)
    
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
        
    master_bg='white'
    
    master.configure(background = master_bg)
    master.title('Control')
    

    
    
    padx=3
    pady=3
    border_color='light gray'
    bg='white'
    button_width=28
    
    right_bg=bg

    right_frame=Frame(master,padx=padx,pady=pady,bd=2,highlightbackground=border_color,highlightcolor=border_color,highlightthickness=1,bg=right_bg)
    right_frame.pack(fill=BOTH)
    light_frame=Frame(right_frame,bg=right_bg)
    light_frame.pack(side=LEFT)
    light_label=Label(light_frame,padx=padx, pady=pady,bg=right_bg,text='Light Source')
    light_label.pack()
    
    light_labels_frame = Frame(light_frame,bg=right_bg,padx=padx,pady=pady)
    light_labels_frame.pack(side=LEFT)
    
    light_start_label=Label(light_labels_frame,padx=padx,pady=pady,bg=right_bg,text='Start:')
    light_start_label.pack(pady=(0,8))
    light_end_label=Label(light_labels_frame,bg=right_bg,padx=padx,pady=pady,text='End:')
    light_end_label.pack(pady=(0,5))

    light_increment_label=Label(light_labels_frame,bg=right_bg,padx=padx,pady=pady,text='Increment:')
    light_increment_label.pack(pady=(0,5))

    
    light_entries_frame=Frame(light_frame,bg=right_bg,padx=padx,pady=pady)
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

    
    detector_frame=Frame(right_frame,bg=right_bg)
    detector_frame.pack(side=RIGHT)
    
    detector_label=Label(detector_frame,padx=padx, pady=pady,bg=right_bg,text='Detector')
    detector_label.pack()
    
    detector_labels_frame = Frame(detector_frame,bg=right_bg,padx=padx,pady=pady)
    detector_labels_frame.pack(side=LEFT)
    
    detector_start_label=Label(detector_labels_frame,padx=padx,pady=pady,bg=right_bg,text='Start:')
    detector_start_label.pack(pady=(0,8))
    detector_end_label=Label(detector_labels_frame,bg=right_bg,padx=padx,pady=pady,text='End:')
    detector_end_label.pack(pady=(0,5))

    detector_increment_label=Label(detector_labels_frame,bg=right_bg,padx=padx,pady=pady,text='Increment:')
    detector_increment_label.pack(pady=(0,5))

    
    detector_entries_frame=Frame(detector_frame,bg=right_bg,padx=padx,pady=pady)
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
    
    gen_bg=bg
    
    gen_frame=Frame(master,padx=padx,pady=pady,bd=2,highlightbackground=border_color,highlightcolor=border_color,highlightthickness=1,bg=gen_bg)
    gen_frame.pack()
    
    go_button=Button(gen_frame, text='Go!', padx=padx, pady=pady, width=button_width,bg='light gray', command=go)
    go_button.pack(padx=padx,pady=pady)
    
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
