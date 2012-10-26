import textwrap
def header():
    header = """\
             <?xml version="1.0" encoding="UTF-8" standalone="no"?>
             """
    return textwrap.dedent(header)

def inkscapeDefinitions():
    defs = """\
              <defs
                id="defs31674">
                <marker
                   inkscape:stockid="Arrow2Lstart"
                   orient="auto"
                   refY="0.0"
                   refX="0.0"
                   id="Arrow2Lstart"
                   style="overflow:visible">
                  <path
                     id="path26427"
                     style="font-size:12.0;fill-rule:evenodd;stroke-width:0.62500000;stroke-linejoin:round"
                     d="M 8.7185878,4.0337352 L -2.2072895,0.016013256 L 8.7185884,-4.0017078 C 6.9730900,-1.6296469 6.9831476,1.6157441 8.7185878,4.0337352 z "
                     transform="scale(1.1) translate(1,0)" />
                </marker>
                <marker
                   inkscape:stockid="Arrow1Mend"
                   orient="auto"
                   refY="0.0"
                   refX="0.0"
                   id="Arrow1Mend"
                   style="overflow:visible;">
                  <path
                     id="path26418"
                     d="M 0.0,0.0 L 5.0,-5.0 L -12.5,0.0 L 5.0,5.0 L 0.0,0.0 z "
                     style="fill-rule:evenodd;stroke:#000000;stroke-width:1.0pt;marker-start:none;"
                     transform="scale(0.4) rotate(180) translate(10,0)" />
                </marker>
                <marker
                   inkscape:stockid="Arrow1Lend"
                   orient="auto"
                   refY="0.0"
                   refX="0.0"
                   id="Arrow1Lend"
                   style="overflow:visible;">
                  <path
                     id="path26412"
                     d="M 0.0,0.0 L 5.0,-5.0 L -12.5,0.0 L 5.0,5.0 L 0.0,0.0 z "
                     style="fill-rule:evenodd;stroke:#000000;stroke-width:1.0pt;marker-start:none;"
                     transform="scale(0.8) rotate(180) translate(12.5,0)" />
                </marker>
              </defs>
           """
    return textwrap.dedent(defs)

def format_attrs(attrs):
    """
    Convert the given dictionary into a string of svg attributes.
    e.g {'x': 10, 'y':20} --> ' x="10" y="20"'
    """
    # Use str.format to generate a big format string
    attr_txt = ''
    for attr in attrs.keys():
        attr_name = attr
        # Trailing underscores are added if the attr would otherwise be a python reserved word (e.g. 'class', 'id')
        if attr_name[-1] == '_':
            attr_name = attr_name[:-1]
        # Double-underscore maps to colon
        attr_name = attr_name.replace('__', ':')
        # All remaining underscores map to dashes
        attr_name = attr_name.replace('_', '-')
        attr_txt += ' {attr_name}="{attr_var}"'.format(attr_name=attr_name, attr_var='{' + attr + '}' )

    # Now opt_attr_txt is of the form "attr1={attr1} attr2={attr2}"
    # Format it with the attr dict to fill in the values
    return attr_txt.format(**attrs)

def format_tag(tag, atomic, standard_attrs, generic_attrs):
    formatted_tag = '<' + tag
    formatted_tag += format_attrs( standard_attrs )
    formatted_tag += format_attrs( generic_attrs )
    if atomic:
        formatted_tag += '/>\n'
    else:
        formatted_tag += '>\n'
    return formatted_tag

