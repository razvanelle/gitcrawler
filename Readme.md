<h1 align="center"> GitHub Crawler </h1>

# What is it ?
It is a simple "test" scraper for GitHub, that handles Search in Repositories, Wikis and Issues and pulls Repository links. For search type "Repository" it also pulls repository information, owner and language stats, only for the first page of results.
It needs to work with a proxy that is randomply selected from a list.
It returns the data in a json list as follows: 
```
  [
    {
      'url': 'https://github.com/psf/requests',
      'extra': {
        'owner': 'psf',
        'language_stats': {
          'Python': '97.5%',
          'PowerShell': '2.2%',
          'Makefile': '0.3%'
        }
      }
    },
    ...
  ]
```
This app was built for test purposes, as it is obviously easier to use the `Git Hub REST API` to gather this data.

# Design decisions
I was debating over using proper html parsing (a library like lxml or even something more powerful like BeautifulSoup). This means that we have to store a full HTML page (about 100KB) and build a tree-like structure by doing XML-parsing. Searches are approx O(log(n)), not bad for our case, but not great either if we have to go through multiple pages of search results. 

An idea was to do **partial HTML** parsing into a tree, but that adds some other complications, like making sure the HTML is valid, etc.

For this particular case I think the requirements are satisfied by using regex matching.

As I wanted to optimize as much as possible for performance (both CPU and Memory). After analyzing the HTML code of the GitHub pages, i found it was possible to use single line patterns. This allows us to do a **"streaming" implementation**, where the HTML is read line-by-line using an iterator and it can yeld matches to the consumer as soon as they are found. This means that "ideally" we don't need to keep more than one line in memory at a time (this varies because of HTTP buffers, etc). Also regex is quite fast (mostly linear complexity).

Some other decision was to use `requests` library instead of `urllib`. I initially started with `urllib` since it's included by default, but I ran into problems with proxy operation. It is very slow and often fails, which doesn't happen using `requests`.

NOTE: I also included the original `git_parse_demo.py` code, which is a straightforward implementation, sequential, etc. It is more of a prototype. However, because of the sequential approach, lots of time is spent waiting so I could not resist adding some simple threading.

In the final implementation `git_crawler.py` we have a `JobManager` class to handle `Job` instances running on Threads, so they can execute during slow I/O operations.
Everything is wrapped in `GitCrawler` class, it extends the JobManager and adds specific functionality for GitHub. We can extend the functionality to other sites by writing new `XyzCrawler` classes.

## Job class
The `Job` class wraps a URL fetch and parse job using a regex pattern for parsing. 
It's supposed to be an abstract implementation, it receives a job_id, URL, Proxy, a regex pattern and returns (yelds) matches in a generator form. The job_id was added just for ease of use, to process the result easier, as it's coming from an unknown job.
In order to start the job we call the run() method, which in turn starts the GET request and parser and returns a generator that yelds a result every time a match is found.

## JobManager class
The Jobmanager is a basic job manager. I uses internally a `jobs` dict() to store jobs that were started as key and a callback function as value.
Calling run_job(job, callback) spawns a Thread that runs the job's run() method and then calls the `callback(job_manager, job_id, result_gen)`. 
The values in result_gen can be used to spawn new jobs (using the `job_manager` param), before the job itself was finished.
After the job is finished it is removed from the `jobs` dict.
In order to make sure all jobs have finished we have to wait until the `jobsd` dict is empty. A utility function is provided, running() for this purpose:
```
  while job_mgr.running():
    time.sleep(0.01)
```
## GitCrawler class
This is an estension of the job manager that is specific for GitHub. It has specific attributes such as BASE_URL, it constructs search in a specific way, it choosses proxy rendomly from the list, etc.
Also it has 2 specific callback handlers defined for the 2 types of jobs:
```
  def on_lang_stats(self, crawler, repo_id, lang_result):
    ... # callsed after repository page parsing started for the lang_stats.

  def on_search_results(self, crawler, job_id, repos):
    ... # callsed after search results parsing started, looking for repositories.
```
# Install and run
Requirements: Python 3, PIP, properly setup (environment vars)

Dependencies: requsts

Extras (for testing): pytest, coverage

Simply git clone this repository or download/unzip to a folder, `cd` to that folder and run commands:

1. Create virtual env:
```
  $> virtualenv venv
  or 
  $> python3 -m venv venv
```
2. Activate venv, example for linux (look up the Windows alernative)
```
  $> source venv/Scripts/activate
```
3. Add PIP dependencies, either install manually the dependencies above, or:
```
  $> pip install -r requirement.txt  
```
4. Create a `run.py` file with content:
```
from git_crawler import GitCrawler

config = {
  'keywords': ['python', 'html', 'parser'],
  'proxies': ['89.42.133.58:8080', '176.62.188.158:56351', '167.99.164.136:80'],
  'search_type': 'Repositories'
}

git_crawler = GitCrawler(config)
results = git_crawler.run()

print(results)
```
4. Run
```
  $> py run.py
```
5. Hack away ...

# Testing and coverage

In order to run Unit Tests use command: 
```
  $> pip install pytest
  $> pytest
```

For coverage: 
```
  $> pip install coverage
  $> coverage run test_git_crawler.py
  $> coverage report
```

Latest coverage report

```
  Name                  Stmts   Miss  Cover
  -----------------------------------------
  git_crawler.py           70      0   100%
  test_git_crawler.py      65      0   100%
  -----------------------------------------
  TOTAL                   135      0   100%
```
