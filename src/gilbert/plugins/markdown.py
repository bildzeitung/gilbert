from markdown2 import Markdown

from gilbert import Site
from gilbert.content import Content, Templated


class MarkdownPage(Templated, Content):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        markdown = Markdown()
        self.content = markdown.convert(self.content)


def load_md(path):
    content = path.read_text(encoding='utf-8')

    return content, {'content_type': 'MarkdownPage'}


Site.register_loader('md', load_md)
