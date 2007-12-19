import compiler
import operator
import parser
import re
from trac.core import TracError

try:
    set = set
except:
    from sets import Set as set

class Expression:
    """ Pass a set of tags through a basic expression filter.

        Expressions are valid, basic Python expressions.

        eg. Match all objects tagged with ticket and workflow, and not tagged
        with wiki or closed.

            (ticket and workflow) and not (wiki or closed)
        """
    __slots__ = ['ast', 'expression']
    __visitors = {}

    def __init__(self, expression):
        self.expression = expression.decode('utf-8')
        self.ast = compiler.parse(self.expression, 'eval')

    def get_tags(self):
        """ Fetch tags used in this expression. """
        tags = set()
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
        context = [tag.encode('utf-8') for tag in context] 
        return self._visit(self.ast, context)

    def _visit(self, node, context):
        v = self.__visitors.get(node.__class__)
        if not v:
            try:
                v = getattr(self, '_visit_%s' % node.__class__.__name__.lower())
            except AttributeError:
                raise TracError('invalid expression node "%s"' % node.__class__.__name__.lower()) 
            self.__visitors[node.__class__] = v
        return v(node, context)

    def _visit_expression(self, node, context):
        for child in node.getChildNodes():
            return self._visit(child, context)

    def _visit_sub(self, node, context):
        return self._visit(node.left, context) \
               and not self._visit(node.right, context)

    def _visit_not(self, node, context):
        return not self._visit(node.expr, context)

    def _visit_and(self, node, context):
        result = True
        for arg in node.nodes:
            result = result and self._visit(arg, context)
            if not result:
                return False
        return True

    _visit_add = _visit_and

    def _visit_or(self, node, context):
        result = False
        for arg in node.nodes:
            result = result or self._visit(arg, context)
            if result:
                return True
        return False

    _visit_bitor = _visit_or

    def _visit_name(self, node, context):
        return node.name in context

    def _visit_const(self, node, context):
        return node.value in context

    def _visit_unarysub(self, node, context):
        return not self._visit(node.expr, context)

    def _visit_tuple(self, node, context):
        return reduce(operator.and_, [self._visit(n, context) for n in node.nodes])
