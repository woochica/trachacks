

def graph(type, data, labels=[], colors=[], width=400, height=200, filename=None, title=None):
	import urllib2
        params = {}
        params['cht'] = str(type)
        params['chs'] = str(width) + "x" + str(height)
        params['chd'] = "t:" + ",".join(str(i) for i in data)
	if title is not None: params['chtt'] = str(title).replace(' ', '+')
        if len(labels) > 0: params['chl'] = "|".join(str(i) for i in labels)
	if len(colors) == 0:
		colors = [ 'ff6666', '66ff66', '6666ff', '888888', 'ffff66', '66ffff', 'ff66ff' ]
	params['chco'] = ",".join(colors)
        url = "http://chart.apis.google.com/chart?" + "&".join([ k + "=" + v for k, v in params.items() ])
        #print url
        img = urllib2.urlopen(url)
        if filename is not None:
                f = open(filename + '.png', 'w')
                f.write(img.read())
                f.close()

		def merge(a, b): return str(a) + " " + str(b) 
		tmp = map(merge, labels, data)

		f = open(filename + '.txt', 'w')
		if title is not None: f.write(title + "\n\n")
		f.write("\n".join(tmp))
		f.close()
        return img

