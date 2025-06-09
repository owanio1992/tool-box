aws_profiles={
    "nebula": [
            {
                "region": "ap-northeast-1",
                "profile": "<fill me>"
            },
            {
                "region": "eu-west-1",
                "profile": "prod3_ci"
            },
        ],
    "iris": [
            {
                "region": "eu-west-1",
                "profile": "<fill me>"
            },
        ],
}

service_site={
    "<service1>": {
        "<site1>": {
            "prefix": ["aaa", "bbb", "ccc"],
            "instance": [],
            "short_name": "site1",
        },
        "<site2>": {
            "prefix": ["aaa", "bbb", "ccc"],
            "instance": [],
            "short_name": "site2",
        },
        "other": {
            "prefix": [],
            "instance": [],
            "short_name": "o",
        },
    },
    "service2": {
        "other": {
            "prefix": [],
            "instance": [],
            "short_name": "o",
        },
    }
}