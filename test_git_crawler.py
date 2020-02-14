import unittest
import time

from git_crawler import GitCrawler, Job, JobManager

class TestJob(unittest.TestCase):
  def test_create_job(self):
    url = 'http://test.com'
    proxy = None
    pattern = r'test'
    name = 'test-job'
    j = Job(url, proxy, pattern, name)
    self.assertEqual(j.url, url)
    self.assertEqual(j.pattern, pattern)
    self.assertEqual(j.proxy, proxy)
    self.assertEqual(j.job_id, name)


  def test_run_parsing(self):
    url = 'http://httpbin.org/html'
    proxy = None
    pattern = r'<h1>(.*?)<\/h1>'
    name = 'test-job'

    j = Job(url, proxy, pattern, name)
    response = j.run()
    results = list(response)
    self.assertEqual(len(results), 1)
    expected_result = 'Herman Melville - Moby-Dick'
    self.assertEqual(results[0], expected_result)

  # TODO: add negative cases


class TestJobManager(unittest.TestCase):
  def test_create(self):
    jm = JobManager()
    self.assertEqual(jm.jobs, {})
  
  def test_run_job(self):
    class TestBadJob:
      def __init__(self):
        pass
    bad_job = TestBadJob()

    class TestJob:
      def __init__(self, job_id):
        self.job_id = job_id
      def run(self):
        time.sleep(0.1)
        return ['row']
    def on_finish(manager, job_id, result):
      self.assertEqual(job_id, 'test-job')
      response = list(result)
      self.assertEqual(response[0], 'row')
    
    job = TestJob('test-job')    
    jm = JobManager()
    
    with self.assertRaises(AttributeError) as context:
      jm.run_job(bad_job, on_finish)

    jm.run_job(job, on_finish)

    self.assertEqual(len(jm.jobs), 1)
    while jm.running():
      time.sleep(0.01)
    # test queue empty after run
    self.assertEqual(jm.jobs, {})



class TestGitCrawler(unittest.TestCase):
  def test_create(self):
    config = {
      'keywords': ['python', 'html', 'parser'],
      'proxies': ['89.42.133.58:8080', '176.62.188.158:56351', '167.99.164.136:80'],
      'search_type': 'Repositories'
    }
    git_crawler = GitCrawler(config)
    self.assertTrue(git_crawler.proxy in config['proxies'])

  def test_run(self):
    config = {
      'keywords': ['python', 'html', 'parser'],
      'proxies': ['89.42.133.58:8080', '176.62.188.158:56351', '167.99.164.136:80'],
      'search_type': 'Repositories'
    }
    git_crawler = GitCrawler(config)
    self.assertTrue(git_crawler.proxy in config['proxies'])
    results = git_crawler.run()
    

if __name__ == '__main__':
    unittest.main()