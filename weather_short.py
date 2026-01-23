# Python3 샘플 코드 #


import requests

url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
params = {
    "serviceKey": "7971bf2e2fe86294900d2dbb67d5406dad1297a2962cef98a6577eed8d69e3ac",
    "pageNo": "1",
    "numOfRows": "1000",
    "dataType": "JSON",
    "base_date": "20260123",
    "base_time": "0500",
    "nx": "55",
    "ny": "127",
}

response = requests.get(url, params=params)
print(response.content)
