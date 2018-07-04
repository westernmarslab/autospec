class Sample(object):
    
    def __init__(self, composition):
        self.composition=composition
        self.position=None
        
    @property
    def composition(self):
        return self.__composition

    @composition.setter
    def composition(self, composition):
        self.__composition = composition

    @property
    def position(self):
        return self.__position

    @position.setter
    def position(self, position):
        self.__position = position

        
        