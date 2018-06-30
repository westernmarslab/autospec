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
        done = False
        while not done:
            for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                            done = True
            if not self.lock.locked():
            
                pivot = (400,400)
                light_len = 300
                x_l = pivot[0] + np.cos(np.radians(self.theta_l)) * light_len
                y_l = pivot[1] - np.sin(np.radians(self.theta_l)) * light_len
                
                detector_len=300
                x_d = pivot[0] + np.cos(np.radians(self.theta_d)) * detector_len
                y_d = pivot[1] - np.sin(np.radians(self.theta_d)) * detector_len
                
                self.screen.fill(pygame.Color("black"))
                pygame.draw.line(self.screen, (200, 200, 0), pivot, (x_l,y_l), 10)
                pygame.draw.line(self.screen, (0, 100, 200), pivot, (x_d,y_d), 10)
                pygame.display.update()
        
        pygame.display.quit()
        pygame.quit()

            
    def move_light(self, theta):
        while np.abs(theta-self.theta_l)>1:
            self.theta_l=self.theta_l+np.sign(theta-self.theta_l)

            if not self.test:
                time.sleep(0.07)
            
    def move_detector(self, theta):
        while np.abs(theta-self.theta_d)>1:
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
        