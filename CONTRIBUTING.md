# Contributing to the project

This document provides information on how to set up your local environment and contribute to the project.

## Prerequisites

To contribute to the project, you need to have the following tools installed on your machine:

* Python 3.8 or more (we highly suggest to install Python using [pyenv](https://github.com/pyenv/pyenv?tab=readme-ov-file#installation) as it allows you to manage multiple Python versions on your machine).
* [Docker](https://docs.docker.com/get-docker/) (optional, if you want to test your Airflow DAGs locally).

For Windows users, we suggest to install Windows Subsystem for Linux (WSL). You can follow the instructions in the [official installation guide](https://learn.microsoft.com/en-us/windows/wsl/install).

## Setting up your local environment

In the following sections, you'll find instructions on how to configure pre-commit, dbt, and Airflow.

Before configuring these tools, create and activate a virtual environment:

```sh
python -m venv .venv
source .venv/bin/activate
```

Then, install the required Python packages declared in the `requirements-dev.txt` file:

```sh
pip install -r requirements-dev.txt
```

### Setting up pre-commit

[pre-commit](https://pre-commit.com/) allows you to run checks (called hooks) before every commit. We usually use this tool to identify (or even fix) simple issues before submission to code review, such as code style issues or syntax errors.

To install the pre-commit hooks declared in the pre-commit configuration file (`.pre-commit-config.yaml`), run:

```sh
pre-commit install
```

After that, before every commit, pre-commit will:

* format and lint your Python code using [Ruff](https://docs.astral.sh/ruff/),
* format and lint your SQL code using [SQLFluff](https://sqlfluff.com/) and [sqlfmt](https://sqlfmt.com/),
* fix issues like trailing whitespaces, end of file not ending in a newline, and more.

Note that if any of the pre-commit hooks fail, the commit will be aborted. You'll have to fix the issues and run `git commit` again.

The Ruff, SQLFluff, and sqlfmt CLI tools are also included in your virtual environment if you want to directly use them in your terminal.

### Setting up dbt

Your virtual environment includes dbt packages and a CLI that you'll use to run dbt commands. You can run `dbt --version` to check if the installation was successful.

dbt uses a [profile](https://docs.getdbt.com/docs/core/connect-data-platform/connection-profiles) to connect to your data warehouse. A profile is a YAML object declared in the `profiles.yml` file located in the `~/.dbt/` directory. Create a `~/.dbt/profiles.yml` file if it doesn't exist, then add and complete the following content with your own information:

```yaml
accor:
  target: personal
  outputs:
    personal:
      account: <Snowflake account> (e.g. "accordata.eu-west-1" for ODP)
      authenticator: externalbrowser
      database: <Snowflake database>
      role: <Snowflake role>
      schema: <Snowflake schema> (e.g. "dbt_jdupont" if your name is Jean Dupont)
      threads: 8
      type: snowflake
      user: <Snowflake user> (e.g. "jean.dupont@accor.com")
      warehouse: <Snowflake warehouse>
```

Note that the `schema` field corresponds to your target schema. Your target schema is the schema that serves as your own workspace in the data warehouse for experimentations. Once your validation is done, you can push your models to the `dev` and `pro` branches and the dbt profile used in the Airflow environment will materialize your models in the appropriate schemas corresponding to your development and production environments in Snowflake.

Once your profile is completed, check that you can access your data warehouse from dbt using the following command:

```sh
dbt debug
```

If everything is fine, then install all dbt packages declared as dependencies by running:

```sh
dbt deps
```

### Setting up Airflow (optional)

Airflow is an open-source data orchestration platform generally used to orchestrate ETL or ELT pipelines. It operates using directed acyclic graphs (DAGs), where each DAG represents a workflow or a series of tasks with dependencies defined within a Python file. A DAG file is essentially a Python script that outlines the structure and sequence of tasks within the workflow. Currently, we exclusively utilize Airflow for orchestrating the transformation phase (via dbt) of ELT pipelines, although Airflow is versatile and capable of orchestrating everything from small Python scripts to complex jobs across multiple external systems.

To run a local Airflow environment, you'll need the [Astro CLI](https://www.astronomer.io/docs/astro/cli/overview) which relies on Docker containers to bring the entire platform to your computer. Follow these steps:

1. Install the Astro CLI by following the [official installation guide](https://www.astronomer.io/docs/astro/cli/install-cli).
2. Start Docker.
3. Run:

   ```sh
   astro dev start
   ```
4. Open the Airflow UI in your web browser at `http://localhost:8080`.

All Airflow DAGs are located in the `dags/` directory (called *DAGs folder*). By default, your local environment scans your DAGs folder for new files every 5 minutes, and parses your DAG files every 30 seconds to reflect the updates made in your DAG files.

## Contributing to the project

In the following sections, you'll get information on how to submit changes on GitLab, and how to contribute to the dbt project and Airflow DAGs.

### Development workflow

Whenever you want to submit changes to the project, you should create a new branch from the `dev` branch, and then submit via a merge request. Each merge request will have to be reviewed and approved by a member of your feature team before merging into the `dev` branch to reduce the chances of introducing errors and bugs.

Once the changes are merged into the `dev` branch, a deployment pipeline will be triggered to deploy the changes to the Airflow development environment on Astronomer. You can then activate and monitor your data pipeline on Astronomer.

After verifying that everything is correct in your development environment, you can trigger a deployment to production by following the same process: open a merge request to merge the `dev` branch into the `pro` branch, wait for approval, merge the branch, then activate and monitor your data pipeline in the Airflow production environment on Astronomer.

Note that the `dev` and `pro` branches are protected, so you cannot push directly to these branches unless you have the necessary permissions.

### Working with dbt

dbt is a data transformation tool that enables data analysts and engineers to easily transform data by creating a cascade of `select` statements, called *models*, and test these models. dbt has many more features such as model contracts, incremental models, model versioning, end more.

The dbt project is located in the `dbt//` folder. You can edit and add new models in the `dbt//models/` folder. Ensure you are in the dbt project folder before issuing dbt commands in your terminal.

For a quick introduction to dbt, we recommend completing the following guides:

* [Quickstart for dbt Core from a manual install (dbt Guide)](https://docs.getdbt.com/guides/manual-install)
* [Refactoring legacy SQL to dbt (dbt Guide)](https://docs.getdbt.com/guides/refactoring-legacy-sql)

### Adding and editing Airflow DAGs

Airflow represents a workflow (or data pipeline) as a directed acyclic graph (or DAG), where each node of the DAG represents a task to run. Currently, we primarily use Airflow with [Cosmos](https://astronomer.github.io/astronomer-cosmos/index.html) to integrate our dbt project with Airflow, allowing us to run and test our models at regular intervals.

All Airflow DAGs in the project are defined in the `dags/` folder. As a best practice, it is recommended to have only one DAG per file.

The most common way of orchestrating a dbt DAG using Cosmos is to use the `DbtDAG` class. You can also orchestrate a subset of a dbt DAG by using the [select and exclude parameters](https://astronomer.github.io/astronomer-cosmos/configuration/selecting-excluding.html). This is useful if you want to create multiple Airflow DAGs to orchestrate different subsets of your dbt DAG with different schedules.

For a quick introduction on how to use Airflow and the Astro CLI, we suggest completing the following learning path:

* [Airflow 101 Learning Path (Astronomer Academy)](https://academy.astronomer.io/path/airflow-101)

You can also check the [Cosmos documentation](https://astronomer.github.io/astronomer-cosmos/index.html) for more information on how to run dbt within Airflow.

## FAQ

<details>
  <summary>What's the difference between a dbt DAG and an Airflow DAG?</summary>

  A dbt DAG is a graph where each node represents a dbt model (which is essentially a `select` statement). The directed links between these nodes indicate dependencies between the models, defining the order in which they should be run and tested. This structure helps you organize and manage your SQL code efficiently.

  On the other hand, an Airflow DAG is a graph where each node represents an arbitrary task, which could be anything from running a Python script to executing a job in an external system (such as a Spark job). The directed links between these tasks specify their execution order, so Airflow knows which tasks need to be completed before others. Additionally, an Airflow DAG can be scheduled to run at regular intervals.

When using the [Cosmos](https://astronomer.github.io/astronomer-cosmos/index.html) integration package, Airflow scans your dbt DAG and automatically creates a corresponding Airflow DAG, so that you don't have to manually define each task in Airflow for running and testing your dbt models.

</details>

<details>
  <summary>How can I change the way an Airflow DAG is scheduled?</summary>

  You can modify the scheduling of an Airflow DAG by updating the `schedule` parameter of your `DAG` object in your DAG file. This parameters accepts a cron expression, a `datetime.timedelta` object, or one of the [cron presets](https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/cron.html).

</details>

<details>
  <summary>How to reference models from another dbt project maintained by another team?</summary>

  To reference models from another dbt project managed by a different team, please contact the [Expo team](mailto:soheil.salmani@consulting-for.accor.com?cc=ismail.mezzour@accor.com). They will assist in configuring your project to enable access to models from the other dbt project.

  Once configured, you'll be able to reference [public models](https://docs.getdbt.com/docs/collaborate/govern/model-access#access-modifiers) from the other dbt project. For example, if your dbt project is set up to access models from another project named `finance`, referencing its `payments` model would look like this:

  ```sql
  select * from {{ ref("finance", "payments") }}
  ```

</details>

<details>
  <summary>What should I do if I want to let other teams to consume my models?</summary>

  To facilitate consumption of your models by other teams, follow these steps:

  1. Add a [model contract](https://docs.getdbt.com/docs/collaborate/govern/model-contracts) to your model. This ensures that you avoid introducing changes that could break the work of other teams.
  2. Declare a [model version](https://docs.getdbt.com/docs/collaborate/govern/model-versions) (e.g., `v1` for a new model). By versioning your models, you can introduce breaking changes in newer versions while allowing other teams to reference the previous versions.
  3. Use [access modifiers](https://docs.getdbt.com/docs/collaborate/govern/model-contracts#related-documentation) to designate your internal models as private and your shareable models as public. This ensures that other dbt projects can only reference your public models, allowing you to modifiy your private models without affecting others' work.

</details>

<details>
  <summary>How to add Snowflake constraints (such as primary and foreign keys) to the tables generated by dbt?</summary>

  Adding Snowflake constraints to tables generated by dbt is facilitated through the `dbt_constraints` dbt package. This package integrates constraints with tests, ensuring that constraints are applied only when tests validate their conditions. This approach is particularly advantageous because Snowflake does not enforce constraints; instead, dbt verifies constraints through tests before applying them.

  To add a primary key constraint to a column, associate the corresponding test in your dbt model:

  ```yml
  - name: orders
    columns:
      - name: order_id
        tests:
          - dbt_constraints.primary_key
  ```

  For declaring a foreign key, you should pass additional information such as the referenced table:

  ```yml
  - name: orders
    columns:
      - name: customer_id
        tests:
          - dbt_constraints.foreign_key:
              pk_table_name: ref('customers')
              pk_column_name: customer_id
  ```

  You can also give a custom name to your constraint by using the `constraint_name` parameter:

  ```yml
  - name: orders
    columns:
      - name: order_id
        tests:
          - dbt_constraints.primary_key:
              constraint_name: <my_constraint_name>
  ```

  Note that constraints are only added when related tests pass, so you will see them after running `dbt test`.

  Check the [documentation](https://hub.getdbt.com/Snowflake-Labs/dbt_constraints/) of the `dbt_constraints` package for more information.

</details>

<details>
  <summary>How to add Snowflake tags to the tables/views generated by dbt?</summary>

  Adding Snowflake tags to tables or views generated by dbt is facilitated through the `snowflake_utils` dbt package. You associate Snowflake tags to a model by setting its `database_tags` [meta property](https://docs.getdbt.com/reference/resource-configs/meta).

  To add a tag for all models in your project, modify your `dbt_project.yml` file as follows:

  ```yml
  models:
    <project_name>:
      +meta:
        database_tags:
          <tag_name>: <tag_value>
  ```

  To add tag to a specific model, use the `config()` macro within the model's SQL file:

  ```sql
  {{
    config(
      meta = {
        "<tag_name>": "tag_value"
      }
    )
  }}

  select * from {{ ref("customers") }}
  ```

  Note that this only allows adding tags for a model; it does not remove tags from a model. However, since dbt drops and recreates tables/views for most materializations, tags are generally updated correctly. If you are using incremental models, though, you will need to fully refresh the model or update the tags manually when changing the associated tags.

  Check the [documentation](https://hub.getdbt.com/Montreal-Analytics/snowflake_utils/) of the `snowflake_utils` package for more information.

</details>

<details>
  <summary>How to create a Snowflake share and add objects to it using dbt?</summary>

  The dbt project contains two macros, `create_share()` and `add_to_share()`, which allow you to create a share and add objects to a share, respectively. These macros take effect only for a production run (i.e. when using the `pro` target).

  To create a share using dbt, update your `dbt_project.yml` file to create a share if it does not exist at the start of a run. Use the `create_share()` macro which takes the name of the share and a list of accounts with which the share will be shared:

  ```yml
  on-run-start:
    - "{{ create_share('my_share', ['orgname.accountname1', 'orgname.accountname2']) }}"
  ```

  To add the object materialized by a dbt model to a share, use a [post-hook](https://docs.getdbt.com/reference/resource-configs/pre-hook-post-hook) and call the `add_to_share()` macro which takes the name of the share as an argument:

  ```sql
  {{
    config(
      post_hook="{{ add_to_share('my_share') }}",
    )
  }}

  select * from {{ ref("customers") }}
  ```

  Note that removing an account from the list of accounts in `create_share()` does not remove it in Snowflake. Similarly, removing the `add_to_share()` call from a model does not remove the associated view or table from the share. These macros only works for the process of adding. Therefore, ensure that you perform the approriate actions in Snowflake after making these type of changes in your dbt project.

  Also, add a [model contract](https://docs.getdbt.com/docs/collaborate/govern/model-contracts) to your shared model to ensure that you avoid introducing changes that could break the work of other teams.

</details>
