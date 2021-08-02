from functools import wraps

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

        # FIXME: Extremely slow and stupid, use hashes or something
        return repr(to_expr(self)) == repr(to_expr(other))

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

    def __getitem__(self, attr):
        return self.args[attr]

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
        return f'({self[0]} * {self[1]})'


class Add(AssocOp, DistOp):
    @property
    def op(_):
        return '+'

    def __repr__(self):
        return f'({self[0]} + {self[1]})'


class AtomicExpr(Expr):
    """
    An Atom is an expression with no subexpressions
    """
    def __init__(self):
        super().__init__()


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


def to_expr_ret(fn):
    @wraps(fn)
    def _fn(*args, **kwargs):
        return to_expr(fn(*args, **kwargs))
    return _fn


@to_expr_ret
def simplify(expr: Expr):
    """
    Simplify an expression
    >>> simplify(x + 0)
    x
    >>> simplify(x*0)
    0
    >>> simplify(x*1)
    x
    >>> simplify((1 * x) + (1 * x))
    (2 * x)
    """
    expr = to_expr(expr)
    if isinstance(expr, AtomicExpr):
        return expr
    elif isinstance(expr, Add):
        a = simplify(expr.args[0])
        b = simplify(expr.args[1])
        if a == 0: return b
        if b == 0: return a
        if a == b: return 2*a
        return a + b
    elif isinstance(expr, Mul):
        a = simplify(expr.args[0])
        b = simplify(expr.args[1])
        if a == 0 or b == 0: return to_expr(0)
        if a == 1: return b
        if b == 1: return a
        return a*b
    else:
        raise ValueError(f'{type(expr)} is not handled')


def simplify_ret(fn):
    @wraps(fn)
    def _fn(*args, **kwargs):
        return simplify(fn(*args, **kwargs))
    return _fn


@simplify_ret
def derivative(expr: Expr, var: Symbol):
    """
    Take the derivative of expr with respect to var
    >>> derivative(x*2, x)
    2
    >>> derivative(x*x, x)
    (2 * x)
    """
    expr = simplify(to_expr(expr))

    if isinstance(expr, Add):
        return derivative(expr.args[0], var) + derivative(expr.args[1], var)
    elif isinstance(expr, Mul):
        # product rule
        return (
            derivative(expr.args[0], var)*expr.args[1]
            + derivative(expr.args[1], var)*expr.args[0]
        )
    elif isinstance(expr, Integer):
        return 0
    elif isinstance(expr, Symbol):
        return 1 if expr == var else 0
    else:
        raise ValueError(f'not expecting {type(expr)}')


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
    # symbols for use in testing
    x = Symbol('x')

    doctest.testmod()
    print('passed')
