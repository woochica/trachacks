from genshi.builder import tag
from genshi.core import Markup
from genshi.filters.transform import Transformer

class ListTransformer(object):
    """apply transforms to a list of items"""

    def __init__(self, items, transform):
        self.items = items
        self.transform = transform

    def __call__(self, stream):
        ctr = 0
        for mark, (kind, data, pos) in stream:
            if mark is not None:

                # create a tag -> stream 
                if kind == 'START':
                    name = data[0]
                    attrs = dict([ (str(i), str(j)) for i, j in data[1]])
                if kind == 'TEXT':
                    text = data
                if kind == 'END':
                    newstream = getattr(tag, name)(text, attrs).generate()

                    # invoke a new transformer from the applicable item
                    item = items[ctr]
                    transform = self.transform(item) # XXX assumes a single argument to the ctor
                    for xmark, xevent in transform(newstream):
                        yield xmark, xevent
                    ctr += 1
            else:
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

    table = HTML('<table>%s</table>' % '\n'.join(table))

    # time old method
    start = datetime.datetime.now()
    end = datetime.datetime.now()

    # create a ListTransformer
    items = [ 'foo' ] * nrows
    listtransformer = ListTransformer(items, ReplaceTransformation)

    # time ListTransformer
    start = datetime.datetime.now()
    result = table | Transformer("//td[@class='foo-2']").apply(listtransformer)
    end = datetime.datetime.now()

    print result
