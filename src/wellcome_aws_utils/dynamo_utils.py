# -*- encoding: utf-8 -*-


def _is_capacity_different(x, desired_capacity):
    read_capacity_units = x['ProvisionedThroughput']['ReadCapacityUnits']
    write_capacity_units = x['ProvisionedThroughput']['WriteCapacityUnits']
    return (
        read_capacity_units != desired_capacity
    ) or (
        write_capacity_units != desired_capacity
    )


def change_dynamo_capacity(client, table_name, desired_capacity):
    """
    Given the name of a DynamoDB table and a desired capacity, update the
    read/write capacity of the table and every secondary index.
    """

    response = client.describe_table(TableName=table_name)

    filtered_gsis = filter(
        lambda x: _is_capacity_different(x, desired_capacity),
        response['Table']['GlobalSecondaryIndexes'])

    gsi_updates = list(map(
        lambda x: {
            'Update': {
                'IndexName': x['IndexName'],
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': desired_capacity,
                    'WriteCapacityUnits': desired_capacity
                }
            }
        },
        filtered_gsis
    ))

    table_update = _is_capacity_different(response['Table'], desired_capacity)
    print(f'table_update: {table_update}')

    if gsi_updates and table_update:
        resp = client.update_table(
            TableName=table_name,
            ProvisionedThroughput={
                'ReadCapacityUnits': desired_capacity,
                'WriteCapacityUnits': desired_capacity
            },
            GlobalSecondaryIndexUpdates=gsi_updates
        )
    elif gsi_updates:
        resp = client.update_table(
            TableName=table_name,
            GlobalSecondaryIndexUpdates=gsi_updates
        )
    elif table_update:
        resp = client.update_table(
            TableName=table_name,
            ProvisionedThroughput={
                'ReadCapacityUnits': desired_capacity,
                'WriteCapacityUnits': desired_capacity
            }
        )
    else:
        return

    print(f'DynamoDB response = {resp!r}')
    assert resp['ResponseMetadata']['HTTPStatusCode'] == 200
