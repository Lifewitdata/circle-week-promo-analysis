"""Execute the same named analytical queries locally and in BigQuery."""
import re
import duckdb


def named_queries(path, dataset=None):
    parts = re.split(r'^-- name: ([a-z0-9_]+)\s*$', path.read_text(), flags=re.M)
    queries = {}
    for name, sql in zip(parts[1::2], parts[2::2]):
        if dataset:
            sql = sql.replace('{{dataset}}', dataset)
        else:
            sql = re.sub(r'`\{\{dataset\}\}\.([a-z_]+)`', r'\1', sql)
        queries[name] = sql.strip().rstrip(';')
    if not queries:
        raise ValueError('No named queries found')
    return queries


def build(sales, stores, products, promotions, sql_path, output):
    output.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    try:
        for name, frame in [('sales_weekly', sales), ('stores', stores), ('products', products), ('promotions', promotions)]:
            con.register('input_frame', frame)
            con.execute(f'CREATE TABLE {name} AS SELECT * FROM input_frame')
        con.execute('CREATE MACRO SAFE_DIVIDE(a,b) AS (a*1.0 / NULLIF(b,0))')
        outputs = {}
        for name, sql in named_queries(sql_path).items():
            frame = con.execute(sql).df()
            frame.to_csv(output/f'{name}.csv', index=False)
            outputs[name] = frame
        return outputs
    finally:
        con.close()
