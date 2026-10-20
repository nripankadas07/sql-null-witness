"""Explain a strict SQL predicate subset with three-valued NULL evidence."""
import argparse, json, pathlib, sys

def need(ok, message):
    if not ok: raise ValueError(message)

def integer(n, low=0, high=10**9):
    need(type(n) is int and low <= n <= high, 'integer outside supported range')
    return n

def ident(s):
    need(type(s) is str and 0 < len(s) <= 80, 'invalid identifier')
    return s

def fields(obj, required, optional=()):
    need(type(obj) is dict and set(required) <= set(obj) <= set(required)|set(optional), 'missing or unknown fields')

def unique_pairs(pairs):
    out={}
    for k,v in pairs:
        need(k not in out, 'duplicate JSON key')
        out[k]=v
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input',type=pathlib.Path);a=p.parse_args()
    try:
        with a.input.open('rb') as f: raw=f.read(1048577)
        need(len(raw) <= 1048576, 'input exceeds 1 MiB')
        doc=json.loads(raw.decode('utf-8'),object_pairs_hook=unique_pairs,parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
        out=analyze(doc);print(json.dumps(out,ensure_ascii=True,sort_keys=True));return out.get('exit_code',0)
    except (ValueError,OSError,UnicodeError,RecursionError,OverflowError) as e:
        print(str(e),file=sys.stderr);return 2


import re

TOKEN=re.compile(r"\s*(?:(?P<string>'(?:[^']|'')*')|(?P<number>-?[0-9]+)|(?P<word>[A-Za-z_][A-Za-z_0-9]*)|(?P<op><=|>=|<>|!=|[=<>(),]))")

class Parser:
    def __init__(self,text):
        need(type(text) is str and 0<len(text)<=4096,'predicate must contain 1..4096 characters');self.ts=[];pos=0
        while pos<len(text):
            if text[pos:].isspace():break
            m=TOKEN.match(text,pos);need(m is not None,'unsupported SQL token at '+str(pos));pos=m.end();self.ts.append((m.lastgroup,m.group(m.lastgroup)))
        need(len(self.ts)<=256,'predicate exceeds 256 tokens');self.i=0
    def peek(self):return self.ts[self.i][1].upper() if self.i<len(self.ts) else ''
    def eat(self,s):
        if self.peek()==s:self.i+=1;return True
        return False
    def require(self,s):need(self.eat(s),'expected '+s)
    def parse(self):
        n=self.disjunction();need(self.i==len(self.ts),'trailing SQL tokens');return n
    def disjunction(self):
        n=self.conjunction()
        while self.eat('OR'):n=('or',n,self.conjunction())
        return n
    def conjunction(self):
        n=self.negation()
        while self.eat('AND'):n=('and',n,self.negation())
        return n
    def negation(self):
        if self.eat('NOT'):return ('not',self.negation())
        if self.eat('('):
            n=self.disjunction();self.require(')');return n
        left=self.value()
        if self.eat('IS'):
            negate=self.eat('NOT');self.require('NULL');return ('is_not_null' if negate else 'is_null',left)
        negate=self.eat('NOT')
        if self.eat('IN'):
            self.require('(');values=[self.value(literal_only=True)]
            while self.eat(','):values.append(self.value(literal_only=True))
            self.require(')');node=('in',left,values);return ('not',node) if negate else node
        need(not negate,'NOT must precede IN')
        op=self.peek()
        if op in ('=','<>','!=','<','<=','>','>='):self.i+=1;return ('cmp',op,left,self.value())
        need(left[0]=='lit' and (left[1] is None or type(left[1]) is bool),'bare predicate must be TRUE, FALSE or NULL');return ('truth',left)
    def value(self,literal_only=False):
        need(self.i<len(self.ts),'missing SQL value');kind,text=self.ts[self.i];self.i+=1
        if kind=='string':return ('lit',text[1:-1].replace("''","'"))
        if kind=='number':return ('lit',integer(int(text),-10**15,10**15))
        if kind=='word':
            if text.upper() in ('NULL','TRUE','FALSE'):return ('lit',{'NULL':None,'TRUE':True,'FALSE':False}[text.upper()])
            need(not literal_only and text.upper() not in ('AND','OR','NOT','IN','IS'),'expected literal');return ('column',text)
        raise ValueError('expected SQL value')

def value(node,row):
    if node[0]=='lit':return node[1]
    need(node[1] in row,'missing column '+node[1]);return row[node[1]]

def compare(a,b,op):
    if a is None or b is None:return None
    need(type(a) is type(b) and type(a) in (int,str),'comparisons require matching integer or text types')
    return {'=':a==b,'<>':a!=b,'!=':a!=b,'<':a<b,'<=':a<=b,'>':a>b,'>=':a>=b}[op]

def evaluate(n,row,trace):
    op=n[0]
    if op in ('and','or'):
        a=evaluate(n[1],row,trace);b=evaluate(n[2],row,trace)
        r=False if op=='and' and (a is False or b is False) else True if op=='or' and (a is True or b is True) else None if a is None or b is None else a and b if op=='and' else a or b
    elif op=='not':
        a=evaluate(n[1],row,trace);r=None if a is None else not a
    elif op=='truth':r=value(n[1],row)
    elif op=='cmp':r=compare(value(n[2],row),value(n[3],row),n[1])
    elif op in ('is_null','is_not_null'):
        r=value(n[1],row) is None
        if op=='is_not_null':r=not r
    elif op=='in':
        results=[compare(value(n[1],row),value(x,row),'=') for x in n[2]];r=True if True in results else None if None in results else False
    else:raise ValueError('unsupported expression')
    trace.append({'operation':op,'result':'UNKNOWN' if r is None else 'TRUE' if r else 'FALSE'});return r

def analyze(doc):
    fields(doc,('predicate','rows'));tree=Parser(doc['predicate']).parse()
    need(type(doc['rows']) is list and len(doc['rows'])<=1000,'rows exceed 1000');rows=[]
    for i,row in enumerate(doc['rows']):
        need(type(row) is dict and len(row)<=100,'invalid row')
        for k,v in row.items():
            ident(k);need(v is None or type(v) is str and len(v)<=4096 or type(v) is int and abs(v)<=10**15,'unsupported row value')
        trace=[];r=evaluate(tree,row,trace);rows.append({'row':i,'result':'UNKNOWN' if r is None else 'TRUE' if r else 'FALSE','passes_where':r is True,'trace':trace})
    return {'predicate':doc['predicate'],'ast':tree,'rows':rows,'kept_rows':[r['row'] for r in rows if r['passes_where']],'exit_code':0}

if __name__ == '__main__':
    raise SystemExit(main())
