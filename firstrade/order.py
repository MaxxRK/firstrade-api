import requests
session = requests.Session()

url = 'https://invest.firstrade.com/cgi-bin/login?ft_locale=en-us'
# send a get request to the server
response = session.get(url)
  
# print the response dictionary
print(session.cookies.get_dict())