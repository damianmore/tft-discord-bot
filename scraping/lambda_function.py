import json
from tft_recent_data_retriever import get_recent_tft_data
def lambda_handler(event, context):
    data = get_recent_tft_data()
    
    return {
        'statusCode': 200,
        'body': json.dumps(data)
    }
