import json
import requests

from ..inspection_analysis.tokens import token

def rolodex_load(entry_type, links=[], filters=[], ids=[], tags={}, limit=100000):
    url = "https://rolodex.cloud.geckorobotics.com/api/v2/entries/load"
    headers = {
        "Accept": "application/json",
        "Authorization": "Bearer "+token,
        "Content-Type": "application/json",
    }

    post_body = {
        "type": entry_type,
        "links": links,
        "filters": filters,
        "ids": ids,
        "tags": tags,
        "limit": limit,
    }

    req = requests.post(url, data=json.dumps(post_body), headers=headers)
    data = req.json()
    
    return data