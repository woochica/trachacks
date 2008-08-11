import libxslt, urllib2, libxml2, sys, SocketServer, re
from os import makedirs

base_url = "http://trac.server.com/"
project_wiki_url = "myproject/wiki/"
project_attachments_url = "myproject/attachment/wiki/"
contents_url = "manuals/usermanual" # 'table of contents' wiki page. contains the links for each chapters

docbook_url_suffix = "?format=docbook"
raw_url_suffix = "?format=raw"
images_base_path = "figure/"
chapters_base_path = "chapter/"
useSVGsIfAvailable = False

contentsDocbook_stream = urllib2.urlopen(base_url + project_wiki_url + contents_url + docbook_url_suffix).read()
contentsDocbook_doc = libxml2.parseDoc(contentsDocbook_stream) #parseDoc always receives utf8, i think

contentsDocbook_xpc = contentsDocbook_doc.xpathNewContext()
nodes = contentsDocbook_xpc.xpathEval("//ulink/@url")

if len(nodes) == 0:
    print "no results"
    sys.exit(1)
else:

    getOriginalUrl_re = re.compile("""<imagedata fileref="/(.*?)".*/>""")
    
    for result in nodes:
        lastSlashIdx = str(result).rfind("/")
        chapter_url = base_url + str(result)[7:-1]
        chapter_slug = str(result)[lastSlashIdx+1:-1]
        try:
            chapterDocbook_stream = urllib2.urlopen(chapter_url + docbook_url_suffix).read()
        except urllib2.HTTPError:
            continue

        #find image urls, change them, and determine the new paths
        images_original_urls = getOriginalUrl_re.findall(chapterDocbook_stream) #myproject/attachment/wiki/manuals/usermanual/section1/untitled.png?format=raw
        images_modified_urls = [url.replace(".png", ".svg") for url in images_original_urls] #myproject/attachment/wiki/manuals/usermanual/section1/untitled.svg?format=raw
        images_newpath_pngfilenames = [images_base_path + url[len(project_attachments_url):-len(raw_url_suffix)] for url in images_original_urls] #figures/manuals/usermanual/untitled.png
        images_newpath_svgfilenames = [images_base_path + url[len(project_attachments_url):-len(raw_url_suffix)] for url in images_modified_urls] #figures/manuals/usermanual/untitled.svg
        images_newpath_filenames = []

        #save images
        for i in range(len(images_modified_urls)):
            image_stream = None
            if useSVGsIfAvailable:
                try:
                    image_stream = urllib2.urlopen(base_url + images_modified_urls[i]).read()
                    images_newpath_filenames.append(images_newpath_svgfilenames[i])
                except urllib2.HTTPError:
                    print "Could not retrieve image resource: " + images_modified_urls[i]

            if image_stream==None:
                try:
                    image_stream = urllib2.urlopen(base_url + images_original_urls[i]).read()
                    images_newpath_filenames.append(images_newpath_pngfilenames[i])
                except urllib2.HTTPError:
                    print "Could not retrieve image resource: " + images_original_urls[i]
                    sys.exit(1)

            dirEndIdx = images_newpath_filenames[i].rfind("/")+1
            try:
                makedirs(images_newpath_filenames[i][0:dirEndIdx])
            except OSError, x:
                #[Errno 17] File exists:
                pass
            image_file = file(images_newpath_filenames[i], "wb")
            image_file.write(image_stream)
            image_file.close()

        #save docbook files, changing them to have the right image paths, and unique ids
        for i in range(len(images_original_urls)):
            chapterDocbook_stream = chapterDocbook_stream.replace("/" + images_original_urls[i], images_newpath_filenames[i])
        chapterDocbook_stream = chapterDocbook_stream.replace("<section id=\"", "<section id=\"" + chapter_slug + "_")
        dbfile = file(chapters_base_path + "chapter_" + chapter_slug + ".xml", "w")
        dbfile.write(chapterDocbook_stream)
        dbfile.close()

contentsDocbook_doc.freeDoc()
contentsDocbook_xpc.xpathFreeContext()