from collections import OrderedDict
class TagFormatter(object):
    """
    Generates a function that formats an svg tag.
    The generated function will have a signature of the form:
        def my_tag(standard_attr1, standard_attr2, ..., **generic_attrs)
    
    All underscores in attribute names are replaced with hyphens when the svg tag is produced.
    For example, calling: my_tag(some_attr1='A', attr2='B', generic_attr='C')
    produces svg tag: <my_tag some-attr1="A", attr2="B", generic-attr="C"/>

    tag: The tag name (e.g. 'rect')
    atomic: Set to true if the tag has no closing element (e.g. <rect/>)
    standard_attrs: A list of attributes that are considered standard for the tag.
                    These become the first arguments to the function.
                    In the output tag text, these attributes are listed first.
    """
    def __init__(self, tag, atomic, standard_attrs=[], **default_attr_values):
        self.tag = tag
        self.atomic = atomic
        self.standard_attrs = standard_attrs
        self.default_attr_values = default_attr_values

    def __call__(self, *args, **kwargs ):
        attrs = []
        assert len(args) <= len(self.standard_attrs)
        
        defaults = dict(self.default_attr_values)
        for key, value in kwargs.items():
            if key in defaults:
                del defaults[key]
        
        kwargs.update(defaults)
        
        for i, attr_name in enumerate(self.standard_attrs):
            if i < len(args):
                attrs.append( (attr_name, args[i]) )
            elif attr_name in kwargs:
                attrs.append( (attr_name, kwargs[attr_name]) )
                del kwargs[attr_name]
        return format_tag(self.tag, self.atomic, OrderedDict(attrs), kwargs)

svg = TagFormatter('svg', False, ['x', 'y', 'width', 'height'], xmlns__inkscape="http://www.inkscape.org/namespaces/inkscape" )
rect = TagFormatter('rect', True, ['x', 'y', 'width', 'height']) # Signature: rect(x, y, width, height, **optional_attrs)
circle = TagFormatter('circle', True, ['cx', 'cy', 'r'])
path = TagFormatter('path', True, ['d'])
text = TagFormatter('text', False)
textPath = TagFormatter('textPath', False)
tspan = TagFormatter('tspan', False, ['x', 'y'])
group = TagFormatter('g', False, ['class_', 'transform'])
connector_path = TagFormatter('path', True,
                              [ 'inkscape__connection_start',
                                'inkscape__connection_end' ],
                              style=textwrap.dedent('''\
                                                    fill:none;
                                                    stroke:#000000;
                                                    stroke-width:1px;
                                                    stroke-linecap:butt;
                                                    stroke-linejoin:miter;
                                                    stroke-opacity:1;
                                                    marker-end:url(#Arrow1Mend)
                                                    '''),
                              d="m 0, 0 1000,1000",
                              inkscape__connector_type="polyline",
                              inkscape__connector_curvature='0',
                              inkscape__connection_end_point="d4",
                              inkscape__connection_start_point="d4"
                              )
import contextlib
@contextlib.contextmanager
def tagblock(stream, formatter, *args, **kwargs):
    assert not formatter.atomic, "Can't make a tag context for atomic tag \"{}\"".format(formatter.tag)
    stream.write( formatter(*args, **kwargs) )
    stream.indent()
    yield
    stream.dedent()
    stream.write( '</' + formatter.tag + '>\n' )

from StringIO import StringIO
class IndentingStringIO(StringIO):
    def __init__(self, *args, **kwargs):
        StringIO.__init__(self, *args, **kwargs)
        self._indent = 0
    
    def indent(self):
        self._indent += 1

    def dedent(self):
        self._indent -= 1

    def write(self, s):
        prefix = ''
        if self.getvalue() and self.getvalue()[-1] == '\n':
            prefix = ' ' * self._indent
        suffix = ''
        if s[-1] == '\n':
            suffix = '\n'
            s = s[:-1]
        s = s.replace( '\n', '\n' + ' ' * self._indent )
        StringIO.write(self, prefix + s + suffix)
        
    def __iadd__(self, s):
        self.write(s)
        return self
    
    def __getitem__(self, i):
        return self.getvalue()[i]
    
    def __len__(self):
        return self.getvalue().__len__()

    def __iter__(self):
        return self.getvalue().__iter__()

class SvgCanvas(IndentingStringIO):
    def __init__(self, *args, **kwargs):
        IndentingStringIO.__init__(self, *args, **kwargs)
        self += header()
    
