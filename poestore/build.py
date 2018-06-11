import requests
import re
from bs4 import BeautifulSoup
import json
import os


class Builder:
	def __init__(self):
		self.url_base = 'https://www.pathofexile.com/shop/'
		self.regex = r"href=\s{0,}[\"']\/shop\/category\/(.+?)[\"']"
		self.link_regex = r'"(.+?)"'
		self.items = {}

	def run(self):
		print('Loading store page...')
		page = requests.get(self.url_base).text
		matches = [m.group(1) for m in re.finditer(self.regex, page, re.MULTILINE)]
		print('\t', 'Found %i matches.' % len(matches))
		for m in matches:
			print(m)
			self.parse_page(self.url_base + 'category/' + m, category=m)
			print()

	def parse_page(self, url, category):
		print(url)
		resp = requests.get(url)
		soup = BeautifulSoup(resp.text, "html.parser")
		elems = soup.find_all(attrs={"class": 'shopItemBase'})
		for i in elems:
			name = i.find(attrs={"class": 'name'}).text
			price = i.find(attrs={"class": 'price'}).text
			desc = i.find(attrs={"class": 'description'}).text.strip()
			img = i.find(attrs={'class': 'itemImage'})['data-href']
			link = i.find(attrs={"class": 'name'})['onclick']
			link = url + '#microtransaction-' + (re.findall(self.link_regex, link)[0])
			print(name, '[%s]' % link, price, desc, img)
			ob = {
				'name': name,
				'price': price,
				'description': desc,
				'image': img,
				'link': link,
				'categories': [category],
			}
			self.add_item(ob)

	def add_item(self, it):
		nm = it['name']
		if it['name'] not in self.items:
			self.items[nm] = it
		else:
			old = self.items[nm]
			print(old)
			old['categories'].extend(it['categories'])
			old['price'] = min(it['price'], old['price'])
			self.items[nm] = old

	def write(self, file):
		with open(file, 'w') as o:
			o.write(json.dumps([o for o in self.items.values()], indent=4, sort_keys=True))


if __name__ == "__main__":
	_b = Builder()
	_b.run()
	print(_b.items)
	os.makedirs('../data/', exist_ok=True)
	_b.write('../data/store_items.json')
	print('Done.')
