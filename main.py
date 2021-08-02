class Expr():
    """
    Base class for expressions
    """

    def __mul__(self, other):
        return Mul(self, other)

    def __rmul__(self, other):
        return Mul(other, self)

    def __add__(self, other):
        return Add(self, other)

    def __radd__(self, other):
        return Add(other, self)

    def __sub__(self, other):
        return self + -other

    def __neg__(self):
        return -1 * self

    def __eq__(self, other):
        # easy cases
        if self is other:
            return True

        # We want Integer(5) == 5
        # if type(self) != type(other):
        #     return False

        # FIXME: Extremely slow and stupid, use hashes or something
        return repr(self) == repr(other)

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        return repr(self)


class BinaryOp(Expr):
    def __init__(self, lhs, rhs):
        self.args = [to_expr(lhs), to_expr(rhs)]

    @property
    def op(_):
        raise NotImplementedError


class AssocOp(BinaryOp):
    """Associative property for op *
    (a * b) * c = a * (b * c) = a * b * c
    """
    pass


class DistOp(BinaryOp):
    """Distribute w/r to addition (for op *)
    a * (b + c) = a * b + b * c
    """
    pass

class Mul(AssocOp, DistOp):
    @property
    def op(_):
        return '*'

    def __repr__(self):
        return f'({self.args[0]} * {self.args[1]})'


class Add(AssocOp, DistOp):
    @property
    def op(_):
        return '+'

    def __repr__(self):
        return f'({self.args[0]} + {self.args[1]})'


class AtomicExpr(Expr):
    """
    An Atom is an expression with no subexpressions
    """
    def __init__(self):
        super().__init__()
        self.args = []


class Symbol(AtomicExpr):
    def __init__(self, name: str):
        super().__init__()
        assert isinstance(name, str), f'name of Symbol must be str, got {type(name)}'
        self.name = name

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, Symbol) and self.name == other.name


class Integer(AtomicExpr):
    def __init__(self, value: int):
        super().__init__()
        assert isinstance(value, int), f'type(value) {type(value)} != int'
        self.value = value

    def __repr__(self):
        return str(self.value)

    def __add__(self, other):
        other = to_expr(other)
        # we know self is an Integer so we only haveto check other
        if isinstance(other, Integer):
            return Integer(self.value + other.value)

        return Add(self, other)


def derivative(expr: Expr, var: Symbol):
    """
    Take the derivative of expr with respect to var
    >>> derivative(Symbol('x')*2, Symbol('x'))
    2
    >>> derivative(Symbol('x')*Symbol('x'), Symbol('x'))
    (2 * x)
    >>> derivative(Symbol('x')*Symbol('x')*Symbol('x'), Symbol('x'))
    (3 * x * x)
    """
    expr = simplify(to_expr(expr))

    if isinstance(expr, Add):
        return simplify(derivative(expr.args[0], var) + derivative(expr.args[1], var))
    elif isinstance(expr, Mul):
        # product rule
        return simplify(
            derivative(expr.args[0], var)*expr.args[1]
            + derivative(expr.args[1], var)*expr.args[0]
        )
    elif isinstance(expr, Integer):
        return to_expr(0)
    elif isinstance(expr, Symbol):
        return to_expr(1) if expr == var else to_expr(0)

    raise ValueError(f'not expecting {type(expr)}')


def is_zero(expr: Expr):
    return expr == Integer(0)

def simplify(expr: Expr):
    """
    Simplify an expression
    >>> simplify(Symbol('x') + 0)
    x
    >>> simplify(Symbol('x')*0)
    0
    >>> simplify(Symbol('x')*1)
    x
    >>> simplify((1 * Symbol('x')) + (1 * Symbol('x')))
    (2 * x)
    """
    expr = to_expr(expr)
    if isinstance(expr, AtomicExpr):
        return expr
    elif isinstance(expr, Add):
        a = simplify(expr.args[0])
        b = simplify(expr.args[1])
        if is_zero(a): return b
        if is_zero(b): return a
        if a == b: return 2*a
        return a + b
    elif isinstance(expr, Mul):
        a = simplify(expr.args[0])
        b = simplify(expr.args[1])
        if is_zero(a) or is_zero(b):
            return to_expr(0)
        if a == Integer(1): return b
        if b == Integer(1): return a
        return a*b
    else:
        raise ValueError(f'{type(expr)} is not handled')


def to_expr(thing):
    """Convert a python type to an algebruh type if possible
    >>> to_expr(5) == Integer(5)
    True
    >>> to_expr(5) == 5
    True
    >>> isinstance(to_expr(5), Integer)
    True
    """
    if isinstance(thing, Expr):
        return thing

    if isinstance(thing, int):
        return Integer(thing)

    raise ValueError(f'Cannot convert {thing} to Expr')


def to_sexpr(expr):
    """Convert expr to an s-expression
    >>> to_sexpr(Integer(2) + Integer(3) * Integer(4))
    '(+ 2 (* 3 4))'
    """

    if isinstance(expr, BinaryOp):
        return f'({expr.op} {" ".join(map(to_sexpr, expr.args))})'
    elif isinstance(expr, AtomicExpr):
        return str(expr)
    else:
        raise ValueError(f'unsupported type {type(expr)}')


if __name__ == '__main__':
    import doctest
    doctest.testmod()
