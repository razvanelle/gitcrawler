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
I was debating over using proper html parsing (a library like lxml or even something more powerful like BeautifulSoup). This means that we have to store a full HTML page (about 100KB) and build a tree-like structure by doing XML-parsing. Searches are approx O(n log(n)) - not too bad for our case, but not great if we have to go through multiple pages of search results.

For this particular case I think the requirements are satisied by using regex matching.

Also I wanted to optimize as much as possible for performance (both CPU and Memory). After analyzing the HTML code of the GitHub pages, i found it was possible to use single line patterns. This allows us to do a "streaming" implementation, where the URL response is read line-by-line using an iterator and it can yeld results to our consumer as soon as they are found.

Some other decisions:
- Using `requests` library instead of `urllib`. I initially started with `urllib` since it's included by default, but I ran into problems with proxy operation. It is very slow and often fails, which doesn't happen to `requests`.


NOTE: I included the original `git_parser` code, which is a straightforward implementation, functional, sequential, etc. It is more of a prototype. However, lots of time is spent waiting so I could not resist adding some simple threading.

In the final implementation we have a `JobManager` class to handle `Job` instances running on Threads, so they can execute during slow I/O operations.
Everything is wrapped in `GitCrawler` class, it extends the JobManager and adds specific functionality for GitHub. We can extend the functionality to other sites by writing new `XyzCrawler` classes.

## Job class
The `Job` class wraps a URL fetch and parse job using a regex pattern for parsing. 
It's supposed to be an abstract implementation, it receives a job_id, URL, Proxy, a regex pattern and returns (yelds) matches in a generator form. The job_id was added just for ease of use, to understand the result.
In order to start the job we call the run() method, which in turn starts the GET request and parser and returns a generator that yelds a result every time a match is found.

## JobManager class
The Jobmanager is a basic job manager. I uses internally a `jobs` dict() to store jobs that were started as key and a callback function as value.
Calling run_job(job, callback) spawns a Thread that runs the job's run() method and then calls the `callback(job_manager, job_id, result_gen)`. 
The values in result_gen can be used to spawn new jobs (using the `job_manager` param), before the job itself was finished.
After the job is finished it is removed from the `jobs` dict.
In order to make sure all jobs have finished we have to wait until the `jobsd` dict is empty. A utility function is provided: running() for this purpose:
  while job_mgr.running():
    time.sleep(0.01)

## GitCrawler class
This is an estension of the job manager that is specific for GitHub. It has specific attributes such as BASE_URL, it constructs search in a specific way, it cheeses proxy rendomly from the list, etc.
Also it has 2 specific callback handlers defined for the 2 types of jobs:
```
  def on_lang_stats(self, crawler, repo_id, lang_result):
    ...

  def on_search_results(self, crawler, job_id, repos):
    ...
```
# Install and run
Requirements: Python 3, PIP, properly setup
Dependencies: requsts, 
Extras (for testing): pytest, coverage

Simply git clone this repository or download/unzip to a folder

1. create virtual env:
```
  virtualenv venv
```
2. add PIP dependencies
```
  PIP install requests
```
3. create a `run.py` file with content:
```
  config = {
    'keywords': ['python', 'html', 'parser'],
    'proxies': ['89.42.133.58:8080', '176.62.188.158:56351', '167.99.164.136:80'],
    'search_type': 'Repositories'
  }

  git_crawler = GitCrawler(config) # TODO: make this context manager?
  results = git_crawler.run()

  print(results)
```
4. Run
```
  py run.py
```
5. Hack away ...
