#!/usr/bin/env python
import colorlib as cl

NONE = 0
FATAL = 1
INFO = 2
DEBUG = 3

log_level = DEBUG

def info(str):
	if log_level >= INFO:
		return "["+cl.green("INFO")+"] "+str
	else:
		return ""

def debug(str):
	if log_level >= DEBUG:
		return "["+cl.brown("DEBUG")+"] "+str
	else:
		return ""


def fatal(str):
	if log_level >= FATAL:
		return "["+cl.red("FATAL")+"] "+str
	else:
		return ""



if __name__ == '__main__':
	print cl.green("test")

