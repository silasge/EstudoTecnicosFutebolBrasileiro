from dbt.cli.main import dbtRunner, dbtRunnerResult

dbt = dbtRunner()
res: dbtRunnerResult = dbt.invoke(["run"])

if res.success:
    print("DBT run completed successfully.")
else:
    print(f"DBT run failed with error: {res.exception}")