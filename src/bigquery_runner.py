"""Optional GCP load, dry-run, execution and reconciliation. No credentials committed."""
import argparse
import json
import re
from pathlib import Path
from src.pipeline import ROOT
from src.warehouse import named_queries


def identifiers(project,dataset):
    if not re.fullmatch(r'[a-z][a-z0-9-]{4,61}[a-z0-9]',project) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,1023}',dataset):
        raise ValueError('Invalid GCP project or dataset identifier')
    return f'{project}.{dataset}'


def run(project,dataset,*,load=False,execute=False,benchmark=False):
    from google.cloud import bigquery
    name=identifiers(project,dataset)
    config=json.loads((ROOT/'config.json').read_text())
    client=bigquery.Client(project=project,location=config['bigquery_location'])
    out=ROOT/'reports/live_bigquery'
    out.mkdir(parents=True,exist_ok=True)
    schema={
        'sales_weekly':[('store_id','STRING'),('region','STRING'),('test_group','STRING'),('category_id','STRING'),('category_name','STRING'),('week_start_date','DATE'),('period','STRING'),('revenue','FLOAT64'),('units_sold','INTEGER')],
        'stores':[('store_id','STRING'),('region','STRING'),('store_format','STRING'),('sq_footage','INTEGER'),('test_group','STRING')],
        'products':[('category_id','STRING'),('category_name','STRING'),('base_weekly_revenue','INTEGER')],
        'promotions':[('promo_id','STRING'),('promo_name','STRING'),('category_targeted','STRING'),('promo_start_date','DATE'),('promo_end_date','DATE'),('design','STRING'),('expected_mechanism','STRING')]}
    jobs=[]
    if load:
        # Validate local source before incurring cloud work.
        import pandas as pd
        from src.validation import validate
        validate(*[pd.read_csv(ROOT/'data'/f'{n}.csv') for n in schema])
        ds=bigquery.Dataset(name);ds.location=config['bigquery_location']
        client.create_dataset(ds,exists_ok=True)
        for table,fields in schema.items():
            job_config=bigquery.LoadJobConfig(schema=[bigquery.SchemaField(n,t,mode='REQUIRED') for n,t in fields],source_format=bigquery.SourceFormat.CSV,skip_leading_rows=1,write_disposition='WRITE_TRUNCATE')
            if table=='sales_weekly':
                job_config.time_partitioning=bigquery.TimePartitioning(type_=bigquery.TimePartitioningType.DAY,field='week_start_date')
                job_config.clustering_fields=['category_id','store_id']
            with (ROOT/'data'/f'{table}.csv').open('rb') as f:
                job=client.load_table_from_file(f,f'{name}.{table}',job_config=job_config);job.result()
            jobs.append({'kind':'load','table':table,'job_id':job.job_id,'output_rows':job.output_rows})
    query_set=named_queries(ROOT/'sql/queries.sql',name)
    if benchmark:
        # Identical projection/results, alternative predicate shapes. Measure; do not assume savings.
        query_set.update({
            'benchmark_wide':f"SELECT store_id,week_start_date,revenue FROM `{name}.sales_weekly` WHERE EXTRACT(YEAR FROM week_start_date)=2026 AND EXTRACT(MONTH FROM week_start_date)=4 AND category_id='CAT04'",
            'benchmark_pruned':f"SELECT store_id,week_start_date,revenue FROM `{name}.sales_weekly` WHERE week_start_date BETWEEN DATE '2026-04-01' AND DATE '2026-04-30' AND category_id='CAT04'"})
    executed_results={}
    try:
        for key,sql in query_set.items():
            dry=client.query(sql,job_config=bigquery.QueryJobConfig(dry_run=True,use_query_cache=False))
            evidence={'kind':'query','name':key,'dry_run_bytes':dry.total_bytes_processed,'executed':False}
            if execute:
                q=client.query(sql,job_config=bigquery.QueryJobConfig(maximum_bytes_billed=config['maximum_bytes_billed'],use_query_cache=False))
                result=q.result()
                records=[dict(row.items()) for row in result]
                executed_results[key]=records
                (out/f'{key}.json').write_text(json.dumps(records,indent=2,default=str))
                evidence.update(executed=True,job_id=q.job_id,total_bytes_processed=q.total_bytes_processed,total_bytes_billed=q.total_bytes_billed,slot_millis=q.slot_millis)
                if key=='primary_effect':
                    import math
                    expected=json.loads((ROOT/'reports/summary.json').read_text())
                    if not all(math.isclose(records[0][k],expected[k],rel_tol=1e-9) for k in ['effect_usd_per_store_week','store_growth_gap_pp']):
                        raise AssertionError('BigQuery/local reconciliation failed')
                    evidence['local_reconciled']=True
            jobs.append(evidence)
        if execute and benchmark:
            canonical=lambda rows:sorted(json.dumps(row,sort_keys=True,default=str) for row in rows)
            if canonical(executed_results['benchmark_wide'])!=canonical(executed_results['benchmark_pruned']):
                raise AssertionError('Benchmark results differ; cannot compare scan efficiency')
        status='success'
    except Exception:
        (out/'execution_evidence.json').write_text(json.dumps({'status':'failed','jobs':jobs},indent=2,default=str))
        raise
    (out/'execution_evidence.json').write_text(json.dumps({'status':status,'project':project,'dataset':dataset,'jobs':jobs},indent=2,default=str))
    return jobs


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',required=True);p.add_argument('--dataset',default='circle_week_portfolio')
    p.add_argument('--load',action='store_true',help='Create/replace four tables in the selected portfolio dataset')
    p.add_argument('--execute',action='store_true',help='Execute queries with a billing cap; default dry-run only')
    p.add_argument('--benchmark',action='store_true')
    a=p.parse_args();run(a.project,a.dataset,load=a.load,execute=a.execute,benchmark=a.benchmark)
