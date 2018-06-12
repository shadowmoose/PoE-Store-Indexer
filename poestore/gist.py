import requests
import json
import os


class Gist:
	def __init__(self, gist_id, env_var='SB_GIST_API_KEY', bkup_file='api_key.key'):
		if env_var in os.environ:
			self.api_token = os.environ[env_var].strip()
		elif os.path.exists(bkup_file):
			with open(bkup_file, 'r') as o:
				self.api_token = o.read().strip()
		else:
			self.api_token = None
		self.headers = {'Accept': 'application/vnd.github.v3+json', 'Authorization': 'token %s' % self.api_token}
		self.gist_id = gist_id

	def change(self, filename, content, new_description=None, obj_override=None):
		if not self.api_token:
			return False
		payload = {
			"files": {
				filename: {
					"content": content
				}
			}
		}
		if new_description:
			payload['description'] = new_description
		if obj_override:
			payload = obj_override
		r = requests.patch('https://api.github.com/gists/%s' % self.gist_id, data=json.dumps(payload), headers=self.headers)
		return 'error' not in r.json()
