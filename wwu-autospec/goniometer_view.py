import pygame
import threading
from threading import Lock
import time
import numpy as np
from tkinter import *
import os

class View(threading.Thread):
    
    def __init__(self, master, test=False):
        threading.Thread.__init__(self)
        # self.master=master
        # self.top_frame = Frame(self.master, width=500, height=500)
        # self.top_frame.pack()
        # label=Label(self.top_frame, text='Test')
        # label.pack()
        # os.environ['SDL_WINDOWID'] = str(self.top_frame.winfo_id())
        self.lock=Lock()
        self.screen = pygame.display.set_mode((800, 500))
        self.screen.fill((255,255,255))
        self.light=pygame.Rect(30,30,60,60)
        self.theta_l=10
        self.theta_d=0
        self.test=test

    def close(self):
        try:
            pygame.quit()
        except:
            print('rats')
        
    def run(self):
        return
        pygame.init()
        largeText = pygame.font.Font('freesansbold.ttf',30)

        
        done = False
        while not done:
            for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                            done = True
            i_text=largeText.render(str(self.theta_l), True, (0, 128, 0))
            e_text=largeText.render(str(self.theta_d), True, (0, 128, 0))
            if not self.lock.locked():
            
                pivot = (400,400)
                light_len = 300
                scale=1.1
                back_radius=250
                x_l = pivot[0] + np.sin(np.radians(self.theta_l)) * light_len
                x_l_text=pivot[0] + np.sin(np.radians(self.theta_l)) * (light_len*scale)
                y_l = pivot[1] - np.cos(np.radians(self.theta_l)) * light_len
                y_l_text = pivot[1] - np.cos(np.radians(self.theta_l)) * light_len*scale
                
                detector_len=300
                x_d = pivot[0] + np.sin(np.radians(self.theta_d)) * detector_len
                x_d_text = pivot[0] + np.sin(np.radians(self.theta_d)) * detector_len*scale
                y_d = pivot[1] - np.cos(np.radians(self.theta_d)) * detector_len
                y_d_text = pivot[1] - np.cos(np.radians(self.theta_d)) * detector_len*scale
                
                self.screen.fill(pygame.Color("white"))
                pygame.draw.circle(self.screen, (0,0,0), pivot, back_radius)
                pygame.draw.rect(self.screen, (255,255,255),(400-back_radius,400,2*back_radius,2*back_radius))
                pygame.draw.rect(self.screen, (0,0,0),(400-back_radius,400,2*back_radius,50))
                
                pygame.draw.line(self.screen, (200, 200, 0), pivot, (x_l,y_l), 10)
                self.screen.blit(i_text,(x_l_text,y_l_text))
                pygame.draw.line(self.screen, (0, 100, 200), pivot, (x_d,y_d), 10)
                
                self.screen.blit(e_text,(x_d_text,y_d_text))
                #pygame.draw.circle(self.screen, 'black', pivot, back_radius=200)
                pygame.display.update()
                #self. master.update()
            
            
        #TextRect.center = ((self.screen.width/2),(self.screen.height/2))
        #self.screen.blit(TextSurf, TextRect)
        
        pygame.display.quit()
        pygame.quit()

            
    def move_light(self, theta):
        while np.abs(theta-self.theta_l)>0:
            self.theta_l=self.theta_l+np.sign(theta-self.theta_l)
            self.draw_circle()
            time.sleep(0.1)
            
    def move_detector(self, theta):
        while np.abs(theta-self.theta_d)>0:
            self.theta_d=self.theta_d+np.sign(theta-self.theta_d)
            self.draw_circle()
            time.sleep(0.1)


    def take_spectrum(self):
        print('taking spectrum')
        self.lock.acquire()
        self.screen.fill(pygame.Color('white'))
        pygame.display.update()
        time.sleep(0.1)
        self.lock.release()
        
    def clear_plots():
        pass
