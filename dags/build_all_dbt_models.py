import os
from pathlib import Path

from airflow.models.param import Param
from cosmos import DbtDag, ExecutionConfig, ProfileConfig, ProjectConfig, RenderConfig
from cosmos.profiles import GoogleCloudServiceAccountDictProfileMapping
from pendulum import datetime

dbt_project_path = Path("/usr/local/airflow/dbt/primelis/")
dbt_executable = Path("/usr/local/airflow/dbt_venv/bin/dbt")
dbt_target_name = os.getenv("DBT_TARGET_NAME", "dev")
venv_execution_config = ExecutionConfig(
    dbt_executable_path=str(dbt_executable),
)
profile_config = ProfileConfig(
    profile_name="primelis",
    target_name=dbt_target_name,
    profile_mapping=GoogleCloudServiceAccountDictProfileMapping(
        conn_id="bigquery_default",
    ),
)

default_args = {
    "owner": "primelis",
}

task_display_name = "{{ ti.task_display_name }}"
task_id = "{{ ti.task_id }}"
ti_details_url = "{{ conf.get('webserver', 'BASE_URL') }}/dags/{{ ti.dag_id }}/grid?dag_run_id={{ run_id }}&task_id={{ ti.task_id }}&tab=details"
run_id = "{{ run_id }}"
ti_logs_url = "{{ conf.get('webserver', 'BASE_URL') }}/dags/{{ ti.dag_id }}/grid?dag_run_id={{ run_id }}&task_id={{ ti.task_id }}&tab=logs"

dag = DbtDag(
    dag_id="build_all_dbt_models",
    project_config=ProjectConfig(
        dbt_project_path=dbt_project_path,
        dbt_vars={
            "orchestrator": "Airflow",
            "job_name": task_display_name,
            "job_id": task_id,
            "job_url": ti_details_url,
            "job_run_id": run_id,
            "job_run_url": ti_logs_url,
        },
    ),
    render_config=RenderConfig(select=["primelis"]),
    profile_config=profile_config,
    execution_config=venv_execution_config,
    schedule_interval="@daily",
    operator_args={
        "install_deps": True,
        "full_refresh": "{{ params.full_refresh }}",
    },
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["dbt"],
    default_args=default_args,
    params={
        "full_refresh": Param(
            False, type="boolean", description="Full-refresh models?"
        ),
    },
    render_template_as_native_obj=True,
)
