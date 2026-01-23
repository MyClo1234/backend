from fastapi import APIRouter, Response
import requests
import json
import io
import csv

router = APIRouter(prefix="/weather", tags=["Weather"])

@router.get("/download-csv")
async def download_weather_csv():
    # 1. 기상청 API 호출 로직 (기존 코드 활용)
    url = 'http://apis.data.go.kr/1360000/MidFcstInfoService/getMidTa'
    params = {
        'serviceKey': '7971bf2e2fe86294900d2dbb67d5406dad1297a2962cef98a6577eed8d69e3ac',
        'pageNo': '1',
        'numOfRows': '10',
        'dataType': 'JSON',
        'regId': '11B10101',
        'tmFc': '202601230600'
    }
    
    response = requests.get(url, params=params)
    data = json.loads(response.content.decode('utf-8'))
    item = data['response']['body']['items']['item'][0]

    # 2. CSV 생성 로직
    output = io.StringIO()
    # 엑셀에서 한글이 깨지지 않게 하려면 utf-8-sig 인코딩이 필요할 수 있습니다.
    writer = csv.writer(output)
    writer.writerow(["날짜", "최저기온", "최고기온"])
    
    for i in range(3, 11):
        writer.writerow([f"{i}일 후", item.get(f'taMin{i}'), item.get(f'taMax{i}')])

    csv_content = output.getvalue()
    
    # 3. 파일 다운로드 응답
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=weather.csv"}
    )