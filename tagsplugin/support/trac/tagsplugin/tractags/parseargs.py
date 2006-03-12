"""
    Basic parsing of arguments into a non-keyword list and keyword dictionary.
"""

class UnexpectedEndOfInput(Exception): pass
class InvalidToken(Exception): pass
class UnexpectedToken(Exception): pass

class Lexer(object):
    """ Convenience wrapper around tokenize.generate_tokens """
    def __init__(self, string):
        from StringIO import StringIO
        import tokenize
        stream = StringIO(string)
        self.tokens = []
        for token in tokenize.generate_tokens(stream.readline):
            self.tokens.append(token[0:2])

    def __iter__(self):
        return self

    def next(self):
        if self.tokens:
            token = self.tokens.pop(0)
            if token[0] != 0:
                return token
        raise StopIteration

    def push_token(self, token):
        self.tokens.insert(0, token)

def parseargs(arguments):
    """ Parse a python-like set of arguments. """
    def parse_dict(lexer):
        out = {}
        try:
            for type, token in lexer:
                if token == '}':
                    return out
                lexer.push_token((type, token))
                key = parse_value(lexer)
                type, token = lexer.get_token()
                if token[1] not in '=:':
                    raise UnexpectedToken(token)
                value = parse_node(lexer)
        except StopIteration:
            pass
        raise UnexpectedEndOfInput

    def parse_array(lexer):
        out = []
        try:
            for type, token in lexer:
                if out and token == ',':
                    type, token = lexer.next()
                if token in '])':
                    return out
                lexer.push_token((type, token))
                out.append(parse_node(lexer))
        except StopIteration:
            pass
        raise UnexpectedEndOfInput
        
    def parse_value(lexer):
        type, token = lexer.next()
        if type == 2:
            return float(token)
        elif type == 3:
            return token[1:-1]
        elif type in (1, 51):
            return token
        else:
            raise InvalidToken(token)

    def parse_node(lexer):
        type, token = lexer.next()
        if token in '([':
            return parse_array(lexer)
        elif token == '{':
            return parse_dict(lexer)
        else:
            lexer.push_token((type, token))
            return parse_value(lexer)
            
    lexer = Lexer(arguments)
    args = []
    kwargs = {}

    try:
        while True:
            arg = parse_value(lexer)
            try:
                type, token = lexer.next()
            except StopIteration:
                args.append(arg)
                break
            if token == '=':
                kwargs[arg] = parse_node(lexer)
                type, token = lexer.next()
                if token != ',':
                    raise UnexpectedToken(token)
            elif token == ',':
                args.append(arg)
    except StopIteration:
        pass
    return args, kwargs

if __name__ == '__main__':
    print parseargs('foo, bar')
