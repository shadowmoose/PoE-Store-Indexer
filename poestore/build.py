import requests
import re
from bs4 import BeautifulSoup
import json
import os
import time
from gist import Gist


headers = {
	'User-Agent': 'Mozilla/5.0 (Android 4.4; Mobile; rv:41.0) Gecko/41.0 Firefox/41.0'
}


class Builder:
	def __init__(self):
		self.url_base = 'https://www.pathofexile.com/shop/'
		self.package_url = 'https://www.pathofexile.com/purchase'
		self.regex = r"href=\s{0,}[\"']\/shop\/category\/(.+?)[\"']"
		self.link_regex = r'"(.+?)"'
		self.items = {}
		self.packages = []
		self.start = 0

	def run(self):
		print('Loading store page...', flush=True)
		self.start = time.time()
		page = requests.get(self.url_base, headers=headers).text
		matches = [m.group(1) for m in re.finditer(self.regex, page, re.MULTILINE)]
		print('\t', 'Found %i categories.' % len(matches), flush=True)
		assert len(matches) > 0
		for m in matches:
			print(m, flush=True)
			self.parse_page(self.url_base + 'category/' + m, category=m)
			print('', flush=True)

	def parse_page(self, url, category):
		print(url, flush=True)
		resp = requests.get(url, headers=headers)
		if resp.status_code != 200:
			raise Exception('Invalid response from server: %s' % resp.status_code)
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
				'points': int(price),
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
			old['points'] = min(it['points'], old['points'])
			self.items[nm] = old

	def parse_packages(self):
		print('Parsing Point Packages...', flush=True)
		resp = requests.get(self.package_url, headers=headers)
		if resp.status_code != 200:
			raise Exception('Invalid response from server: %s' % resp.status_code)
		soup = BeautifulSoup(resp.text, "html.parser")
		for p in soup.find_all(class_='package'):
			bundle = p.get('id')
			points = None
			price = None
			if bundle is None:
				bundle = 'PointPack'
			print(bundle, flush=True)

			pf = p.find(class_='points')
			if pf:
				assert 'points' in pf.text.lower()
				points = int(''.join([c for c in pf.text if c in '0123456789.']))
			else:
				for pts in p.find_all('li'):
					if 'Points' in pts.text:
						try:
							val = int(pts.strong.text)
						except ValueError:
							continue
						points = val
			print('\tPoints:', points, flush=True)
			assert points is not None

			for btn in p.find_all(class_='price'):
				price = btn.text.strip().lower()
				assert '$' in price
				price = float(''.join([c for c in price if c in '0123456789.']))
				print('\tPrice:', price, flush=True)
			assert price is not None
			self.packages.append({'pack_name': bundle, 'points': points, 'approx_price_usd': price})
		print('Found %s point packages.' % len(self.packages))
		assert len(self.packages) > 0

	def write(self, file):
		with open(file, 'w') as o:
			o.write(self.to_string())

	def to_string(self):
		return json.dumps({
			'store_items': [o for o in sorted(self.items.values(), key=lambda it: it['name'])],
			'point_packages': sorted(self.packages, key=lambda pak: pak['pack_name']),
			'@metadata': {
				'version': 1.4,
				'compatible_since': 1.4,
				'timestamp': time.time(),
				'runtime': time.time() - self.start
			}
		}, indent=4, sort_keys=True)


if __name__ == "__main__":
	_b = Builder()
	_b.parse_packages()
	_b.run()
	filepath = os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + '/../data/store_items.json')
	print(filepath, flush=True)
	os.makedirs(os.path.dirname(filepath), exist_ok=True)
	_b.write(filepath)
	_g = Gist(gist_id='9b64e0f0452001883cb341fee975c12b', bkup_file='../api_key.key')
	if _g.change('data.json', _b.to_string()):
		print('Done. Pushed changes.')
	else:
		print('Done.')
