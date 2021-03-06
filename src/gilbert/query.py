import operator


class Query:
    def __init__(self, expr):
        self.query = AstNode.build(expr)

    def __call__(self, context):
        return self.query(context)


class AstNode:
    __ops__ = {}

    def __init_subclass__(cls, operator, **kwargs):
        super().__init_subclass__(**kwargs)
        if operator is not None:
            AstNode.__ops__[operator] = cls

    @staticmethod
    def build(term):
        if isinstance(term, (int, float, str)):
            return term

        assert isinstance(term, dict)

        operator, args = list(term.items())[0]

        args = [AstNode.build(arg) for arg in args]
        return AstNode.__ops__[operator](*args)

    def resolve(self, term, context):
        if isinstance(term, (int, float, str)):
            return term

        return term(context)


class Attr(AstNode, operator='attr'):
    def __init__(self, name):
        self.name = name

    def __call__(self, context):
        name = self.resolve(self.name, context)

        return getattr(context, name)


class All(AstNode, operator='all'):

    def __init__(self, *terms):
        self.terms = terms

    def __call__(self, context):
        return all(
            term(context)
            for term in self.terms
        )


class Any(AstNode, operator='any'):

    def __init__(self, *terms):
        self.terms = terms

    def __call__(self, context):
        return any(
            term(context)
            for term in self.terms
        )


class BooleanNode(AstNode, operator=None):

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __call__(self, context):
        left = self.resolve(self.left, context)
        right = self.resolve(self.right, context)

        return self.op(left, right)


class Not(BooleanNode, operator='not'):
    op = operator.not_


class Lt(BooleanNode, operator='lt'):
    op = operator.lt


class Le(BooleanNode, operator='le'):
    op = operator.le


class Equal(BooleanNode, operator='eq'):
    op = operator.eq


class NotEqual(BooleanNode, operator='ne'):
    op = operator.ne


class Ge(BooleanNode, operator='ge'):
    op = operator.ge


class Gt(BooleanNode, operator='gt'):
    op = operator.gt


class StartsWith(AstNode, operator='startswith'):
    def __init__(self, value, prefix):
        self.value = value
        self.prefix = prefix

    def __call__(self, context):
        value = self.resolve(self.value, context)
        prefix = self.resolve(self.prefix, context)

        return value.startswith(prefix)


class Contains(AstNode, operator='contains'):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __call__(self, context):
        left = self.resolve(self.left, context)
        right = self.resolve(self.right, context)

        return right in left
