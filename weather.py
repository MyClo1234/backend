# Python3 샘플 코드 #


import requests
import json

url = 'http://apis.data.go.kr/1360000/MidFcstInfoService/getMidTa'
params ={'serviceKey' : '7971bf2e2fe86294900d2dbb67d5406dad1297a2962cef98a6577eed8d69e3ac', 'pageNo' : '1', 'numOfRows' : '10', 'dataType' : 'JSON', 'regId' : '11B10101', 'tmFc' : '202601230600' }

response = requests.get(url, params=params)
# print(response.content)

data = json.loads(response.content.decode('utf-8'))

print(data)

if data['response']['header']['resultCode'] == '00':
    item = data['response']['body']['items']['item'][0]
    
    # 깔끔하게 표 형태로 출력
    print(f"{'날짜':<10} | {'최저기온':<10} | {'최고기온':<10}")
    print("-" * 35)
    for i in range(3, 11):
        min_k = f"taMin{i}"
        max_k = f"taMax{i}"
        if min_k in item:
            print(f"{i}일 후{' ':<6} | {item[min_k]:>6}℃ | {item[max_k]:>6}℃")
else:
    print(f"오류 발생: {data['response']['header']['resultMsg']}")