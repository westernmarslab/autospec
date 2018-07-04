import os
import sys

from threading import Lock
import time
import subprocess
import pexpect
import imp
import numpy as np

import auto_goniometer
imp.reload(auto_goniometer)

from auto_goniometer.sample import Sample
from auto_goniometer.sample_holder import Sample_holder
from auto_goniometer.detector import Detector
from auto_goniometer.motor import Motor

class Model:

    def __init__(self, view, plotter, spec_compy_connected=True, raspberry_pi_connected=True):
        self.spec_compy_connected=spec_compy_connected
        self.raspberry_pi_connected=raspberry_pi_connected
        self.view=view
        self.plotter=plotter
        self.wr=Sample('wr')
        self.s1=Sample('Mars!')
        self.sh=Sample_holder(3)
        self.sh.fill_tray(self.wr,0)
        self.sh.fill_tray(self.s1,1)
        x=Motor('foo')
        self.m_i=Motor('incidence')
        self.m_e=Motor('emission')
        self.m_a=Motor('azimuth')
        
        self.detector=Detector()
        self.i_e_tuples=[]
        if spec_compy_connected:
            self.rs3_process=pexpect.spawnu('ssh MELISSA+RS3Admin@MELISSA.univ.dir.wwu.edu')
            fout = open('mylog.txt','w')
            fin=open('mylog2.txt','w')
            self.rs3_process.logfile_send = fout
            self.rs3_process.logfile_read = fin
            self.rs3_process.expect('password:')
            self.rs3_process.sendline('fieldspecadmin')
            self.rs3_process.expect('$')
            self.rs3_process.sendline('touch c:/Kathleen/test')
        else:
            self.rs3_process=None
        if self.raspberry_pi_connected:
            self.pi_process=pexpect.spawnu('python3')
            self.pi_process.expect('>>>')
        else:
            self.pi_process=None
        
    def plot(self):
        self.plotter.plot_spectrum(10,10,[[1,2,3,4,5],[1,2,3,4,5]])

    def go(self, incidence, emission):
        self.i_e_tuples=[]
        pi_process=None
        
        

        
        for i in range(incidence['start'],incidence['end']+1):
            if (i-incidence['start'])%(incidence['increment']) != 0 and i != incidence['end'] and i != incidence['start']:
                continue
            self.move_light(i, self.pi_process)
            
            for e in range(emission['start'],emission['end']+1):
                if (e-emission['start'])%(emission['increment']) != 0 and e != emission['end'] and e != emission['start']:
                    continue
                print('taking spectrum at '+str(e))
                self.move_detector(e, self.pi_process)
                self.take_spectrum(i,e, self.rs3_process)
                data = np.genfromtxt('test_data/test_'+str(i)+'_'+str(e)+'.csv', dtype=float,delimiter=',')

                self.plotter.plot_spectrum(i,e,data)
            
        if self.spec_compy_connected:
            self.rs3_process.terminate(force=True)
        if self.raspberry_pi_connected:
            pi_process.terminate(force=True)



    def move_detector(self, e, process):
        command='print('+str(e)+')'#,'print("foo")']
        print('Detector to ', str(e), ' degrees...')
        # process.sendline(command)
        # process.expect('>>> ')
        self.view.move_detector(e)
        # process.sendline('time.sleep(0.3)')
        # process.expect('>>> ')
        # process.sendline('print("moved detector")')
        # process.expect('>>> ')
        #print(process.before)
        self.m_e.position=e
        
    def move_light(self, i, process):
        # command='ssh pi@192.168.2.3'
        # print('Light source to ', str(i), ' degrees...')
        # process.sendline(command)
        # process.expect('>>> ')
        self.view.move_light(i)
        # process.sendline('time.sleep(0.3)')
        # process.expect('>>> ')
        # process.sendline('print("moved light")')
        # process.expect('>>> ')
        # print(process.before)
        # self.m_i.position=i
    
        
    def take_spectrum(self, i, e, process):
        open('spectrometer_network/newfile','w')
        if self.spec_compy_connected: 
            cmd='touch c:/Kathleen/test'+str(np.random.rand())
            process.sendline(cmd)
            process.expect('$')
            print('got it')
            print(process.after)

            #process.sendline('c:/users/rs3admin/anaconda3/python.exe c:/users/rs3admin/hozak/Python/spectrum_taker.py -sp')

        self.view.take_spectrum()
        self.detector.take_spectrum()
        self.i_e_tuples.append((i,e))
        print(self.i_e_tuples)
        
        name='test_'+str(i)+'_'+str(e)+'.csv'
        file=open('test_data/'+name,'w')
        for j in range(10):
            file.write(str(0.5+0.1*j))
            if j<9:
                file.write(',')
        file.write('\n')
        for k in range(10):
            file.write(str(k*e/100))
            if k<9:
                file.write(',')
        file.close()
            
    def fill_tray(composition, position):
        sample=Sample(composition)
        self.sh.fill_tray(sample, position)


        process.terminate()
        #spectrum_taker.take_spectrum()

    #l.release()
        
    
def take_wr():
    pass
    
def take_spectrum():
    pass

# if __name__=='__main__':
#     main()