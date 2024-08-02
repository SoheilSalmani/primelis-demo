"""Helpers for authoring DAG in Airflow."""

import time

from airflow.decorators import task
from airflow.models.mappedoperator import MappedOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from airflow.sensors.base import PokeReturnValue
from airflow.utils.task_group import TaskGroup


def run_snowflake_sprocs(
    task_id: str, sproc_list: list[str], snowflake_conn_id="snowflake_default"
) -> MappedOperator:
    """Generate a mapped task group, one task for each stored procedure.

    Args:
        task_id: The ID of the mapped task group.
        sproc_list: The list of stored procedures to run.
        snowflake_conn_id: The ID of the Snowflake connection.

    Returns:
        The generated mapped task group.
    """
    return SQLExecuteQueryOperator.partial(
        task_id=task_id,
        conn_id=snowflake_conn_id,
        autocommit=True,
    ).expand(sql=[f"CALL {sproc}()" for sproc in sproc_list])


def snowflake_dag_manager(
    database: str,
    schema: str,
    task_name: str,
    task_group_name: str,
    connection_id: str = "snowflake_accor_data_plat",
):
    """
    Create a task group with the execution of the root task and catchup of the
    :param database: environment where you are going to launch the task
    :param schema: schema where your task is stored
    :param task_name: task you are going to launch
    :param task_group_name: name of the task group you will have in airflow
    :param connection_id: name of the snowflake connection
    :return: task group containing task launching and sensor that get the end of the dag execution
    """
    with TaskGroup(task_group_name) as snowflake_tasks_group:

        @task
        def launch_task():
            hook = SnowflakeHook(snowflake_conn_id=connection_id)
            hook.run(f"EXECUTE TASK {database}.{schema}.{task_name} ;")
            time.sleep(10)
            get_run_id = f"""
                SELECT
                    RUN_ID
                FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
                SCHEDULED_TIME_RANGE_START=>DATEADD('day',-1,current_timestamp()),
                RESULT_LIMIT => 10,
                TASK_NAME=>'{task_name}'))
                WHERE DATABASE_NAME='{database}' AND SCHEMA_NAME='{schema}'
                ORDER BY SCHEDULED_TIME DESC
                limit 1
            """
            result = hook.get_first(sql=get_run_id)
            run_id = result[0] if result else None
            if run_id is not None:
                return run_id
            else:
                raise ValueError("Run id does not exist")

        @task.sensor(poke_interval=60, timeout=3600, mode="poke")
        def sensor_wait_complete_graph(task_run_id) -> PokeReturnValue:
            hook = SnowflakeHook(snowflake_conn_id=connection_id)
            check_complete = f"""
                SELECT
                    ROOT_TASK_NAME,
                    STATE,
                    FIRST_ERROR_TASK_NAME,
                    FIRST_ERROR_MESSAGE
                FROM SNOWFLAKE.ACCOUNT_USAGE.COMPLETE_TASK_GRAPHS
                WHERE RUN_ID='{task_run_id}'
                ORDER BY QUERY_START_TIME DESC
                LIMIT 1;
            """
            result = hook.get_first(check_complete)
            if result is not None:
                (
                    root_task_name,
                    state,
                    first_error_task_name,
                    first_error_message,
                ) = result
                if state == "FAILED":
                    display_error_message = (
                        f"Error on task {first_error_task_name}: {first_error_message}"
                    )
                    print(display_error_message)
                    raise ValueError(display_error_message)
                else:
                    print(result)
                    return PokeReturnValue(is_done=True)
            else:
                print("Check will be re-run")
                return PokeReturnValue(is_done=False)

        launch_task = launch_task()
        sensor_wait_complete_graph(launch_task)

    return snowflake_tasks_group
