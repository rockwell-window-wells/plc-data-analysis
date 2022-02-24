molds = ["Brown", "Purple", "Red", "Pink", "Orange", "Green"]

publicIds = {"Brown": "1NlIuZgMJPMY", "Purple": "cLnbY5lNm6it",
            "Red": "1vWjAHS4F6Cv", "Pink": "JLSdrrXNedLi",
            "Orange": "Sfdr3IrXgZlM", "Green": "wUeYJftWrLEz"}

url = "https://www.stridelinx.com/api/data-export"

operator_headers = {
    "Accept": "application/json",
    "Api-Version": "2",
    "Api-Application": "AzgTnqV556kL",
    "Api-Company": "4795-6677-4436-1317-9986",
    "Content-Type": "application/json",
    "Authorization": "Bearer swGVmsXgEWdwwfYkLEkwIghNGVdgJfUW"
}

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

operator_tags = {"Brown": brown_op_tags, "Purple": purple_op_tags,
                 "Red": red_op_tags, "Pink": pink_op_tags,
                 "Orange": orange_op_tags, "Green": green_op_tags}