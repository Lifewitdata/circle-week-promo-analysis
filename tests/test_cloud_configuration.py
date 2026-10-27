"""Mock SDK configuration tests, not authenticated GCP execution evidence."""
import json
import shutil
import sys
import types
from pathlib import Path
import pytest
from src import bigquery_runner as runner
from src.pipeline import ROOT


def fake_sdk(monkeypatch,*,bad_effect=False):
    calls=[]
    class Config:
        def __init__(self,**kwargs):self.__dict__.update(kwargs)
    class Field:
        def __init__(self,*args,**kwargs):self.args=args;self.__dict__.update(kwargs)
    class Dataset:
        def __init__(self,name):self.name=name
    class Job:
        job_id='mock-job-not-live';output_rows=12480;total_bytes_processed=1000;total_bytes_billed=10485760;slot_millis=5
        def __init__(self,rows=None):self.rows=rows or []
        def result(self):return self.rows
    class Client:
        def __init__(self,**kwargs):calls.append(('client',kwargs))
        def create_dataset(self,ds,**kwargs):calls.append(('dataset',ds,kwargs))
        def load_table_from_file(self,file,table,**kwargs):
            calls.append(('load',table,kwargs['job_config']));return Job()
        def query(self,sql,job_config):
            calls.append(('query',sql,job_config))
            if 'AS effect_usd_per_store_week' in sql:
                return Job([{'effect_usd_per_store_week':999 if bad_effect else 2585.5542891483524,'store_growth_gap_pp':14.886089950023866}])
            return Job([{'mock':True}])
    sdk=types.ModuleType('google.cloud.bigquery')
    for name,value in {'Client':Client,'Dataset':Dataset,'SchemaField':Field,'LoadJobConfig':Config,
                       'QueryJobConfig':Config,'TimePartitioning':Config,
                       'TimePartitioningType':types.SimpleNamespace(DAY='DAY'),
                       'SourceFormat':types.SimpleNamespace(CSV='CSV')}.items():
        setattr(sdk,name,value)
    cloud=types.ModuleType('google.cloud');cloud.bigquery=sdk
    google=types.ModuleType('google');google.cloud=cloud
    monkeypatch.setitem(sys.modules,'google',google);monkeypatch.setitem(sys.modules,'google.cloud',cloud)
    monkeypatch.setitem(sys.modules,'google.cloud.bigquery',sdk)
    return calls


def root_fixture(tmp_path,monkeypatch):
    for name in ['data','sql']:
        shutil.copytree(ROOT/name,tmp_path/name)
    shutil.copy2(ROOT/'config.json',tmp_path/'config.json')
    (tmp_path/'reports').mkdir()
    (tmp_path/'reports/summary.json').write_text(json.dumps({'effect_usd_per_store_week':2585.5542891483524,'store_growth_gap_pp':14.886089950023866}))
    monkeypatch.setattr(runner,'ROOT',tmp_path)


def test_partitioned_load_billing_cap_and_reconciliation(tmp_path,monkeypatch):
    root_fixture(tmp_path,monkeypatch)
    calls=fake_sdk(monkeypatch)
    jobs=runner.run('valid-project','portfolio',load=True,execute=True,benchmark=True)
    loads=[c for c in calls if c[0]=='load']
    assert len(loads)==4
    fact=next(c[2] for c in loads if c[1].endswith('.sales_weekly'))
    assert fact.time_partitioning.field=='week_start_date'
    assert fact.clustering_fields==['category_id','store_id']
    assert fact.write_disposition=='WRITE_TRUNCATE'
    queries=[c[2] for c in calls if c[0]=='query']
    assert sum(getattr(c,'dry_run',False) for c in queries)==12
    for c in queries:
        if not getattr(c,'dry_run',False):assert c.maximum_bytes_billed==1000000000 and c.use_query_cache is False
    assert next(j for j in jobs if j.get('name')=='primary_effect')['local_reconciled']
    evidence=json.loads((tmp_path/'reports/live_bigquery/execution_evidence.json').read_text())
    assert evidence['status']=='success'


def test_dry_run_does_not_execute_or_load(tmp_path,monkeypatch):
    root_fixture(tmp_path,monkeypatch)
    calls=fake_sdk(monkeypatch)
    jobs=runner.run('valid-project','portfolio')
    assert not any(c[0]=='load' for c in calls)
    assert all(not j['executed'] for j in jobs)
    assert all(c[2].dry_run for c in calls if c[0]=='query')


def test_cloud_mismatch_fails_and_records_failure(tmp_path,monkeypatch):
    root_fixture(tmp_path,monkeypatch)
    fake_sdk(monkeypatch,bad_effect=True)
    with pytest.raises(AssertionError,match='reconciliation'):
        runner.run('valid-project','portfolio',execute=True)
    evidence=json.loads((tmp_path/'reports/live_bigquery/execution_evidence.json').read_text())
    assert evidence['status']=='failed'
