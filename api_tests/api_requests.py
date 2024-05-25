import requests
from bs4 import BeautifulSoup

response = requests.get('https://services.planningcenteronline.com/songs/24408198/arrangements/28252258')
print(response.status_code)
soup = BeautifulSoup(response.text, 'lxml')
data = soup.find_all("span", role="presentation")
print(data)
#for row in data:
#    text = row.find(itemprop="text").text
#    print(response.text)