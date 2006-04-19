import compiler
import operator
import re
from trac.core import TracError

try:
    set = set
except:
    from sets import Set as set

class Expression:
    """ Pass a set of tags through a basic expression filter.
    
        Supported operators are: unary - (not); binary +, - and | (and, and
        not, or). All values in the expression are treated as tags. Any tag
        not in the same form as a Python variable must be quoted.
        
        eg. Match all objects tagged with ticket and workflow, and not tagged
        with wiki or closed.
        
            (ticket+workflow)-(wiki|closed)
        """
    __slots__ = ['ast', 'expression']
    __visitors = {}

    def __init__(self, expression):
        tokenizer = re.compile(r'''"[^"]*"|'[^']*'|[-|,+()\[\]]|[^-,|+()\[\]\s]+''')
        expr = []
        for token in tokenizer.findall(expression):
            if token not in '-|+()[],' and token[0] not in '"\'':
                expr.append('"%s"' % token)
            else:
                expr.append(token)
        self.expression = ' '.join(expr)
        self.ast = compiler.parse(self.expression, 'eval')

    def get_tags(self):
        """ Fetch tags used in this expression. """
        tags = set()
        import parser
        def walk(node):
            if node[0] == 1:
                tags.add(node[1])
            elif node[0] == 3:
                tags.add(eval(node[1]))
            else:
                for i in range(1, len(node)):
                    if isinstance(node[i], tuple):
                        walk(node[i])
        tree = parser.expr(self.expression).totuple()
        walk(tree)
        return tags

    def __call__(self, context):
        return self._visit(self.ast, context)

    def _visit(self, node, context):
        v = self.__visitors.get(node.__class__)
        if not v:
            try:
                v = getattr(self, '_visit_%s' % node.__class__.__name__.lower())
            except AttributeError:
                raise TracError('invalid expression node "%s"' % str(node.__class__.__name__.lower()))
            self.__visitors[node.__class__] = v
        return v(node, context)

    def _visit_expression(self, node, context):
        for child in node.getChildNodes():
            return self._visit(child, context)

    def _visit_sub(self, node, context):
        return self._visit(node.left, context) \
               and not self._visit(node.right, context)

    def _visit_add(self, node, context):
        return self._visit(node.left, context) \
               and self._visit(node.right, context)

    def _visit_bitor(self, node, context):
        return self._visit(node.nodes[0], context) \
               or self._visit(node.nodes[1], context)

    def _visit_name(self, node, context):
        return node.name in context

    def _visit_const(self, node, context):
        return node.value in context

    def _visit_unarysub(self, node, context):
        return not self._visit(node.expr, context)

    def _visit_tuple(self, node, context):
        return reduce(operator.and_, [self._visit(n, context) for n in node.nodes])
