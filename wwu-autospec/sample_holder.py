# import imp
# 
# import sample
# imp.reload(sample)
# from sample import Sample

class Sample_holder:

    def __init__(self, num_trays, wr_tray=None):
        self.num_trays=num_trays
        self.samples=[]
        self.full_trays=dict()
        for i in range(num_trays):
            self.full_trays[i]=None
        
        
    def fill_tray(self, s, tray_num=None):
        if s.position is not None and tray_num is None:
            print('keeping '+s.composition+' at position '+str(s.position))
            return
        if None not in self.full_trays.values():
            print('WARNING! Sample holder is already full. Not adding sample.')
            return
        if tray_num:
            if tray_num<len(self.full_trays) and tray_num>=0 and self.full_trays[tray_num]==None:
                if s.position is not None:
                    self.rm_sample(s)
                self.add_sample(s, tray_num)
                
            else:
                print('WARNING! Invalid tray specified.')
                if s.position is not None:
                    print('keeping '+s.composition+' at position '+str(s.position))
                    return
                else:
                    for i in self.full_trays:
                        if self.full_trays[i]==None:
                            self.add_sample(s, i)
                            #print('putting '+s.composition+' at position '+str(s.position))
                            return
        else:
            for i in self.full_trays:
                if self.full_trays[i]==None:
                    self.add_sample(s, i)
                    #print('Putting '+s.composition+ ' in tray '+str(i))
                    return
                
            
    def rm_sample(self, s):
        self.full_trays[s.position]=None
        s.position=None
        
    def add_sample(self, s, pos):
        self.full_trays[pos]=s
        s.position=pos






    
        
    @property
    def num_trays(self):
        return __num_trays

    @num_trays.setter
    def num_trays(self, num_trays):
        self.__num_trays = num_trays
        
