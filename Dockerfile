FROM quay.io/astronomer/astro-runtime:11.7.0

# Install dbt in a virtual environment
RUN python3 -m venv /usr/local/airflow/dbt_venv \
    && /bin/bash -c "source /usr/local/airflow/dbt_venv/bin/activate && pip install --no-cache-dir dbt-bigquery==1.8.2 && deactivate"
