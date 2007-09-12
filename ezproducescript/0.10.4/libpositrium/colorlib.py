#!/usr/bin/env python
# this is coloring library for linux console

def fix(str):
	PF = "\033["
	SF = "\033[0m"
	return PF+str+SF

# -------------------------------
# base color
def black(str):
	return fix("0;30m"+str)

def red(str):
	return fix("0;31m"+str)

def green(str):
	return fix("0;32m"+str)

def brown(str):
	return fix("0;33m"+str)

def blue(str):
	return fix("0;34m"+str)

def purple(str):
	return fix("0;35m"+str)

def cyan(str):
	return fix("0;36m"+str)

def gray(str):
	return fix("0;37m"+str)

# ------------------------------
# light color
def bblack(str):
	return fix("1;30m"+str)

def bred(str):
	return fix("1;31m"+str)

def bgreen(str):
	return fix("1;32m"+str)

def bbrown(str):
	return fix("1;33m"+str)

def bblue(str):
	return fix("1;34m"+str)

def bpurple(str):
	return fix("1;35m"+str)

def bcyan(str):
	return fix("1;36m"+str)

def bgray(str):
	return fix("1;37m"+str)

# -----------------------------
# style
def underline(str):
	return fix("4m"+str)

def blink(str):
	return fix("5m"+str)

def reverse(str):
	return fix("7m"+str)

#def nazo(str):
#	return fix("6m"+str)

def hide(str):
	return fix("8m"+str)

if __name__ == '__main__':
	print "===== base color ===="
	print black("black()")
	print red("red()")
	print green("green()")
	print brown("brown()")
	print blue("blue()")
	print purple("purple()")
	print cyan("cyan()")
	print gray("gray()")
	
	print "===== bold color ===="
	print bblack("bblack()")
#	print bgray("bgray()")
	print bred("bred()")
	print bgreen("bgreen()")
	print bbrown("bbrown()")
	print bblue("bblue()")
	print bpurple("bpurple()")
	print bcyan("bcyan()")
	print bgray("bgray()")
	
	print "===== style ===="
	print underline("underline()")
	print blink("blink()")
	print reverse("reverse()")
#	print nazo("nazo()")
	print hide("hide()")
	
