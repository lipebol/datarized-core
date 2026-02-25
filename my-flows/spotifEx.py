from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from flows.spotifEx.transform import Transform


with DAG(
    dag_id="spotifEx",
    default_args={"owner": "lipebol", "depends_on_past": True},
    start_date=datetime.now(), catchup=False, description=""
):
    
    task_1=PythonOperator(
        task_id="Processing...",
        python_callable=Transform.data
    )


task_1