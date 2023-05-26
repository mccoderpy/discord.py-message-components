from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sphinx.application import Sphinx as SphinxApp

from sphinx.util.docutils import SphinxDirective
from sphinx.locale import _
from docutils import nodes
from sphinx import addnodes


# A custom rst directive for sphinx that adds an admonition info, that this is an experimental discord feature and may be removed at any time
# This can also take an optional link to the support article for the feature that will be added to the warning
# Usage:
# .. experiment:: [title]
#    :article: [link-or-article-id]

class ExperimentalFeatureDirective(SphinxDirective):
    has_content = False
    required_arguments = 0
    optional_arguments = 40
    option_spec = {
        'article': str,
    }

    def run(self):
        title = ' '.join(self.arguments) if self.arguments else None
        title = f'Experimental Discord Feature - {title}' if title else 'Experimental Discord Feature'
        link_or_article_id = self.options.get('article', None)
        if link_or_article_id and not link_or_article_id.startswith('https://'):
            link = f'https://support.discord.com/hc/en-us/articles/{link_or_article_id}'
        else:
            link = link_or_article_id

        node = nodes.admonition(classes=['admonition', 'experimental'])
        node.document = self.state.document
        node += nodes.title(title, title)
        node += nodes.paragraph(text=_('This is an experimental feature and may be removed at any time.'))
        if link:
            ref = nodes.reference('', '', internal=False, refuri=link, anchorname='sus', *[nodes.Text(_('support article'))])
            node += nodes.paragraph(
                '',
                _('For more information, take a look at the '),
                *[addnodes.compact_paragraph('', '', ref)]
            )

        return [node]

def setup(app: SphinxApp):
    app.add_directive('experiment', ExperimentalFeatureDirective)
