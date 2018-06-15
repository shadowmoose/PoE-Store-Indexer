import requests
import re
from bs4 import BeautifulSoup
import json
import os
import time
from gist import Gist


class Builder:
	def __init__(self):
		self.url_base = 'https://www.pathofexile.com/shop/'
		self.regex = r"href=\s{0,}[\"']\/shop\/category\/(.+?)[\"']"
		self.link_regex = r'"(.+?)"'
		self.items = {}
		self.start = 0

	def run(self):
		print('Loading store page...', flush=True)
		self.start = time.time()
		page = requests.get(self.url_base).text
		matches = [m.group(1) for m in re.finditer(self.regex, page, re.MULTILINE)]
		print('\t', 'Found %i categories.' % len(matches), flush=True)
		for m in matches:
			print(m, flush=True)
			self.parse_page(self.url_base + 'category/' + m, category=m)
			print('', flush=True)

	def parse_page(self, url, category):
		print(url, flush=True)
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
		if nm not in self.items:
			self.items[nm] = it
		else:
			old = self.items[nm]
			old['categories'].extend(it['categories'])
			old['price'] = min(it['price'], old['price'])
			self.items[nm] = old

	def write(self, file):
		with open(file, 'w') as o:
			o.write(self.to_string())

	def to_string(self):
		return json.dumps({
			'items': [o for o in self.items.values()],
			'@metadata': {
				'version': 1.1,
				'compatible_since': 1.1,
				'timestamp': time.time(),
				'runtime': time.time() - self.start
			}
		}, indent=4, sort_keys=True)


if __name__ == "__main__":
	_b = Builder()
	_b.run()
	filepath = os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + '/../data/store_items.json')
	print(filepath, flush=True)
	os.makedirs(os.path.dirname(filepath), exist_ok=True)
	_b.write(filepath)
	_g = Gist(gist_id='c5b9e22d36cd9b08329b97a9aaa19746', bkup_file='../api_key.key')
	if _g.change('data.json', _b.to_string()):
		print('Done. Pushed changes.')
	else:
		print('Done.')