class TestView():
    def __init__(self,controller):
        self.width=1800
        self.height=1200
        self.controller=controller
        self.master=self.controller.master
        self.embed = Frame(self.master, width=self.width, height=self.height,bg=self.controller.bg)
        self.embed.pack(side=RIGHT,fill=BOTH,expand=True)

        self.double_embed=Frame(self.embed,width=self.width,height=self.height)
        self.double_embed.pack(fill=BOTH,expand=True)

        self.master.update()
        os.environ['SDL_WINDOWID'] = str(self.double_embed.winfo_id())
        if self.controller.opsys=='Windows':
            os.environ['SDL_VIDEODRIVER'] = 'windib'
        #pygame.display.init()
        self.screen = pygame.display.set_mode((self.width,self.height))#self.width,self.height))
        
        self.light=pygame.Rect(30,30,60,60)
        self.theta_l=10
        self.theta_d=60
        self.d_up=False
        self.l_up=False
        
        pygame.init()

    def flip(self):
        pygame.display.update()
        pygame.display.flip()
        
    def draw_circle(self,width,height):
        self.width=width
        self.height=height
        self.char_len=self.height
        if self.width-120<self.height:
            self.char_len=self.width-120
        try:
            i_str='i='+str(self.theta_l)
            e_str='e='+str(self.theta_d)
            largeText = pygame.font.Font('freesansbold.ttf',int(self.char_len/18))
            i_text=largeText.render(i_str, True, pygame.Color(self.controller.textcolor))
            e_text=largeText.render(e_str, True, pygame.Color(self.controller.textcolor))
        except:
            print('no pygame font')
        
        pivot = (int(self.width/2),int(0.8*self.height))
        light_len = int(5*self.char_len/8)#300
        light_width=24  #needs to be an even number
        scale=1.12
        back_radius=int(self.char_len/2)#250
        border_thickness=1
        
        x_l = pivot[0] + np.sin(np.radians(self.theta_l)) * light_len
        x_l_text=pivot[0] + np.sin(np.radians(self.theta_l)) * (light_len/scale)
        y_l = pivot[1] - np.cos(np.radians(self.theta_l)) * light_len
        y_l_text = pivot[1] - np.cos(np.radians(self.theta_l)) * light_len*scale-abs(np.sin(np.radians(self.theta_l))*light_len/12)
        
        detector_len=light_len
        detector_width=light_width
        x_d = pivot[0] + np.sin(np.radians(self.theta_d)) * detector_len
        x_d_text = pivot[0] + np.sin(np.radians(self.theta_d)) * (detector_len/scale)
        y_d = pivot[1] - np.cos(np.radians(self.theta_d)) * detector_len
        y_d_text = pivot[1] - np.cos(np.radians(self.theta_d)) * detector_len*scale-abs(np.sin(np.radians(self.theta_d))*detector_len/12)
        if np.abs(y_d_text-y_l_text)<self.char_len/30 and np.abs(x_d_text-x_l_text)<self.char_len/15:
            if self.d_up:
                y_d_text-=self.char_len/20
            elif self.l_up:
                y_l_text-=self.char_len/20
            elif y_d_text<y_l_text:
                print('emission above,lift it higher')
                y_d_text-=self.char_len/20
                self.d_up=True
            else:
                print('incidence above,lift it higher')
                self.l_up=True
                y_l_text-=self.char_len/20
        else:
            self.d_up=False
            self.l_up=False
        
        #deltas to give arm width.
        delta_y_l=light_width/2*np.sin(np.radians(self.theta_l))
        delta_x_l=light_width/2*np.cos(np.radians(self.theta_l))
        
        delta_y_d=detector_width/2*np.sin(np.radians(self.theta_d))
        delta_x_d=detector_width/2*np.cos(np.radians(self.theta_d))
        
        self.screen.fill(pygame.Color(self.controller.bg))
        
        #Draw goniometer
        pygame.draw.circle(self.screen, pygame.Color('darkgray'), pivot, back_radius+border_thickness)
        pygame.draw.circle(self.screen, (0,0,0), pivot, back_radius)
        pygame.draw.rect(self.screen, pygame.Color(self.controller.bg),(pivot[0]-back_radius,pivot[1]+int(self.char_len/10-5),2*back_radius,2*back_radius))
        pygame.draw.rect(self.screen, (0,0,0),(pivot[0]-back_radius,pivot[1],2*back_radius,int(self.char_len/6.5)))
        #draw border around bottom part of goniometer
        pygame.draw.line(self.screen,pygame.Color('darkgray'),(pivot[0]-back_radius-1,pivot[1]),(pivot[0]-back_radius-1,pivot[1]+int(self.char_len/6.5)))
        pygame.draw.line(self.screen,pygame.Color('darkgray'),(pivot[0]+back_radius,pivot[1]),(pivot[0]+back_radius,pivot[1]+int(self.char_len/6.5)))
        pygame.draw.line(self.screen,pygame.Color('darkgray'),(pivot[0]-back_radius,pivot[1]+int(self.char_len/6.5)),(pivot[0]+back_radius,pivot[1]+int(self.char_len/6.5)))

        
        #draw light arm
        points=((pivot[0]-delta_x_l,pivot[1]-delta_y_l),(x_l-delta_x_l,y_l-delta_y_l),(x_l+delta_x_l,y_l+delta_y_l),(pivot[0]+delta_x_l,pivot[1]+delta_y_l))
        pygame.draw.polygon(self.screen, pygame.Color('black'), points)
        pygame.draw.polygon(self.screen, pygame.Color('darkgray'), points, border_thickness)
        
        #draw detector arm
        points=((pivot[0]-delta_x_d,pivot[1]-delta_y_d),(x_d-delta_x_d,y_d-delta_y_d),(x_d+delta_x_d,y_d+delta_y_d),(pivot[0]+delta_x_d,pivot[1]+delta_y_d))
        pygame.draw.polygon(self.screen, pygame.Color('black'), points)
        pygame.draw.polygon(self.screen, pygame.Color('darkgray'), points, border_thickness)

        
        
        self.screen.blit(i_text,(x_l_text,y_l_text))
        self.screen.blit(e_text,(x_d_text,y_d_text))
        
        #border around screen
        pygame.draw.rect(self.screen,pygame.Color('darkgray'),(2,2,self.width-6,self.height+15),2)


        #pygame.display.update()
        #self. master.update()
        
        
        #pygame.display.flip()
        
        # self.screen.fill((255,255,255))

        #   for i in range(100):
        #     time.sleep(0.05)
        #     pygame.draw.circle(self.screen, (0,0,0), (200,200),i)
        #     pygame.display.flip()
        
    def move_light(self, theta):
        while np.abs(theta-self.theta_l)>0:
            self.theta_l=self.theta_l+np.sign(theta-self.theta_l)
            time.sleep(0.1)
            self.draw_circle(self.width,self.height)
            self.flip()
            
    def move_detector(self, theta):
        while np.abs(theta-self.theta_d)>0:
            self.theta_d=self.theta_d+np.sign(theta-self.theta_d)
            time.sleep(0.1)
            self.draw_circle(self.width,self.height)
            self.flip()
                
    def quit(self):
        pygame.display.quit()
        pygame.quit()
        
        

class TestViewOld():
    def __init__(self,root):
        self.width=800
        self.height=600
        self.embed = Frame(root, width=self.width, height=self.height)
        self.embed.pack(side=RIGHT)#row=0,column=2)
        self.root=root
        self.root.update()
        os.environ['SDL_WINDOWID'] = str(self.embed.winfo_id())
        #os.environ['SDL_VIDEODRIVER'] = 'windib'
        pygame.display.init()
        self.screen = pygame.display.set_mode((self.width,self.height))
        pygame.display.flip()
        
        
    def run(self):
        while True:
            #your code here
            #self.screen.fill((255,255,255))
            pygame.draw.circle(self.screen, (0,0,0), (100,100),100)
            #pygame.display.flip()
            self.root.update()
            
    def draw_circle(self):
        self.screen.fill((255,255,255))

        for i in range(100):
            time.sleep(0.05)
            pygame.draw.circle(self.screen, (0,0,0), (200,200),i)
            pygame.display.flip()