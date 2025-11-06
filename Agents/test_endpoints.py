"""Test various API endpoint patterns"""
import requests

task_id = 'f7a7607f6e91286a02914082c6239f6e'
headers = {
    'Authorization': 'Bearer f9dbdbefa5beb4b61912891e4c88f6dd',
    'Content-Type': 'application/json'
}

endpoints = [
    ('https://api.kie.ai/api/v1/jobs/query', 'GET', {'taskId': task_id}),
    ('https://api.kie.ai/api/v1/jobs/query', 'POST', {'taskId': task_id}),
    (f'https://api.kie.ai/api/v1/jobs/task/{task_id}', 'GET', None),
    (f'https://api.kie.ai/api/v1/task/{task_id}', 'GET', None),
    ('https://api.kie.ai/api/v1/getTask', 'GET', {'taskId': task_id}),
    ('https://api.kie.ai/api/v1/getTask', 'POST', {'taskId': task_id}),
]

print("Testing various endpoint patterns...\n")

for url, method, params in endpoints:
    try:
        if method == 'GET':
            if params:
                response = requests.get(url, headers=headers, params=params, timeout=10)
            else:
                response = requests.get(url, headers=headers, timeout=10)
        else:
            response = requests.post(url, headers=headers, json=params, timeout=10)
        
        print(f"{method:4} {url}")
        print(f"     Status: {response.status_code}")
        if response.status_code != 404:
            print(f"     Response: {response.text[:100]}")
        print()
    except Exception as e:
        print(f"{method:4} {url}")
        print(f"     Error: {e}\n")
