# -*- coding: utf-8 -*-

import os.path
import random
from optparse import OptionParser

from gomedia.core import RandomListCreator




class VideoListCreator(RandomListCreator):


    def __init__(self, size_limit=None, global_size_limit=None, _directory=None, _destination=None):
        RandomListCreator.__init__(self,size_limit,global_size_limit, _directory,_destination)
        self.VALID_TYPE = ['.MPG','.AVI','.MP4','.DAT','MPEG','DIVX','OGG','MKV']

                
def run():
    usage = "%prog [-s <max file size>] [-m <global max size>] [-d <dir to scan>]"
    str_version = "%prog 0.1"
    parser = OptionParser(usage=usage, version=str_version)
    parser.add_option("-s", "--size", action="store", type="int", dest="max_file_size", help="max size of each file in MB")
    parser.add_option("-m", "--max", action="store", type="int", dest="max_global_size", help="max size of the global files set in MB")
    parser.add_option("-d", "--dircetory", action="store", type="string", dest="directory", help="root dircetory to scan for media files")
    parser.add_option("-o", "--output", action="store", type="string", dest="output", help="file to write the random file set to")    
    options, args = parser.parse_args()    
    VideoListCreator(options.max_file_size, options.max_global_size, options.directory, options.output).create_random_list()



if __name__ == "__main__":
    
   run()
