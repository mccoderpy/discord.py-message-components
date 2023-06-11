# A Sphinx extension that looks up for operation implementations like __iter__, __lt__, __eq__, etc.
# and adds them to the class documentation as a container table
from __future__ import annotations

import inspect
from typing import Any, List, Dict, TYPE_CHECKING


if TYPE_CHECKING:
    from sphinx.application import Sphinx as SphinxApp

# This is a mapping of all the magic methods to a string that will be used to display them in the table
method_operator_map = {
    '__lt__': 'x < y',
    '__le__': 'x <= y',
    '__eq__': 'x == y',
    '__ne__': 'x != y',
    '__gt__': 'x > y',
    '__ge__': 'x >= y',
    '__add__': 'x + y',
    '__sub__': 'x - y',
    '__mul__': 'x * y',
    '__matmul__': 'x @ y',
    '__truediv__': 'x / y',
    '__floordiv__': 'x // y',
    '__mod__': 'x % y',
    '__divmod__': 'divmod(x, y)',
    '__pow__': 'x ** y',
    '__lshift__': 'x << y',
    '__rshift__': 'x >> y',
    '__and__': 'x & y',
    '__xor__': 'x ^ y',
    '__or__': 'x | y',
    '__radd__': 'y + x',
    '__rsub__': 'y - x',
    '__rmul__': 'y * x',
    '__rmatmul__': 'y @ x',
    '__rtruediv__': 'y / x',
    '__rfloordiv__': 'y // x',
    '__rmod__': 'y % x',
    '__rdivmod__': 'divmod(y, x)',
    '__rpow__': 'y ** x',
    '__rlshift__': 'y << x',
    '__rrshift__': 'y >> x',
    '__rand__': 'y & x',
    '__rxor__': 'y ^ x',
    '__ror__': 'y | x',
    '__iadd__': 'x += y',
    '__isub__': 'x -= y',
    '__imul__': 'x *= y',
    '__imatmul__': 'x @= y',
    '__itruediv__': 'x /= y',
    '__ifloordiv__': 'x //= y',
    '__imod__': 'x %= y',
    '__ipow__': 'x **= y',
    '__ilshift__': 'x <<= y',
    '__irshift__': 'x >>= y',
    '__iand__': 'x &= y',
    '__ixor__': 'x ^= y',
    '__ior__': 'x |= y',
    '__neg__': '-x',
    '__pos__': '+x',
    '__abs__': 'abs(x)',
    '__invert__': '~x',
    '__complex__': 'complex(x)',
    '__int__': 'int(x)',
    '__float__': 'float(x)',
    '__round__': 'round(x)',
    '__index__': 'operator.index(x)',
    '__trunc__': 'math.trunc(x)',
    '__floor__': 'math.floor(x)',
    '__ceil__': 'math.ceil(x)',
    '__enter__': 'with x as y: ...',
    '__await__': 'await x',
    '__aiter__': 'aiter(x) - (async for ... in x: ...)',
    '__anext__': 'await next(x)',
    '__aenter__': 'async with x as y: ...',
    '__call__': 'x()',
    '__len__': 'len(x)',
    '__length_hint__': 'operator.length_hint(x)',
    '__getitem__': 'x[y]',
    '__missing__': 'x[y]',
    '__setitem__': 'x[y] = z',
    '__delitem__': 'del x[y]',
    '__contains__': 'y in x',
    '__iter__': 'iter(x) - (for ... in x: ...)',
    '__reversed__': 'reversed(x)',
    '__next__': 'next(x)',
}


def handle_processed_docstring(
        app: SphinxApp,
        what: str,
        name: str,
        obj: object,
        options: Dict[str, Any],
        lines: List[str]
) -> List[str]:
    if what != 'class':
        return lines

    container_items = []
    if container_not_present := ('.. container:: operations' not in lines):
        # operations container not present yet? So we don't need to check for duplicates
        check = lambda n, v: v.__doc__ and inspect.isfunction(v) and n in method_operator_map
    else:
        check = lambda n, v: v.__doc__ and inspect.isfunction(v) and n in method_operator_map \
                          and f'    .. describe:: {method_operator_map[n]}' not in lines

    for f_name, special_method in (
            special_methods := sorted(
                filter(
                    lambda x: check(x[0], x[1]),
                    inspect.getmembers(obj)
                ),
                key=lambda x: list(method_operator_map).index(x[0]) if x[0] in method_operator_map else -1
            )):
        container_items.extend(
            [
                f'    .. describe:: {method_operator_map[f_name]}',
                '',
                *[f'        {line.lstrip()}' for line in special_method.__doc__.lstrip().splitlines()]
            ]
        )

    if container_items:
        if container_not_present:
            print(f'Creating supported operations container with {len(special_methods)} entries for class {name}')
            lines.extend(['', '.. container:: operations', ''])
        else:
            print(f'Updating supported operations container with {len(special_methods)} entries for class {name}')
        lines.extend(container_items)

    return lines


def setup(app: SphinxApp):
    app.connect('autodoc-process-docstring', handle_processed_docstring)
