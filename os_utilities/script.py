# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/script.ipynb (unless otherwise specified).

__all__ = ['store_attr', 'str2bool', 'store_true', 'store_false', 'bool_arg', 'args_from_prog', 'call_parse',
           'maybe_attr', 'basic_repr', 'CustomFormatter', 'is_array', 'is_iter', 'listify', 'clean_type', 'Param',
           'anno_parser', 'assign_doc', 'clean_md_lines', 'show_docs']

# Cell
import argparse
import inspect
import functools
import distutils
import sys
import re

from IPython.display import Markdown

# Cell
def _store_attr(self, anno, **attrs):
    for n,v in attrs.items():
        if n in anno: v = anno[n](v)
        setattr(self, n, v)
        self.__stored_args__[n] = v

def store_attr(names=None, self=None, but=None, cast=False, **attrs):
    "Store params named in comma-separated `names` from calling context into attrs in `self`"
    fr = sys._getframe(1)
    args = fr.f_code.co_varnames[:fr.f_code.co_argcount]
    if self: args = ('self', *args)
    else: self = fr.f_locals[args[0]]
    if not hasattr(self, '__stored_args__'): self.__stored_args__ = {}
    anno = self.__class__.__init__.__annotations__ if cast else {}
    if attrs: return _store_attr(self, anno, **attrs)
    ns = re.split(', *', names) if names else args[1:]
    _store_attr(self, anno, **{n:fr.f_locals[n] for n in ns if n not in listify(but)})

# Cell
def str2bool(s):
    "Case-insensitive convert string `s` too a bool (`y`,`yes`,`t`,`true`,`on`,`1`->`True`)"
    if not isinstance(s,str): return bool(s)
    return bool(distutils.util.strtobool(s)) if s else False

# Cell
def store_true():
    "Placeholder to pass to `Param` for `store_true` action"
    pass

def store_false():
    "Placeholder to pass to `Param` for `store_false` action"
    pass

def bool_arg(v):
    "Use as `type` for `Param` to get `bool` behavior"
    return str2bool(v)

def args_from_prog(func, prog):
    "Extract args from `prog`"
    if prog is None or '#' not in prog: return {}
    if '##' in prog: _,prog = prog.split('##', 1)
    progsp = prog.split("#")
    args = {progsp[i]:progsp[i+1] for i in range(0, len(progsp), 2)}
    for k,v in args.items():
        t = func.__annotations__.get(k, Param()).type
        if t: args[k] = t(v)
    return args

def call_parse(func):
    "Decorator to create a simple CLI from `func` using `anno_parser`"
    mod = inspect.getmodule(inspect.currentframe().f_back)
    if not mod: return func

    @functools.wraps(func)
    def _f(*args, **kwargs):
        mod = inspect.getmodule(inspect.currentframe().f_back)
        if not mod: return func(*args, **kwargs)
        p = anno_parser(func)
        args = p.parse_args().__dict__
        xtra = otherwise(args.pop('xtra', ''), eq(1), p.prog)
        tfunc = trace(func) if args.pop('pdb', False) else func
        tfunc(**merge(args, args_from_prog(func, xtra)))

    if mod.__name__=="__main__":
        setattr(mod, func.__name__, _f)
        return _f()
    else: return _f

# Cell
def maybe_attr(o, attr):
    "`getattr(o,attr,o)`"
    return getattr(o,attr,o)

def basic_repr(flds=None):
    if isinstance(flds, str): flds = re.split(', *', flds)
    flds = list(flds or [])
    def _f(self):
        sig = ', '.join(f'{o}={maybe_attr(getattr(self,o), "__name__")}' for o in flds)
        return f'{self.__class__.__name__}({sig})'
    return _f

# Cell
class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter): pass

# Cell
def is_array(x):
    "`True` if `x` supports `__array__` or `iloc`"
    return hasattr(x,'__array__') or hasattr(x,'iloc')

# Cell
def is_iter(o):
    "Test whether `o` can be used in a `for` loop"
    #Rank 0 tensors in PyTorch are not really iterable
    return isinstance(o, (Iterable,Generator)) and getattr(o,'ndim',1)

# Cell
def listify(o):
    "Convert `o` to a `list`"
    if o is None: return []
    if isinstance(o, list): return o
    if isinstance(o, str) or is_array(o): return [o]
    if is_iter(o): return list(o)
    return [o]

# Cell
def clean_type(t:str):
    doc = str(t)
    doc = doc.replace('class ','')
    doc = doc.replace('<', '').replace('>', '')
    doc = doc.replace("'", '')
    doc = doc.replace('__main__.', '')
    return doc

# Cell
class Param:
    "A parameter in a function used in `anno_parser` or `call_parse`"
    #__repr__=basic_repr('help')
    def __init__(self, help=None, type=None, opt=True, action=None, nargs=None, const=None,
                 choices=None, required=None, alias=None, metavar='', default=None):
        if type==store_true:  type,action,default=None,'store_true' ,False
        if type==store_false: type,action,default=None,'store_false',True
        store_attr()

    def set_default(self, d):
        if self.default is None:
            if d==inspect.Parameter.empty: self.required = False
            else: self.default = d

    @property
    def pre(self): return '--' if self.opt else ''
    @property
    def kwargs(self): return {k:v for k,v in self.__dict__.items()
                              if v is not None and k!='opt' and k[0]!='_' and k!='alias'}
    def __repr__(self):
        if self.help is not None:
              return f"{clean_type(self.type)} ({self.help})"
        else: return f"{clean_type(self.type)}"

# Cell
def anno_parser(func, prog=None, description=None, usage=None, epilog=None):
    "Look at params (annotated with `Param`) in func and return an `ArgumentParser`"
    p = argparse.ArgumentParser(
        description=func.__doc__, prog=prog, usage=usage,
        formatter_class=CustomFormatter)
    for k,v in inspect.signature(func).parameters.items():
        param = func.__annotations__.get(k, Param())
        param.set_default(v.default)
        if param.opt is not None:
            if param.alias is None: p.add_argument(f"{param.pre}{k}", **param.kwargs)
            else: p.add_argument(f"-{param.alias}", f"--{k}", **param.kwargs)
        else:
            p.add_argument(f"{param.pre}{k}", **param.kwargs)
    p.add_argument(f"--pdb", help="Run in pdb debugger", action='store_true')
    p.add_argument(f"--xtra", help="Parse for additional args", type=str)
    return p

# Cell
from typing import Callable
def assign_doc(func:Callable, docs:str):
    assert inspect.isfunction(func)
    assert isinstance(docs,str)
    func.__doc__ = docs

# Cell
def clean_md_lines(x): return x.replace('\n', '<br>')

def show_docs(func:Callable):
    "Return markdown of `func`'s __doc__'"
    doc = func.__doc__
    doc = clean_md_lines(doc)
    return Markdown(doc)