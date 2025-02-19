# pylint: disable=no-value-for-parameter,unused-variable, no-member

from dagster import Output, OutputDefinition, composite_solid, lambda_solid, pipeline, solid


@lambda_solid
def return_one() -> int:
    return 1


@lambda_solid
def adder(a: int, b: int) -> int:
    return a + b


@lambda_solid
def multer(a: int, b: int) -> int:
    return a * b


@pipeline
def compute_two():
    one = return_one()
    two = adder(a=one, b=one)


@pipeline
def compute_three():
    one = return_one()
    two = adder(a=one, b=one)
    adder_2 = adder.alias('adder_2')
    three = adder_2(a=two, b=one)


@composite_solid
def add_one(num: int):
    adder(num, return_one())


@composite_solid
def add_one_out(num: int) -> int:
    return adder(num, return_one())


@composite_solid(output_defs=[OutputDefinition(int, 'a_out'), OutputDefinition(int, 'b_out')])
def add_both(a: int, b: int):
    one = return_one()
    a = adder.alias('adder_a')(a, one)
    b = adder.alias('adder_b')(b, one)
    return {'a_out': a, 'b_out': b}


@lambda_solid
def sales_team_path():
    pass


@lambda_solid
def hr_team_path():
    pass


@lambda_solid
def extract(_):
    pass


@lambda_solid
def transform(_):
    pass


@lambda_solid
def load(_):
    pass


@lambda_solid
def analysis(_):
    pass


@pipeline
def complex_pipeline():
    sales_path = sales_team_path()
    sales_data = extract.alias('extract_sales')(sales_path)
    transformed_sales_data = transform.alias('transform_sales')(sales_data)
    load.alias('load_sales')(transformed_sales_data)

    hr_path = hr_team_path()
    hr_data = extract.alias('extract_hr')(hr_path)
    transformed_hr_data = transform.alias('transform_hr')(hr_data)
    loaded_hr_table = load.alias('load_hr')(transformed_hr_data)
    analysis(loaded_hr_table)


@composite_solid
def etl(path: str):
    data = extract(path)
    table = transform(data)
    return load(table)


@pipeline
def composed_pipeline():
    etl.alias('sales_etl')(sales_team_path())
    hr_table = etl.alias('hr_etl')(hr_team_path())
    analysis(hr_table)


@solid(output_defs=[OutputDefinition(int, 'one'), OutputDefinition(int, 'two')])
def return_one_and_two(_):
    yield Output(1, 'one')
    yield Output(2, 'two')


@solid(output_defs=[OutputDefinition(int, 'three'), OutputDefinition(int, 'four')])
def return_three_and_four(_):
    yield Output(3, 'three')
    yield Output(4, 'four')


@pipeline
def multiple_outputs():
    # you can do tuple unpacking
    one, two = return_one_and_two()
    m = multer(one, two)

    # or key off the result tuple
    results = return_three_and_four()
    a = adder(results.three, results.four)

    add_both(m, a)
