# -*- coding: utf-8 -*-
'''
Created on 18 nov. 2010

@author: thierry
'''


import os.path
import random
from optparse import OptionParser

class ResultDestination():
    def open(self):
        raise NotImplementedError()
    
    def close(self):
        raise NotImplementedError()
    
    def write(self,pathname):
        raise NotImplementedError()

class ConsoleDestination(ResultDestination):

    def open(self):
        pass


    def close(self):
        pass


    def write(self, pathname):
        print pathname

    

class FileDestination(ResultDestination):
    def __init__(self, _pathname):
        self.pathname = _pathname

    def open(self):
        return ResultDestination.open(self)


    def close(self):
        return ResultDestination.close(self)


    def write(self, pathname):
        return ResultDestination.write(self, pathname)




class RandomListCreator(object):
    SIZE_LIMIT = None
    GLOBAL_SIZE_LIMIT = None
    VALID_TYPE = []

    def __init__(self, size_limit=None, global_size_limit=None, _directory=None, _destination=None):
        if size_limit:
            self.SIZE_LIMIT = size_limit * 1024 * 1024
        if global_size_limit:
            self.GLOBAL_SIZE_LIMIT = global_size_limit * 1024 * 1024
        if _destination:
            self.destination = FileDestination(_destination)
        else:
            self.destination = ConsoleDestination()
        self.directory = _directory

    def accept_file(self, f):
        if self.SIZE_LIMIT :
            if os.path.getsize(f) > self.SIZE_LIMIT :
                return False
        name,ext, = os.path.splitext(f)
        ext_upper = ext.upper()   
        return ext_upper in self.VALID_TYPE





    def list_document(self):
            if not self.directory :
                self.directory = os.getcwdu()
            for root, dirs, files in os.walk(self.directory):                
                for accepted in filter(self.accept_file,map(lambda(x): os.path.join(root, x), files)):                
                    yield accepted

    def write_play_list(self,doc):
        self.destination.write(doc)
        

    def create_random_list(self):        
        self.destination.open()
        if self.GLOBAL_SIZE_LIMIT :
            basket = [ doc for doc in  self.list_document()]
            random.shuffle(basket)
            current_global_size = 0
            for doc in basket:
                file_size = os.path.getsize(doc)
                if (current_global_size + file_size < self.GLOBAL_SIZE_LIMIT):
                    current_global_size += file_size
                    self.write_play_list(doc)                    
        else:
            for doc in self.list_document():
                self.write_play_list(doc)
        self.destination.close()