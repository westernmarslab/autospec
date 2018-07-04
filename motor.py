class Motor(object):

    def __init__(self, name, pos=0, range=[0,90]):
        self.name=name
        self.x=10
        self.position=pos
        self.range=range

        
    @property
    def x(self):
        return self.__x
    @x.setter
    def x(self, x):
        self.__x=x
        
    @property
    def position(self):
        return self.__position
    @position.setter
    def position(self,pos):
        if not hasattr(self,'__position'):
            self.__position=0
        # print('moving '+self.name)
        # diff=pos-self.position
        # command='print('+str(diff)+')'
        # print('Trying to move to ', str(pos), '...')
        # process.sendline( command )
        # process.expect('>>> ')
        # print(process.before)
    
        self.__position=pos
        
    # @position.setter
    # def position(self,pos):

            
        
