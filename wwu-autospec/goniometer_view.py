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
        self.width=1000
        self.height=650
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
        self.theta_d=0
        
        pygame.init()
        #self.draw_circle()
        # largeText = pygame.font.Font('freesansbold.ttf',30)
        # i_text=largeText.render(str(self.theta_l), True, (0, 128, 0))
        # e_text=largeText.render(str(self.theta_d), True, (0, 128, 0))
        # 
        # pivot = (400,400)
        # light_len = 300
        # scale=1.1
        # back_radius=250
        # x_l = pivot[0] + np.sin(np.radians(self.theta_l)) * light_len
        # x_l_text=pivot[0] + np.sin(np.radians(self.theta_l)) * (light_len*scale)
        # y_l = pivot[1] - np.cos(np.radians(self.theta_l)) * light_len
        # y_l_text = pivot[1] - np.cos(np.radians(self.theta_l)) * light_len*scale
        # 
        # detector_len=300
        # x_d = pivot[0] + np.sin(np.radians(self.theta_d)) * detector_len
        # x_d_text = pivot[0] + np.sin(np.radians(self.theta_d)) * detector_len*scale
        # y_d = pivot[1] - np.cos(np.radians(self.theta_d)) * detector_len
        # y_d_text = pivot[1] - np.cos(np.radians(self.theta_d)) * detector_len*scale
        # 
        # self.screen.fill(pygame.Color("white"))
        # pygame.draw.circle(self.screen, (0,0,0), pivot, back_radius)
        # pygame.draw.rect(self.screen, (255,255,255),(400-back_radius,400,2*back_radius,2*back_radius))
        # pygame.draw.rect(self.screen, (0,0,0),(400-back_radius,400,2*back_radius,50))
        # 
        # pygame.draw.line(self.screen, (200, 200, 0), pivot, (x_l,y_l), 10)
        # self.screen.blit(i_text,(x_l_text,y_l_text))
        # pygame.draw.line(self.screen, (0, 100, 200), pivot, (x_d,y_d), 10)
        # 
        # self.screen.blit(e_text,(x_d_text,y_d_text))
        # #pygame.draw.circle(self.screen, 'black', pivot, back_radius=200)
        # pygame.display.update()
        # #self. master.update()
    def flip(self):
        pygame.display.update()
        pygame.display.flip()
        
    def draw_circle(self,width,height):
        # self.width=width
        # self.height=height
        #self.double_embed.configure(width=width, height=height)
        #self.screen = pygame.display.set_mode((self.width,self.height), pygame.RESIZABLE)#self.width,self.height))
        #self.screen=pygame.display.set_mode((self.width,self.height))
        try:
            largeText = pygame.font.Font('freesansbold.ttf',int(self.width/20))
            i_text=largeText.render(str(self.theta_l), True, pygame.Color(self.controller.textcolor))
            e_text=largeText.render(str(self.theta_d), True, pygame.Color(self.controller.textcolor))
        except:
            print('no pygame font')
        
        pivot = (int(self.width/2),int(3*self.height/4))
        light_len = int(5*self.width/16)#300
        light_width=24  #needs to be an even number
        scale=1.15
        back_radius=int(self.width/4)#250
        border_thickness=1
        
        x_l = pivot[0] + np.sin(np.radians(self.theta_l)) * light_len
        x_l_text=pivot[0] + np.sin(np.radians(self.theta_l)) * (light_len*scale)
        y_l = pivot[1] - np.cos(np.radians(self.theta_l)) * light_len
        y_l_text = pivot[1] - np.cos(np.radians(self.theta_l)) * light_len*scale
        
        detector_len=int(5*self.width/16)
        x_d = pivot[0] + np.sin(np.radians(self.theta_d)) * detector_len
        x_d_text = pivot[0] + np.sin(np.radians(self.theta_d)) * detector_len*scale
        y_d = pivot[1] - np.cos(np.radians(self.theta_d)) * detector_len
        y_d_text = pivot[1] - np.cos(np.radians(self.theta_d)) * detector_len*scale
        
        self.screen.fill(pygame.Color(self.controller.bg))
        
        pygame.draw.circle(self.screen, pygame.Color('darkgray'), pivot, back_radius+border_thickness)
        pygame.draw.circle(self.screen, (0,0,0), pivot, back_radius)
        pygame.draw.rect(self.screen, pygame.Color(self.controller.bg),(pivot[0]-back_radius,pivot[1]+int(self.width/10-5),2*back_radius,2*back_radius))
        pygame.draw.rect(self.screen, (0,0,0),(pivot[0]-back_radius,pivot[1],2*back_radius,int(self.width/10)))
        
        pygame.draw.line(self.screen, pygame.Color('black'), pivot, (x_l,y_l), light_width)
        pygame.draw.line(self.screen,pygame.Color('darkgray'),(pivot[0]-light_width/2,pivot[1]),(x_l-light_width/2,y_l),border_thickness)
        pygame.draw.line(self.screen,pygame.Color('darkgray'),(pivot[0]+light_width/2,pivot[1]),(x_l+light_width/2,y_l),border_thickness)
        pygame.draw.line(self.screen,pygame.Color('darkgray'),(x_l+light_width/2,y_l),(x_l-light_width/2,y_l),border_thickness)
        pygame.draw.line(self.screen,pygame.Color('darkgray'),(pivot[0]+light_width/2,pivot[1]),(pivot[0]-light_width/2,pivot[1]),border_thickness)
        
        pygame.draw.line(self.screen, pygame.Color('black'), pivot, (x_d,y_d), light_width)
        pygame.draw.line(self.screen,pygame.Color('darkgray'),(pivot[0]-light_width/2,pivot[1]),(x_d-light_width/2,y_d),border_thickness)
        pygame.draw.line(self.screen,pygame.Color('darkgray'),(pivot[0]+light_width/2,pivot[1]),(x_d+light_width/2,y_d),border_thickness)
        pygame.draw.line(self.screen,pygame.Color('darkgray'),(x_d+light_width/2,y_d),(x_d-light_width/2,y_d),border_thickness)
        pygame.draw.line(self.screen,pygame.Color('darkgray'),(pivot[0]+light_width/2,pivot[1]),(pivot[0]-light_width/2,pivot[1]),border_thickness)
        
        self.screen.blit(i_text,(x_l_text,y_l_text))
        self.screen.blit(e_text,(x_d_text,y_d_text))
        #pygame.draw.circle(self.screen, 'black', pivot, back_radius=200)
        
        pygame.draw.rect(self.screen,pygame.Color('darkgray'),(2,2,self.width-4,self.height-3),2)

        pygame.display.update()
        #self. master.update()
        
        
        pygame.display.flip()
        # self.screen.fill((255,255,255))

        #   for i in range(100):
        #     time.sleep(0.05)
        #     pygame.draw.circle(self.screen, (0,0,0), (200,200),i)
        #     pygame.display.flip()
        
    def move_light(self, theta):
        while np.abs(theta-self.theta_l)>0:
            self.theta_l=self.theta_l+np.sign(theta-self.theta_l)

            if not self.test:
                time.sleep(0.07)
            
    def move_detector(self, theta):
        while np.abs(theta-self.theta_d)>0:
            self.theta_d=self.theta_d+np.sign(theta-self.theta_d)
            if not self.test:
                time.sleep(0.07)
                
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