from django import template
import re

register = template.Library()

class StripSpacesNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        output = self.nodelist.render(context)
        return re.sub(r'\s+', ' ', output).strip()

@register.tag(name='strip')
def do_strip_spaces(parser, token):
    nodelist = parser.parse(('endstrip',))
    parser.delete_first_token()
    return StripSpacesNode(nodelist)