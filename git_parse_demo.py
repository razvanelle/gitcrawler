import re
import requests
import json

# input
keywords = ['python', 'html', 'parser']
proxies = {
  "http": "89.42.133.58:8080",
}
search_type = 'Repositories'


# config
BASE_URL = 'https://github.com'

TYPES = ['Repositories', 'Issues', 'Wikis']
PATTERNS = [
  r'<a class=\"v-align-middle\" data-hydro.*? href=\"(\/[^\/]*\/[^\"\/]*)\">',
  r'<a class=\"muted-link text-bold\".*?href=\"(\/[^\/]*\/[^\/]*)\/issues\">',
  r'<a class=\"muted-link .*?href=\"(\/[^\/]*\/[^\/]*)\">'
]

PATTERNS = { q[0]:q[1] for q in zip(TYPES, PATTERNS) }

params = {
  'q': '+'.join(keywords),
  'type': search_type
}
full_url = BASE_URL+'/search?'+'&'.join([f'{k}={params[k]}' for k in params])
print(full_url)

def parse_with_pattern(full_url, proxies, pattern):
  result = []

  with requests.get(full_url, proxies=proxies, stream=True) as html:
    print('Parsing URL:', html.url, 'USING PATTERN:', pattern, 'VIA PROXY:', proxies)

    # we'll use the iter-lines iterator to save memory
    for line in html.iter_lines():
      if line:
        line_str = line.decode('utf-8')
        match = re.search(pattern, line_str)
        if match is not None:
          result.append(match.group(1))

  return result

pattern = re.compile(PATTERNS[search_type])
repos = parse_with_pattern(full_url, proxies, pattern)

repo_pattern = r'<span class="(?:lang|percent)">([^<]*?)<\/span>'
result = []
for repo in repos:
  repo_dict = {
    'url': BASE_URL + repo,
  }
  if search_type == 'Repositories':
    langs = parse_with_pattern(BASE_URL + repo, proxies, repo_pattern)
    repo_dict.update({'extra': { 'owner': repo.split('/')[1],
                                 'language_stats': dict(zip(langs[::2], langs[1::2]))}})
                            
  result.append(repo_dict)

print(json.dumps(result))
