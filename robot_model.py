import sys
from threading import Lock
import time
import subprocess
import pexpect
import imp
import numpy as np

import sample
imp.reload(sample)
from sample import Sample

import sample_holder
imp.reload(sample_holder)
from sample_holder import Sample_holder

# import drawing
# imp.reload(drawing)
# from drawing import Drawing

import motor
imp.reload(motor)
from motor import Motor

import detector
imp.reload(detector)
from detector import Detector

import sample
imp.reload(sample)
from sample import Sample

test=True

class Model:

    def __init__(self, view, plotter):
        
        self.view=view
        self.plotter=plotter
            
        self.wr=Sample('wr')
        self.s1=Sample('Mars!')
        self.sh=Sample_holder(3)
        self.sh.fill_tray(self.wr,0)
        self.sh.fill_tray(self.s1,1)
    
        self.m_i=Motor('incidence')
        self.m_e=Motor('emission')
        self.m_a=Motor('azimuth')
        
        self.detector=Detector()
        self.i_e_tuples=[]
        
    def plot(self):
        self.plotter.plot_spectrum(10,10,[[1,2,3,4,5],[1,2,3,4,5]])

    def go(self, incidence, emission):

        self.i_e_tuples=[]

        # process = pexpect.spawnu('python3',ignore_sighup=False) #change to True to kill ssh?

        #   process.expect('>>> ')  
        # process.sendline('import time')
        # process.expect('>>> ')
        # 
        rs3_process=0
        pi_process=0
        if not test:
            rs3_process=pexpect.spawnu('ssh MELISSA+RS3Admin@MELISSA.univ.dir.wwu.edu')
            rs3_process.expect('Are you sure you want to continue connecting (yes/no)?')
            print('process says 1:')
            print(rs3_process.before)
            rs3_process.sendline('yes')
            time.sleep('3')
            rs3_process.sendline('yes')
            print(rs3_process.after)
            #rs3_process.expect("MELISSA+RS3Admin@melissa.univ.dir.wwu.edu's password:")
            rs3_process.sendline('fieldspecadmin')
            print('process_says_2:')
            print(rs3_process.before)
            rs3_process.expect('$')
            
            pi_process=pexpect.spawnu('python3')
            pi_process.expect('>>>')
        else:
            test_process=pexpect.spawnu('python3')
            test_process.expect('>>>')
            test_process.sendline('print("hooray")')
            #print(test_process.before)
            print(test_process.after)

        
        for i in range(incidence['start'],incidence['end']+1):
            if (i-incidence['start'])%(incidence['increment']) != 0 and i != incidence['end'] and i != incidence['start']:
                continue
            self.move_light(i, pi_process)
            
            for e in range(emission['start'],emission['end']+1):
                if (e-emission['start'])%(emission['increment']) != 0 and e != emission['end'] and e != emission['start']:
                    continue
                print('taking spectrum at '+str(e))
                self.move_detector(e, pi_process)
                self.take_spectrum(i,e, rs3_process)
                data = np.genfromtxt('/home/khoza/test_data/test_'+str(i)+'_'+str(e)+'.csv', dtype=float,delimiter=',')

                print(data)
                self.plotter.plot_spectrum(i,e,data)
            
        if not test:
            rs3_process.terminate(force=True)
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
        if not test: 
            process.sendline('c:/users/rs3admin/anaconda3/python.exe c:/users/rs3admin/hozak/Python/spectrum_taker.py -sp')

        self.view.take_spectrum()
        self.detector.take_spectrum()
        self.i_e_tuples.append((i,e))
        print(self.i_e_tuples)
        
        name='test_'+str(i)+'_'+str(e)+'.csv'
        file=open('/home/khoza/test_data/'+name,'w')
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

if __name__=='__main__':
    main()