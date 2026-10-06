import requests
import json

token='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'
headers={
    'Authorization': f'Bearer {token}',
    'Accept': 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28'
}
r=requests.get('https://api.github.com/repos/analisistiempos-sketch/Seguimiento_usos_mc/contents/datos', headers=headers)
print(r.status_code)
print(r.text)
