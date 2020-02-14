import re
import requests
import json
import threading
import time
import random

class Job():
  '''
  A HTTP GET job that parses the HTML by line, matching the pattern expression (first occurence).\n
  Calling run() returns a generator that yelds the matches.\n
  As a limitation, it only works when we can match expressions on single line.\n
  However there are huge gains in memory consumption, as we dont have to read the whole file.
  '''
  def __init__(self, url, proxy, pattern, job_id):
    # TODO: Add verifications
    self.url = url
    self.pattern = pattern
    self.result = []
    self.proxy = proxy
    self.job_id = job_id

  def parse_with_pattern(self):
    '''
    Generator, parses the HTML by line, matching the pattern expression (first occurence).
    '''
    # TODO: Add exception handling >>> currenlty handled on thread run
    proxies = {'http': self.proxy} if self.proxy is not None else {}
    with requests.get(self.url, proxies=proxies, stream=True) as html:
      print('Parsing URL:', html.url, 'USING PATTERN:', self.pattern, 'VIA PROXY:', self.proxy)

      # we'll use the iter-lines iterator to save memory
      for line in html.iter_lines(): # TODO: split match in another function
        if line:
          line_str = line.decode('utf-8')
          match = re.search(self.pattern, line_str)
          if match is not None:
            yield match.group(1)

  def run(self):
    '''
    Initiates the HTTP GET
    Returns a generator that yelds all matches.
    As a limitation, it only works when we can match expressions on single line.
    '''
    return self.parse_with_pattern()
    
    

class JobManager:
  '''
  A basic job manager, linking a Job with a callback.\n
  The job runs on a new thread and a reference is kept in a local dict until it ends.\n
  After the Job starts, the handler is called with a generator object, so that we dont have to wait for the job to end.\n
  This can be obviously extended heavily by using ThreadPoolExecutor, futures and at least having a thread count,\n 
  but I just wanted something simple to get the job done for this specific task.\n
  '''
  def __init__(self):
    self.jobs = {}

  def _thread(self, job):
    result_iter = job.run()
    callback = self.jobs[job]
    callback(self, job.job_id, result_iter)
    del self.jobs[job]

  def run_job(self, job, callback):
    if not hasattr(job, 'job_id') or not hasattr(job, 'run'):
      raise AttributeError(f"{type(job)} object missing attribute: job_id or function: run()")

    self.jobs[job] = callback
    try: 
      t = threading.Thread(target=self._thread, args=(job,))
      t.start()
    except Exception as e:
      print('ERROR!!!', e)
      raise e


  def running(self):
    return len(self.jobs) > 0



class GitCrawler(JobManager):
  '''
  A specific crawler/job manager class for GitHub\n
  __init()__ takes a config dict, in the following format:\n
  {
    'keywords': ['python', 'html', 'parser'],
    'proxies': ['89.42.133.58:8080', '176.62.188.158:56351', '167.99.164.136:80'],
    'search_type': 'Repositories'
  }\n
  Supported search_types are: 'Repositories', 'Issues', 'Wikis'  
  '''
  # basic config for GitHub
  BASE_URL = 'https://github.com'
  TYPES = ['Repositories', 'Issues', 'Wikis']
  R_PATTERNS = [
    r'<a class=\"v-align-middle\" data-hydro.*? href=\"(\/[^\/]*\/[^\"\/]*)\">',
    r'<a class=\"muted-link text-bold\".*?href=\"(\/[^\/]*\/[^\/]*)\/issues\">',
    r'<a class=\"muted-link .*?href=\"(\/[^\/]*\/[^\/]*)\">'
  ]
  REPO_PATTERN = r'<span class="(?:lang|percent)">([^<]*?)<\/span>'
  
  def __init__(self, config):
    self.keywords = config['keywords']
    # pick a random proxy and use it for the whole session.
    self.proxy = config['proxies'][random.randint(0, len(config['proxies']) - 1)]
    self.search_type = config['search_type']
    self.PATTERNS = {q[0]: q[1] for q in zip(self.TYPES, self.R_PATTERNS)}
    params = {
      'q': '+'.join(self.keywords),
      'type': self.search_type
    }
    # I am manually building the URL as the exisitng implementations apply encoding and replace the '+' chars
    self.search_url = self.BASE_URL + '/search?' + '&'.join([f'{k}={params[k]}' for k in params])
    # we'll store results here, dict() should be thread-safe for the kind of operations that we are doing, no need for a lock.
    # If this was a larger-scale, I would add a lock on writes, as it adds very little overhead compared to the rest.
    self.results = {}
    super().__init__()

  def on_lang_stats(self, crawler, repo_id, lang_result):
    '''
    Handler for the Language stats matches
    '''
    # fully read generator values into list as we need all stats at once. Also makes it easier to write the composition code
    lang_list = list(lang_result)
    lang_stats = dict(zip(lang_list[::2], lang_list[1::2]))
    self.results[repo_id]['extra'].update( {'language_stats': lang_stats })

  def on_search_results(self, crawler, job_id, repos):
    '''
    Custom handler for the search result repository matches.\n
    Iterates through repositories and starts new jobs to get extra info (language stats)
    '''
    # using the generator, we can spawn a new job as soon as we find a match
    for repo in repos:
      self.results[repo] = {'url': self.BASE_URL+repo, 'extra': {'owner': repo.split('/')[1] } }
      job = Job(self.BASE_URL + repo, self.proxy, self.REPO_PATTERN, repo)
      crawler.run_job(job, self.on_lang_stats)

  def run(self):
    '''
    This is the main run() method. Called after setup.\n
    Returns results in json list format:\n
    [url: value, extra: { owner: value, language_stats: {lang1: value, lang2: value, ...etc... }}]
    '''
    search_job = Job(self.search_url, self.proxy, self.PATTERNS[self.search_type], 'repo')
    self.run_job(search_job, self.on_search_results)
    while self.running():
      time.sleep(0.1)
    return json.dumps(list(self.results.values()))


# # input
# config = {
#   'keywords': ['python', 'html', 'parser'],
#   'proxies': ['89.42.133.58:8080', '176.62.188.158:56351', '167.99.164.136:80'],
#   'search_type': 'Repositories'
# }

# git_crawler = GitCrawler(config) # TODO: make this context manager?
# results = git_crawler.run()


# print('================ RESULT ===============')
# print(results)

