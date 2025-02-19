import os

from pyspark.sql import Row, DataFrame as SparkDF

from dagster_pyspark import spark_session_from_config

from dagster.utils.temp_file import get_temp_dir

from dagster import InputDefinition

from lakehouse import PySparkMemLakehouse, input_table, pyspark_table

from .common import LocalOnDiskSparkCsvLakehouse, execute_spark_lakehouse_build

# Note typehints in lakehouse purely optional and behave as vanilla typehints


@pyspark_table(other_input_defs=[InputDefinition('num', int)])
def TableOne(context, num) -> SparkDF:
    return context.resources.spark.createDataFrame([Row(num=num)])


@pyspark_table
def TableTwo(context) -> SparkDF:
    return context.resources.spark.createDataFrame([Row(num=2)])


@pyspark_table(
    input_tables=[input_table('table_one', TableOne), input_table('table_two', TableTwo)]
)
def TableThree(_, table_one: SparkDF, table_two: SparkDF) -> SparkDF:
    return table_one.union(table_two)


def test_execute_in_mem_lakehouse():
    lakehouse = PySparkMemLakehouse()
    pipeline_result = execute_spark_lakehouse_build(
        tables=[TableOne, TableTwo, TableThree],
        lakehouse=lakehouse,
        environment_dict={'solids': {'TableOne': {'inputs': {'num': {'value': 1}}}}},
    )

    assert pipeline_result.success

    assert lakehouse.collected_tables == {
        'TableOne': [Row(num=1)],
        'TableTwo': [Row(num=2)],
        'TableThree': [Row(num=1), Row(num=2)],
    }


def test_execute_file_system_lakehouse():
    with get_temp_dir() as temp_dir:
        pipeline_result = execute_spark_lakehouse_build(
            tables=[TableOne, TableTwo, TableThree],
            lakehouse=LocalOnDiskSparkCsvLakehouse(temp_dir),
            environment_dict={'solids': {'TableOne': {'inputs': {'num': {'value': 1}}}}},
        )

        assert pipeline_result.success

        def get_table(name):
            spark = spark_session_from_config()
            return spark.read.csv(
                os.path.join(temp_dir, name), header=True, inferSchema=True
            ).collect()

        assert get_table('TableOne') == [Row(num=1)]
        assert get_table('TableTwo') == [Row(num=2)]
        assert set(get_table('TableThree')) == set([Row(num=1), Row(num=2)])
