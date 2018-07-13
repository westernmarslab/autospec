import pygame
import threading
from threading import Lock
import time
import numpy as np

class View(threading.Thread):
    
    def __init__(self, test=False):
        threading.Thread.__init__(self)
        self.lock=Lock()
        self.screen = pygame.display.set_mode((800, 500))
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
            
            
        #TextRect.center = ((self.screen.width/2),(self.screen.height/2))
        #self.screen.blit(TextSurf, TextRect)
        
        pygame.display.quit()
        pygame.quit()

            
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


    def take_spectrum(self):
        print('taking spectrum')
        self.lock.acquire()
        self.screen.fill(pygame.Color('white'))
        pygame.display.update()
        time.sleep(0.1)
        self.lock.release()
        
    def clear_plots():
        pass
        