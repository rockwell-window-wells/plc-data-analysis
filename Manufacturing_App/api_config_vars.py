import base64
import json
import requests
import yaml

molds = ["Brown", "Purple", "Red", "Pink", "Orange", "Green"]

publicIds = {"Brown": "1NlIuZgMJPMY", "Purple": "cLnbY5lNm6it",
            "Red": "1vWjAHS4F6Cv", "Pink": "JLSdrrXNedLi",
            "Orange": "Sfdr3IrXgZlM", "Green": "wUeYJftWrLEz"}

url = "https://www.stridelinx.com/api/data-export"

CONFIG_FILE = 'config_vars.yaml'

def get_config_vars(config_file:str):
    with open(config_file, 'r') as file:
        config_data = yaml.safe_load(file)
        
        user = config_data['user']
        password = config_data['password']
        api_application = config_data['api_application']
        api_company = config_data['api_company']
    
    return user, password, api_application, api_company

def request_bearer_token():
    # Generate a current bearer token based on the login credentials specified   
    # with open(CONFIG_FILE, 'r') as file:
    #     config_data = yaml.safe_load(file)
        
    #     user = config_data['user']
    #     password = config_data['password']
    
    user, password, api_application, _ = get_config_vars(CONFIG_FILE)

    credentials = user + "::" + password
    credentials_bytes = credentials.encode()
    base64auth = base64.b64encode(credentials_bytes)
    base64_message = base64auth.decode()
    base64_message = "Basic " + base64_message

    headers = {
        'Api-Version': '2',
        'Api-Application': api_application,
        # Already added when you pass json= but not when you pass data=
        'Content-Type': 'application/json',
        'Authorization': base64_message,
    }

    params = {
        'fields': 'secretId',
    }

    json_data = {
        'expiresIn': 3600,
    }

    response = requests.post('https://portal.ixon.cloud:443/api/access-tokens?fields=secretId', headers=headers, params=params, json=json_data)

    data = json.loads(response.text)

    bearer_string = data["data"]["secretId"]

    bearer_string = "Bearer " + bearer_string
    
    return bearer_string

def request_operator_headers():
    bearer_string = request_bearer_token()
    
    user, password, api_application, api_company = get_config_vars(CONFIG_FILE)
    
    operator_headers = {
        "Accept": "application/json",
        "Api-Version": "2",
        "Api-Application": api_application,
        "Api-Company": api_company,
        "Content-Type": "application/json",
        "Authorization": bearer_string
    }
    
    return operator_headers

brown_op_tags = [
    {
        "queries": [
            {
                "ref": "Layup Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 95
    },
    {
        "queries": [
            {
                "ref": "Close Time",
                "factor": "0.0166667",
                "decimals": 2,
                "offset": 0
            }
        ],
        "id": 96,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Resin Time",
                "factor": "0.0166667",
                "offset": 0,
                "decimals": 2
            }
        ],
        "id": 98,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Cycle Time",
                "factor": "0.0166667",
                "decimals": 2,
                "offset": 0
            }
        ],
        "id": 12,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Lead",
                "offset": 0,
                "factor": "1.0000000",
                "decimals": 0
            }
        ],
        "id": 99,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Assistant 1",
                "offset": 0,
                "decimals": 0,
                "factor": "1.0000000"
            }
        ],
        "id": 100,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Assistant 2",
                "offset": 0,
                "decimals": 0,
                "factor": "1.0000000"
            }
        ],
        "id": 101,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "offset": 0,
                "factor": "1.0000000",
                "decimals": 0,
                "ref": "Assistant 3"
            }
        ],
        "id": 102,
        "preAggr": "raw"
    }
]

