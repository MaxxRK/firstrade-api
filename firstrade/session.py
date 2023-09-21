symbol = 'INTC'
url = f'https://invest.firstrade.com/cgi-bin/getxml?page=quo&quoteSymbol={symbol}'
headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'Host': 'invest.firstrade.com',
    'Referer': 'https://invest.firstrade.com/cgi-bin/main',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.81',
    'X-Requested-With': 'XMLHttpRequest',
    'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Microsoft Edge";v="116"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"'
}
symbol_data = session.get(url=url, headers=headers)
print(symbol_data.text)
soup = BeautifulSoup(symbol_data.text, 'xml')
quote = soup.find('quote')
symbol = quote.find('symbol').text
exchange = quote.find('exchange').text
bid = quote.find('bid').text
ask = quote.find('ask').text
last = quote.find('last').text
change = quote.find('change').text
high = quote.find('high').text
low = quote.find('low').text
volume = quote.find('vol').text
company_name = quote.find('companyname').text

print(f"Symbol: {symbol}")
print(f"Exchange: {exchange}")
print(f"Bid: {bid}")
print(f"Ask: {ask}")
print(f"Last: {last}")
print(f"Change: {change}")
print(f"High: {high}")
print(f"Low: {low}")
print(f"Volume: {volume}")
print(f"Company Name: {company_name}")







headers = {
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
	'Accept-Encoding': 'gzip, deflate, br',
	'Accept-Language': 'en-US,en;q=0.9',
	'Cache-Control': 'max-age=0',
	'Connection': 'keep-alive',
	'Host': 'invest.firstrade.com',
	'Referer': 'https://invest.firstrade.com/cgi-bin/login',
	'Sec-Fetch-Dest': 'document',
	'Sec-Fetch-Mode': 'navigate',
	'Sec-Fetch-Site': 'same-origin',
	'Sec-Fetch-User': '?1',
	'Upgrade-Insecure-Requests': '1',
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.81',
	'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Microsoft Edge";v="116"',
	'sec-ch-ua-mobile': '?0',
	'sec-ch-ua-platform': '"Windows"'
}


#response_three = session.get(url=url, headers=headers, cookies=session.cookies)
#print(response_three.headers)
#print(session.cookies.get_dict())