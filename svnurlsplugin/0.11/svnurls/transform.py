from genshi.builder import tag
from genshi.core import Markup
from genshi.filters.transform import Transformer

class ListTransformer(object):
    """apply transforms to a list of items"""

    def __init__(self, items, transform):
        self.items = items
        self.transform = transform

    def __call__(self, stream):
        ctr = 0 # reset counter
        for mark, (kind, data, pos) in stream:
            if mark is not None:

                # create a tag -> stream 
                if kind == 'START':
                    # invoke a new transformer from the applicable item
                    transform = self.transform(items[ctr]) # XXX assumes a single argument to the ctor
                    xstream = [ (mark, (kind, data, pos)) ]
                else:
                    xstream.append((mark, (kind,data, pos)))

                if kind == 'END':
                    xstream.append((mark, (kind, data, pos)))

                    # make a generator
                    def genstream():
                        for mark, event in xstream:
                            yield mark, event

                    # yield the transformed items
                    for xmark, xevent in transform(genstream()):
                        yield xmark, xevent

                    ctr += 1 # increment counter
            else:
                # if mark is None, just yield stream bits
                yield mark, (kind, data, pos)

if __name__ == '__main__':
    
    import datetime
    from genshi.input import HTML
    from genshi.filters.transform import ReplaceTransformation

    # make a times-table to test
    nrows = 100
    ncols = 10

    table = [ [ i*j for i in range(ncols) ] for j in range(nrows) ]
    
    table = [ '<tr>%s</tr>' % ' '.join([ ('<td class="foo-%s">%s</td>' % (i, j))
                                         for i, j in enumerate(row) ]) 
              for row in table ]

    table = '<table>%s</table>' % '\n'.join(table)
    
    # data for the transforms
    items = [ 'f' * (i % 7) for i in range(nrows) ]

    # time old method
    stream = HTML(table)
    start = datetime.datetime.now()
    for idx, entry in enumerate(items):
        xpath = "//table//tr[%s]/td[@class='foo-2']" % (idx + 1)
        stream |= Transformer(xpath).apply(ReplaceTransformation(entry))
    oldresult = str(stream)
    end = datetime.datetime.now()
    oldtime = end-start

    # create a ListTransformer
    listtransformer = ListTransformer(items, ReplaceTransformation)

    # time ListTransformer
    stream = HTML(table)
    start = datetime.datetime.now()
    result = stream | Transformer("//td[@class='foo-2']").apply(listtransformer)
    result = str(result)
    end = datetime.datetime.now()
    newtime = end-start

    assert oldresult == result

    print 'Incremental method: %s' % oldtime
    print 'ListTransformer: %s' % newtime