brown_bag_tags = [
    {
        "queries": [
            {
                "ref": "Layup Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 95
    },
    {
        "queries": [
            {
                "ref": "Close Time",
                "factor": "0.0166667",
                "decimals": 2,
                "offset": 0
            }
        ],
        "id": 96,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Resin Time",
                "factor": "0.0166667",
                "offset": 0,
                "decimals": 2
            }
        ],
        "id": 98,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Cycle Time",
                "factor": "0.0166667",
                "decimals": 2,
                "offset": 0
            }
        ],
        "id": 12,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Bag",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 105
    },
    {
        "queries": [
            {
                "ref": "Bag Days",
                "factor": "1.0000000",
                "decimals": 0,
                "offset": 0
            }
        ],
        "id": 108,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Bag Cycles",
                "factor": "1.0000000",
                "offset": 0,
                "decimals": 0
            }
        ],
        "id": 107,
        "preAggr": "raw"
    }
]


brown_all_tags = [
    {
        "queries": [
            {
                "ref": "Layup Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 95
    },
    {
        "queries": [
            {
                "ref": "Close Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 96
    },
    {
        "queries": [
            {
                "ref": "Resin Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 98
    },
    {
        "queries": [
            {
                "ref": "Cycle Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 12
    },
    {
        "queries": [
            {
                "ref": "Leak Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 94
    },
    {
        "queries": [
            {
                "ref": "Leak Count",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 93
    },
    {
        "queries": [
            {
                "ref": "Parts Count",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 70
    },
    {
        "queries": [
            {
                "ref": "Weekly Count",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 68
    },
    {
        "queries": [
            {
                "ref": "Monthly Count",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 66
    },
    {
        "queries": [
            {
                "ref": "Trash Count",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 92
    },
    {
        "queries": [
            {
                "ref": "Lead",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 99
    },
    {
        "queries": [
            {
                "ref": "Assistant 1",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 100
    },
    {
        "queries": [
            {
                "ref": "Assistant 2",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 101
    },
    {
        "queries": [
            {
                "ref": "Assistant 3",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 102
    },
    {
        "queries": [
            {
                "ref": "Bag",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 105
    },
    {
        "queries": [
            {
                "ref": "Bag Days",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 108
    },
    {
        "queries": [
            {
                "ref": "Bag Cycles",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 107
    },
]

purple_op_tags = [
    {
        "queries": [
            {
                "ref": "Layup Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 9
    },
    {
        "queries": [
            {
                "ref": "Close Time",
                "factor": "0.0166667",
                "decimals": 2,
                "offset": 0
            }
        ],
        "id": 10,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Resin Time",
                "factor": "0.0166667",
                "offset": 0,
                "decimals": 2
            }
        ],
        "id": 6,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Cycle Time",
                "factor": "0.0166667",
                "decimals": 2,
                "offset": 0
            }
        ],
        "id": 2,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Lead",
                "offset": 0,
                "factor": "1.0000000",
                "decimals": 0
            }
        ],
        "id": 19,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Assistant 1",
                "offset": 0,
                "decimals": 0,
                "factor": "1.0000000"
            }
        ],
        "id": 20,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Assistant 2",
                "offset": 0,
                "decimals": 0,
                "factor": "1.0000000"
            }
        ],
        "id": 21,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "offset": 0,
                "factor": "1.0000000",
                "decimals": 0,
                "ref": "Assistant 3"
            }
        ],
        "id": 22,
        "preAggr": "raw"
    }
]

purple_bag_tags = [
    {
        "queries": [
            {
                "ref": "Layup Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 9
    },
    {
        "queries": [
            {
                "ref": "Close Time",
                "factor": "0.0166667",
                "decimals": 2,
                "offset": 0
            }
        ],
        "id": 10,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Resin Time",
                "factor": "0.0166667",
                "offset": 0,
                "decimals": 2
            }
        ],
        "id": 6,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Cycle Time",
                "factor": "0.0166667",
                "decimals": 2,
                "offset": 0
            }
        ],
        "id": 2,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Bag",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 23
    },
    {
        "queries": [
            {
                "ref": "Bag Days",
                "factor": "1.0000000",
                "decimals": 0,
                "offset": 0
            }
        ],
        "id": 25,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Bag Cycles",
                "factor": "1.0000000",
                "offset": 0,
                "decimals": 0
            }
        ],
        "id": 24,
        "preAggr": "raw"
    }
]

purple_all_tags = [
    {
        "queries": [
            {
                "ref": "Layup Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 9
    },
    {
        "queries": [
            {
                "ref": "Close Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 10
    },
    {
        "queries": [
            {
                "ref": "Resin Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 6
    },
    {
        "queries": [
            {
                "ref": "Cycle Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 2
    },
    {
        "queries": [
            {
                "ref": "Leak Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 17
    },
    {
        "queries": [
            {
                "ref": "Leak Count",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 16
    },
    {
        "queries": [
            {
                "ref": "Parts Count",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 3
    },
    {
        "queries": [
            {
                "ref": "Weekly Count",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 12
    },
    {
        "queries": [
            {
                "ref": "Monthly Count",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 15
    },
    {
        "queries": [
            {
                "ref": "Trash Count",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 18
    },
    {
        "queries": [
            {
                "ref": "Lead",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 19
    },
    {
        "queries": [
            {
                "ref": "Assistant 1",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 20
    },
    {
        "queries": [
            {
                "ref": "Assistant 2",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 21
    },
    {
        "queries": [
            {
                "ref": "Assistant 3",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 22
    },
    {
        "queries": [
            {
                "ref": "Bag",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 23
    },
    {
        "queries": [
            {
                "ref": "Bag Days",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 25
    },
    {
        "queries": [
            {
                "ref": "Bag Cycles",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 24
    },
]

red_op_tags = [
    {
        "queries": [
            {
                "ref": "Layup Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 6
    },
    {
        "queries": [
            {
                "ref": "Close Time",
                "factor": "0.0166667",
                "decimals": 2,
                "offset": 0
            }
        ],
        "id": 7,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Resin Time",
                "factor": "0.0166667",
                "offset": 0,
                "decimals": 2
            }
        ],
        "id": 9,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Cycle Time",
                "factor": "0.0166667",
                "decimals": 2,
                "offset": 0
            }
        ],
        "id": 2,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Lead",
                "offset": 0,
                "factor": "1.0000000",
                "decimals": 0
            }
        ],
        "id": 17,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Assistant 1",
                "offset": 0,
                "decimals": 0,
                "factor": "1.0000000"
            }
        ],
        "id": 18,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Assistant 2",
                "offset": 0,
                "decimals": 0,
                "factor": "1.0000000"
            }
        ],
        "id": 19,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "offset": 0,
                "factor": "1.0000000",
                "decimals": 0,
                "ref": "Assistant 3"
            }
        ],
        "id": 20,
        "preAggr": "raw"
    }
]

red_bag_tags = [
    {
        "queries": [
            {
                "ref": "Layup Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 6
    },
    {
        "queries": [
            {
                "ref": "Close Time",
                "factor": "0.0166667",
                "decimals": 2,
                "offset": 0
            }
        ],
        "id": 7,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Resin Time",
                "factor": "0.0166667",
                "offset": 0,
                "decimals": 2
            }
        ],
        "id": 9,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Cycle Time",
                "factor": "0.0166667",
                "decimals": 2,
                "offset": 0
            }
        ],
        "id": 2,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Bag",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 21
    },
    {
        "queries": [
            {
                "ref": "Bag Days",
                "factor": "1.0000000",
                "decimals": 0,
                "offset": 0
            }
        ],
        "id": 25,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Bag Cycles",
                "factor": "1.0000000",
                "offset": 0,
                "decimals": 0
            }
        ],
        "id": 28,
        "preAggr": "raw"
    }
]

red_all_tags = [
    {
        "queries": [
            {
                "ref": "Layup Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 6
    },
    {
        "queries": [
            {
                "ref": "Close Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 7
    },
    {
        "queries": [
            {
                "ref": "Resin Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 9
    },
    {
        "queries": [
            {
                "ref": "Cycle Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 2
    },
    {
        "queries": [
            {
                "ref": "Leak Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 16
    },
    {
        "queries": [
            {
                "ref": "Leak Count",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 15
    },
    {
        "queries": [
            {
                "ref": "Parts Count",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 3
    },
    {
        "queries": [
            {
                "ref": "Weekly Count",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 11
    },
    {
        "queries": [
            {
                "ref": "Monthly Count",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 13
    },
    {
        "queries": [
            {
                "ref": "Trash Count",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 4
    },
    {
        "queries": [
            {
                "ref": "Lead",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 17
    },
    {
        "queries": [
            {
                "ref": "Assistant 1",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 18
    },
    {
        "queries": [
            {
                "ref": "Assistant 2",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 19
    },
    {
        "queries": [
            {
                "ref": "Assistant 3",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 20
    },
    {
        "queries": [
            {
                "ref": "Bag",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 21
    },
    {
        "queries": [
            {
                "ref": "Bag Days",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 25
    },
    {
        "queries": [
            {
                "ref": "Bag Cycles",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 28
    },
]

pink_op_tags = [
    {
        "queries": [
            {
                "ref": "Layup Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 12
    },
    {
        "queries": [
            {
                "ref": "Close Time",
                "factor": "0.0166667",
                "decimals": 2,
                "offset": 0
            }
        ],
        "id": 4,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Resin Time",
                "factor": "0.0166667",
                "offset": 0,
                "decimals": 2
            }
        ],
        "id": 5,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Cycle Time",
                "factor": "0.0166667",
                "decimals": 2,
                "offset": 0
            }
        ],
        "id": 2,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Lead",
                "offset": 0,
                "factor": "1.0000000",
                "decimals": 0
            }
        ],
        "id": 17,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Assistant 1",
                "offset": 0,
                "decimals": 0,
                "factor": "1.0000000"
            }
        ],
        "id": 18,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Assistant 2",
                "offset": 0,
                "decimals": 0,
                "factor": "1.0000000"
            }
        ],
        "id": 19,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "offset": 0,
                "factor": "1.0000000",
                "decimals": 0,
                "ref": "Assistant 3"
            }
        ],
        "id": 20,
        "preAggr": "raw"
    }
]

pink_bag_tags = [
    {
        "queries": [
            {
                "ref": "Layup Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 12
    },
    {
        "queries": [
            {
                "ref": "Close Time",
                "factor": "0.0166667",
                "decimals": 2,
                "offset": 0
            }
        ],
        "id": 4,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Resin Time",
                "factor": "0.0166667",
                "offset": 0,
                "decimals": 2
            }
        ],
        "id": 5,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Cycle Time",
                "factor": "0.0166667",
                "decimals": 2,
                "offset": 0
            }
        ],
        "id": 2,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Bag",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 21
    },
    {
        "queries": [
            {
                "ref": "Bag Days",
                "factor": "1.0000000",
                "decimals": 0,
                "offset": 0
            }
        ],
        "id": 23,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Bag Cycles",
                "factor": "1.0000000",
                "offset": 0,
                "decimals": 0
            }
        ],
        "id": 22,
        "preAggr": "raw"
    }
]

pink_all_tags = [
    {
        "queries": [
            {
                "ref": "Layup Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 12
    },
    {
        "queries": [
            {
                "ref": "Close Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 4
    },
    {
        "queries": [
            {
                "ref": "Resin Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 5
    },
    {
        "queries": [
            {
                "ref": "Cycle Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 2
    },
    {
        "queries": [
            {
                "ref": "Leak Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 15
    },
    {
        "queries": [
            {
                "ref": "Leak Count",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 14
    },
    {
        "queries": [
            {
                "ref": "Parts Count",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 11
    },
    {
        "queries": [
            {
                "ref": "Weekly Count",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 9
    },
    {
        "queries": [
            {
                "ref": "Monthly Count",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 13
    },
    {
        "queries": [
            {
                "ref": "Trash Count",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 16
    },
    {
        "queries": [
            {
                "ref": "Lead",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 17
    },
    {
        "queries": [
            {
                "ref": "Assistant 1",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 18
    },
    {
        "queries": [
            {
                "ref": "Assistant 2",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 19
    },
    {
        "queries": [
            {
                "ref": "Assistant 3",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 20
    },
    {
        "queries": [
            {
                "ref": "Bag",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 21
    },
    {
        "queries": [
            {
                "ref": "Bag Days",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 23
    },
    {
        "queries": [
            {
                "ref": "Bag Cycles",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 22
    },
]

orange_op_tags = [
    {
        "queries": [
            {
                "ref": "Layup Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 12
    },
    {
        "queries": [
            {
                "ref": "Close Time",
                "factor": "0.0166667",
                "decimals": 2,
                "offset": 0
            }
        ],
        "id": 4,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Resin Time",
                "factor": "0.0166667",
                "offset": 0,
                "decimals": 2
            }
        ],
        "id": 5,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Cycle Time",
                "factor": "0.0166667",
                "decimals": 2,
                "offset": 0
            }
        ],
        "id": 2,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Lead",
                "offset": 0,
                "factor": "1.0000000",
                "decimals": 0
            }
        ],
        "id": 17,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Assistant 1",
                "offset": 0,
                "decimals": 0,
                "factor": "1.0000000"
            }
        ],
        "id": 18,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Assistant 2",
                "offset": 0,
                "decimals": 0,
                "factor": "1.0000000"
            }
        ],
        "id": 19,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "offset": 0,
                "factor": "1.0000000",
                "decimals": 0,
                "ref": "Assistant 3"
            }
        ],
        "id": 20,
        "preAggr": "raw"
    }
]

orange_bag_tags = [
    {
        "queries": [
            {
                "ref": "Layup Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 12
    },
    {
        "queries": [
            {
                "ref": "Close Time",
                "factor": "0.0166667",
                "decimals": 2,
                "offset": 0
            }
        ],
        "id": 4,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Resin Time",
                "factor": "0.0166667",
                "offset": 0,
                "decimals": 2
            }
        ],
        "id": 5,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Cycle Time",
                "factor": "0.0166667",
                "decimals": 2,
                "offset": 0
            }
        ],
        "id": 2,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Bag",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 21
    },
    {
        "queries": [
            {
                "ref": "Bag Days",
                "factor": "1.0000000",
                "decimals": 0,
                "offset": 0
            }
        ],
        "id": 23,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Bag Cycles",
                "factor": "1.0000000",
                "offset": 0,
                "decimals": 0
            }
        ],
        "id": 22,
        "preAggr": "raw"
    }
]

orange_all_tags = [
    {
        "queries": [
            {
                "ref": "Layup Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 12
    },
    {
        "queries": [
            {
                "ref": "Close Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 4
    },
    {
        "queries": [
            {
                "ref": "Resin Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 5
    },
    {
        "queries": [
            {
                "ref": "Cycle Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 2
    },
    {
        "queries": [
            {
                "ref": "Leak Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 15
    },
    {
        "queries": [
            {
                "ref": "Leak Count",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 14
    },
    {
        "queries": [
            {
                "ref": "Parts Count",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 11
    },
    {
        "queries": [
            {
                "ref": "Weekly Count",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 9
    },
    {
        "queries": [
            {
                "ref": "Monthly Count",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 13
    },
    {
        "queries": [
            {
                "ref": "Trash Count",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 8
    },
    {
        "queries": [
            {
                "ref": "Lead",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 17
    },
    {
        "queries": [
            {
                "ref": "Assistant 1",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 18
    },
    {
        "queries": [
            {
                "ref": "Assistant 2",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 19
    },
    {
        "queries": [
            {
                "ref": "Assistant 3",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 20
    },
    {
        "queries": [
            {
                "ref": "Bag",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 21
    },
    {
        "queries": [
            {
                "ref": "Bag Days",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 23
    },
    {
        "queries": [
            {
                "ref": "Bag Cycles",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 22
    },
]

green_op_tags = [
    {
        "queries": [
            {
                "ref": "Layup Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 12
    },
    {
        "queries": [
            {
                "ref": "Close Time",
                "factor": "0.0166667",
                "decimals": 2,
                "offset": 0
            }
        ],
        "id": 4,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Resin Time",
                "factor": "0.0166667",
                "offset": 0,
                "decimals": 2
            }
        ],
        "id": 5,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Cycle Time",
                "factor": "0.0166667",
                "decimals": 2,
                "offset": 0
            }
        ],
        "id": 2,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Lead",
                "offset": 0,
                "factor": "1.0000000",
                "decimals": 0
            }
        ],
        "id": 25,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Assistant 1",
                "offset": 0,
                "decimals": 0,
                "factor": "1.0000000"
            }
        ],
        "id": 26,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Assistant 2",
                "offset": 0,
                "decimals": 0,
                "factor": "1.0000000"
            }
        ],
        "id": 27,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "offset": 0,
                "factor": "1.0000000",
                "decimals": 0,
                "ref": "Assistant 3"
            }
        ],
        "id": 28,
        "preAggr": "raw"
    }
]

green_bag_tags = [
    {
        "queries": [
            {
                "ref": "Layup Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 12
    },
    {
        "queries": [
            {
                "ref": "Close Time",
                "factor": "0.0166667",
                "decimals": 2,
                "offset": 0
            }
        ],
        "id": 4,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Resin Time",
                "factor": "0.0166667",
                "offset": 0,
                "decimals": 2
            }
        ],
        "id": 5,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Cycle Time",
                "factor": "0.0166667",
                "decimals": 2,
                "offset": 0
            }
        ],
        "id": 2,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Bag",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 29
    },
    {
        "queries": [
            {
                "ref": "Bag Days",
                "factor": "1.0000000",
                "decimals": 0,
                "offset": 0
            }
        ],
        "id": 31,
        "preAggr": "raw"
    },
    {
        "queries": [
            {
                "ref": "Bag Cycles",
                "factor": "1.0000000",
                "offset": 0,
                "decimals": 0
            }
        ],
        "id": 30,
        "preAggr": "raw"
    }
]

green_all_tags = [
    {
        "queries": [
            {
                "ref": "Layup Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 12
    },
    {
        "queries": [
            {
                "ref": "Close Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 4
    },
    {
        "queries": [
            {
                "ref": "Resin Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 5
    },
    {
        "queries": [
            {
                "ref": "Cycle Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 2
    },
    {
        "queries": [
            {
                "ref": "Leak Time",
                "decimals": 2,
                "factor": "0.0166667",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 20
    },
    {
        "queries": [
            {
                "ref": "Leak Count",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 21
    },
    {
        "queries": [
            {
                "ref": "Parts Count",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 11
    },
    {
        "queries": [
            {
                "ref": "Weekly Count",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 9
    },
    {
        "queries": [
            {
                "ref": "Monthly Count",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 13
    },
    {
        "queries": [
            {
                "ref": "Trash Count",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 8
    },
    {
        "queries": [
            {
                "ref": "Lead",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 25
    },
    {
        "queries": [
            {
                "ref": "Assistant 1",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 26
    },
    {
        "queries": [
            {
                "ref": "Assistant 2",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 27
    },
    {
        "queries": [
            {
                "ref": "Assistant 3",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 28
    },
    {
        "queries": [
            {
                "ref": "Bag",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 29
    },
    {
        "queries": [
            {
                "ref": "Bag Days",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 31
    },
    {
        "queries": [
            {
                "ref": "Bag Cycles",
                "decimals": 0,
                "factor": "1.0000000",
                "offset": 0
            }
        ],
        "preAggr": "raw",
        "id": 30
    },
]


operator_tags = {"Brown": brown_op_tags, "Purple": purple_op_tags,
                 "Red": red_op_tags, "Pink": pink_op_tags,
                 "Orange": orange_op_tags, "Green": green_op_tags}

bag_tags = {"Brown": brown_bag_tags, "Purple": purple_bag_tags,
                 "Red": red_bag_tags, "Pink": pink_bag_tags,
                 "Orange": orange_bag_tags, "Green": green_bag_tags}

all_tags = {"Brown": brown_all_tags, "Purple": purple_all_tags,
                 "Red": red_all_tags, "Pink": pink_all_tags,
                 "Orange": orange_all_tags, "Green": green_all_tags}