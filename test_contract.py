import copy,itertools,json,pathlib,random,sqlite3,subprocess,sys,tempfile,unittest
from sql_null_witness import analyze
ROOT=pathlib.Path(__file__).absolute().parent
def example():return json.loads((ROOT/'example.json').read_text())
class Contract(unittest.TestCase):
    def test_strict_cli_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=pathlib.Path(tmp)/'bad.json'
            for raw in ('{', '{"x":1,"x":2}', '{"x":NaN}', '{}', ' '*1048577):
                p.write_text(raw);r=subprocess.run([sys.executable,str(ROOT/'sql_null_witness.py'),str(p)],text=True,capture_output=True,timeout=5)
                self.assertEqual(r.returncode,2);self.assertTrue(r.stderr);self.assertFalse(r.stdout)
    def test_input_unchanged(self):
        x=example();saved=copy.deepcopy(x);analyze(x);self.assertEqual(x,saved)

    def test_example_unknown_where(self):
        r=analyze(example());self.assertEqual(r['kept_rows'],[2]);self.assertEqual([x['result'] for x in r['rows']],['UNKNOWN','UNKNOWN','TRUE'])
    def test_sqlite_truth_table_oracle(self):
        con=sqlite3.connect(':memory:')
        for a,b in itertools.product(('TRUE','FALSE','NULL'),repeat=2):
            for op in ('AND','OR'):
                predicate=f'{a} {op} {b}';v=con.execute('SELECT '+predicate).fetchone()[0];got=analyze({'predicate':predicate,'rows':[{}]})['rows'][0]['result'];self.assertEqual(got,'UNKNOWN' if v is None else 'TRUE' if v else 'FALSE')
    def test_sqlite_rows_and_precedence(self):
        con=sqlite3.connect(':memory:')
        for p in ('x NOT IN (1,NULL)','NOT (x = 1 OR x IS NULL)','x = 1 OR x = 2 AND x IS NOT NULL','x >= -1','x <> 1','x IN (2,3)','x IS NOT NULL'):
            for x in (None,-2,0,1,2,3):
                want=con.execute('SELECT '+p+' FROM (SELECT ? AS x)',(x,)).fetchone()[0];out=analyze({'predicate':p,'rows':[{'x':x}]})['rows'][0];self.assertEqual(out['result'],'UNKNOWN' if want is None else 'TRUE' if want else 'FALSE')
    def test_text_escape_and_missing(self):
        self.assertEqual(analyze({'predicate':"x = 'it''s'",'rows':[{'x':"it's"}]})['kept_rows'],[0])
        with self.assertRaisesRegex(ValueError,'missing column'):analyze({'predicate':'x = 1','rows':[{}]})
    def test_reject_coercion_and_full_sql(self):
        for p,row in [('x = 1',{'x':'1'}),('SELECT x',{}),('x LIKE 1',{'x':1}),('x IN ()',{'x':1}),('x=1; DROP TABLE x',{'x':1}),('TRUE = FALSE',{})]:
            with self.assertRaises(ValueError):analyze({'predicate':p,'rows':[row]})

if __name__ == '__main__':unittest.main()
