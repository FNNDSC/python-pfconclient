
import io
import zipfile
import random
import time
from unittest import TestCase
from unittest import mock
from nose.plugins.attrib import attr

from pfconclient import client


class ClientTests(TestCase):

    def setUp(self):
        self.pfcon_url = "http://localhost:30006/api/v1/"
        self.pfcon_jobs_url = "http://localhost:30006/api/v1/jobs/"
        self.pfcon_user = 'pfcon'
        self.pfcon_password = 'pfcon1234'
        self.pfcon_auth_url = self.pfcon_url + 'auth-token/'

        # create an in-memory zip file
        self.zip_file = io.BytesIO()
        with zipfile.ZipFile(self.zip_file, 'w', zipfile.ZIP_DEFLATED) as job_data_zip:
            job_data_zip.writestr('test.txt', 'Test file')
        self.zip_file.seek(0)

        job_descriptors = {
            'cmd_args': '--saveinputmeta --saveoutputmeta --dir cube/uploads',
            'cmd_path_flags': '--dir',
            'auid': 'cube',
            'number_of_workers': 1,
            'cpu_limit': 1000,
            'memory_limit': 200,
            'gpu_limit': 0,
            'image': 'fnndsc/pl-simplefsapp',
            'selfexec': 'simplefsapp',
            'selfpath': '/usr/local/bin',
            'execshell': 'python3',
            'type': 'fs'}
        self.job_descriptors = job_descriptors.copy()

    def test_submit_job(self):
        """
        Test whether submit_job method makes the appropriate request to pfcon.
        """
        response_mock = mock.Mock()
        response_mock.status_code = 200
        response_mock.json = mock.Mock(return_value='json content')
        with mock.patch.object(client.requests, 'post',
                               return_value=response_mock) as requests_post_mock:
            job_id = 'chris-jid-1'
            zip_content = self.zip_file.getvalue()

            # call submit_job method
            cl = client.Client(self.pfcon_url, 'a@token')
            cl.max_wait = 2 ** 3
            cl.submit_job(job_id, self.job_descriptors, zip_content)

            requests_post_mock.assert_called_with(self.pfcon_jobs_url,
                                                  files={'data_file': zip_content},
                                                  data=self.job_descriptors,
                                                  headers={'Authorization': 'Bearer a@token'},
                                                  timeout=1000)

    @attr('integration')
    def test_integration_submit_job(self):
        """
        Test whether submit_job method can successfully submit a job for execution.
        """
        job_id = 'chris-jid-%s' % random.randint(10**3, 10**7)
        zip_content = self.zip_file.getvalue()

        # call submit_job method

        auth_token = client.Client.get_auth_token(self.pfcon_auth_url, self.pfcon_user,
                                                  self.pfcon_password)
        cl = client.Client(self.pfcon_url, auth_token)
        cl.max_wait = 2 ** 3
        resp_data = cl.submit_job(job_id, self.job_descriptors, zip_content)
        self.assertIn('data', resp_data)
        self.assertIn('compute', resp_data)

        # clean up
        time.sleep(2)
        cl.delete_job(job_id)

    def test_get_job_status(self):
        """
        Test whether get_job_status method makes the appropriate request to pfcon.
        """
        response_mock = mock.Mock()
        response_mock.status_code = 200
        response_mock.json = mock.Mock(return_value='json content')
        with mock.patch.object(client.requests, 'get',
                               return_value=response_mock) as requests_get_mock:
            job_id = 'chris-jid-1'

            # call get_job_status method
            cl = client.Client(self.pfcon_url, 'a@token')
            cl.max_wait = 2 ** 3
            cl.get_job_status(job_id)

            url = self.pfcon_jobs_url + job_id + '/'
            requests_get_mock.assert_called_with(url,
                                                 headers={'Authorization': 'Bearer a@token'},
                                                 timeout=1000)

    @attr('integration')
    def test_integration_get_job_status(self):
        """
        Test whether get_job_status method can get the status of a job from pfcon.
        """
        job_id = 'chris-jid-%s' % random.randint(10 ** 3, 10 ** 7)
        zip_content = self.zip_file.getvalue()
        auth_token = client.Client.get_auth_token(self.pfcon_auth_url, self.pfcon_user,
                                                  self.pfcon_password)
        cl = client.Client(self.pfcon_url, auth_token)
        cl.max_wait = 2 ** 3
        cl.submit_job(job_id, self.job_descriptors, zip_content)
        time.sleep(2)

        # call get_job_status method
        resp_data = cl.get_job_status(job_id)

        self.assertIn('compute', resp_data)
        self.assertIn('status', resp_data['compute'])

        # clean up
        cl.delete_job(job_id)

    def test_get_job_zip_data(self):
        """
        Test whether get_job_zip_data method makes the appropriate request to pfcon.
        """
        response_mock = mock.Mock()
        response_mock.status_code = 200
        response_mock.content = 'zip file content'
        with mock.patch.object(client.requests, 'get',
                               return_value=response_mock) as requests_get_mock:
            job_id = 'chris-jid-1'

            # call get_job_status method
            cl = client.Client(self.pfcon_url, 'a@token')
            cl.max_wait = 2 ** 3
            resp_data = cl.get_job_zip_data(job_id)

            self.assertEqual(resp_data, response_mock.content)
            url = self.pfcon_jobs_url + job_id + '/file/'
            requests_get_mock.assert_called_with(url,
                                                 headers={'Authorization': 'Bearer a@token'},
                                                 timeout=1000)

    @attr('integration')
    def test_integration_get_job_zip_data(self):
        """
        Test whether get_job_status method can get the status of a job from pfcon.
        """
        job_id = 'chris-jid-%s' % random.randint(10 ** 3, 10 ** 7)
        zip_content = self.zip_file.getvalue()
        auth_token = client.Client.get_auth_token(self.pfcon_auth_url, self.pfcon_user,
                                                  self.pfcon_password)
        cl = client.Client(self.pfcon_url, auth_token)
        cl.max_wait = 2 ** 3
        cl.submit_job(job_id, self.job_descriptors, zip_content)
        time.sleep(2)
        cl.poll_job_status(job_id)

        # call get_job_zip_data method
        resp_data = cl.get_job_zip_data(job_id)

        memory_zip_file = io.BytesIO(resp_data)
        with zipfile.ZipFile(memory_zip_file, 'r', zipfile.ZIP_DEFLATED) as job_data_zip:
            filenames = job_data_zip.namelist()
            self.assertIn('test.txt', filenames)

        # clean up
        cl.delete_job(job_id)
