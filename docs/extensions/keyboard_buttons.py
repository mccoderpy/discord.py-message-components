#  The MIT License (MIT)
#
#  Copyright (c) 2015-2021 Rapptz & (c) 2021-present mccoderpy
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation
#  the rights to use, copy, modify, merge, publish, distribute, sublicense,
#  and/or sell copies of the Software, and to permit persons to whom the
#  Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.

# Credit to sphinx.ext.extlinks for being a good starter
# Copyright 2007-2020 by the Sphinx team
# Licensed under BSD.

from typing import Any, Dict, List, Tuple

from docutils import nodes, utils
from docutils.nodes import Node, system_message
from docutils.parsers.rst.states import Inliner

import sphinx
from sphinx.application import Sphinx
from sphinx.util.nodes import split_explicit_title
from sphinx.util.typing import RoleFunction


# A custom sphinx role that renders as a html element for a keyboard button using the "key" class
# Usage:
# :key:`<title>`

def make_key_role(
        typ: str,
        rawtext: str,
        text: str,
        lineno: int,
        inliner: Inliner,
        options: Dict = {},
        content: List[str] = []
    ) -> Tuple[List[Node], List[system_message]]:

        text = utils.unescape(text)
        has_explicit_title, title, key = split_explicit_title(text)
        print(has_explicit_title, title, key)
        pnode = nodes.inline('', '', nodes.inline(title, title, classes=['key']), classes=['key-combo'])
        return [pnode], []


def setup(app: Sphinx) -> Dict[str, Any]:
    app.add_role('key', make_key_role)
    return {'version': sphinx.__display_version__, 'parallel_read_safe': True}