#!/usr/bin/env python

import random
import urllib

class WordChooser(object):
    """chose a random word given a dict file"""
    wordlist = []
    def __init__(self, dictfile, min_len=5):
        if not getattr(WordChooser, 'dictfile', '') == dictfile:
            if dictfile.startswith("http://"):
                f = urllib.urlopen(dictfile)
            else:
                f = open(dictfile, 'r')
            _dict = f.read()
            f.close()
            _dict = _dict.lower().split()
            _dict = [word for word in _dict if word.isalpha() and len(word) > min_len]
            WordChooser.wordlist = _dict
            WordChooser.dictfile = dictfile

    def __call__(self):
        return random.Random().choice(self.wordlist)

def random_word(dictfile):
    chooser = WordChooser(dictfile)
    return chooser()
    

if __name__ == '__main__':
    foo = WordChooser('http://java.sun.com/docs/books/tutorial/collections/interfaces/examples/dictionary.txt')
    print foo()

