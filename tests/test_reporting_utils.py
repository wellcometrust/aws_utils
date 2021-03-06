import json
import boto3
from moto import mock_s3, mock_dynamodb2
from unittest.mock import patch
from wellcome_aws_utils.reporting_utils import process_messages


def create_sns_message(id):
    return {
        "Records": [
            {
                "Sns": {
                    "Message": (f'{{"id":"{id}","version":1}}'),
                    "MessageAttributes": {},
                    "MessageId": "0cf7d798-64c8-45a7-a7bf-a9ebc94d1108",
                    "Type": "Notification",
                }
            }
        ]
    }


def given_s3_has(s3_client, bucket, path, data):
    s3_client.put_object(
        ACL="public-read",
        Bucket=bucket,
        Key=path,
        Body=data,
        CacheControl="max-age=0",
        ContentType="application/json",
    )


def identity_transform(record):
    return record


class TestReportingUtils(object):
    @mock_s3
    @mock_dynamodb2
    def test_saves_record_in_es(self):
        with patch('elasticsearch.Elasticsearch') as MockElasticsearch:
            id = "V0000001"
            mock_elasticsearch_client = MockElasticsearch()
            elasticsearch_index = "index"
            hybrid_data = '{"foo": "bar"}'
            path = "00/V0000001/0.json"
            bucket = "bukkit"

            s3_client = boto3.client('s3')
            s3_client.create_bucket(Bucket=bucket)
            given_s3_has(
                s3_client=s3_client,
                bucket=bucket,
                path=path,
                data=json.dumps(hybrid_data)
            )

            table_name = 'vhs'
            dynamodb = boto3.resource('dynamodb')
            dynamodb.create_table(
                TableName=table_name,
                AttributeDefinitions=[{
                    "AttributeName": "id",
                    "AttributeType": "S"
                }],
                KeySchema=[{
                    "AttributeName": "id",
                    "KeyType": "HASH"
                }],
                ProvisionedThroughput={
                    "ReadCapacityUnits": 1,
                    "WriteCapacityUnits": 1,
                }
            )
            dynamodb.Table(table_name).put_item(
                Item={
                    "id": id,
                    "version": 1,
                    "payload": {"namespace": bucket, "path": path}
                }
            )

            event = create_sns_message(id)

            process_messages(
                event,
                identity_transform,
                elasticsearch_index,
                table_name,
                dynamodb=dynamodb,
                s3_client=s3_client,
                es_client=mock_elasticsearch_client
            )

            mock_elasticsearch_client.index.assert_called_once_with(
                body=json.dumps(hybrid_data),
                doc_type="_doc",
                id=id,
                index=elasticsearch_index
            )
