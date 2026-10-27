"""Airflow 2.10 DAG. Install in your Airflow environment, not the analytics env."""
import os
import subprocess
from pathlib import Path
from datetime import datetime, timedelta, timezone
from airflow.decorators import dag, task


@dag(dag_id='circle_week_analytics',schedule='0 6 * * 1',start_date=datetime(2026,1,1,tzinfo=timezone.utc),catchup=False,max_active_runs=1,
     default_args={'retries':2,'retry_delay':timedelta(minutes=5)},tags=['retail','portfolio'])
def circle_week():
    @task
    def validate_analyze_publish():
        root=Path(os.environ['CIRCLE_WEEK_REPO']).resolve()
        python=os.environ.get('CIRCLE_WEEK_PYTHON','python')
        subprocess.run([python,'-m','src.pipeline'],cwd=root,check=True,timeout=600)
    validate_analyze_publish()


circle_week()
