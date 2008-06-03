from genshi.filters.transform import Transformer

class ListTransformer(object):
    """apply transforms to a list of items"""

    def __init__(self, items):
        self.items = items

    def __call__(self, stream):
        for mark, (kind, data, pos) in stream:
            if mark is not None:
                pass
            yield mark, (kind, data, pos)

if __name__ == '__main__':
    
    import datetime

    # make a times-table to test
    nrows = 100
    ncols = 10

    table = [ [ i*j for i in range(ncols) ] for j in range(nrows) ]
    
    table = [ '<tr>%s</tr>' % ' '.join([ ('<td class="foo-%s">%s</td>' % (i, j))
                                         for i, j in enumerate(row) ]) 
              for row in table ]

    table = '<table>%s</table>' % '\n'.join(table)

    # time old method
    start = datetime.datetime.now()
    end = datetime.datetime.now()

    # time new method
    start = datetime.datetime.now()
    end = datetime.datetime.now()

    print table
