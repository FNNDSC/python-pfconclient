"""
Pfcon API client module.
"""

import os
import io
import time
import zipfile
import json
import requests
from .exceptions import PfconRequestException


class Client(object):
    """
    A pfcon API client.
    """

    def __init__(self, url, username=None, password=None):
        self.url = url
        self.username = username
        self.password = password

        # initial and maximum wait time (seconds) for exponetial-backoff-based retries
        self.initial_wait = 2
        self.max_wait = 2**16

    def run_job(self, job_id, d_job_descriptors, input_dir, output_dir, timeout=1000):
        """
        Run a new job by taking the passed input_dir and output_dir as the
        local input and output directories for the plugin respectively.
        """
        # create job zip file content from local input_dir
        job_zip_file = self.create_zip_file(input_dir)
        zip_content = job_zip_file.getvalue()

        print('Submitting job %s to pfcon service at -->%s<--...\n' % (job_id, self.url))
        self.submit_job(job_id, d_job_descriptors, zip_content, timeout)

        # poll for job's execution status using exponential backoff retries
        l_status = self.poll_job_status(job_id, timeout)
        if 'finishedSuccessfully' in l_status:
            print('Downloading and unpacking job %s files...' % job_id)
            self.get_job_files(job_id, output_dir, timeout)
            print('Done')
        elif 'finishedWithError' in l_status:
            print('Job %s finished with errors' % job_id)
        else:
            print('Job %s finished with unexpected status: %s' % (job_id, l_status))
        return l_status

    def submit_job(self, job_id, d_job_descriptors, data_file, timeout=1000):
        """
        Submit a new job.
        """
        d_job_descriptors['jid'] = job_id
        resp = self.post(self.url, d_job_descriptors, data_file, timeout)
        return self.get_data_from_response(resp)

    def get_job_status(self, job_id, timeout=1000):
        """
        Get a job's execution status.
        """
        url = self.url + job_id + '/'
        resp = self.get(url, timeout)
        return self.get_data_from_response(resp)

    def poll_job_status(self, job_id, timeout=1000):
        """
        Poll for a job's execution status until 'finishedSuccessfully' or
        'finishedWithError'.
        """
        wait_time = self.initial_wait
        poll_num = 1
        l_status = []
        while self.max_wait >= wait_time:
            time.sleep(wait_time)
            print('Polling job %s status, poll number: %s' % (job_id, poll_num))
            d_resp = self.get_job_status(job_id, timeout)
            l_status = d_resp['compute']['d_ret']['l_status']
            print('Job %s status: %s' % (job_id, l_status))
            if ('finishedSuccessfully' in l_status) or ('finishedWithError' in l_status):
                break
            else:
                wait_time = self.initial_wait * 2 ** poll_num
                poll_num += 1
                print('Waiting for %s seconds before the next poll...\n' % wait_time)
        return l_status

    def get_job_zip_data(self, job_id, timeout=1000):
        """
        Get a job's zip file content.
        """
        url = self.url + job_id + '/file/'
        resp = self.get(url, timeout)
        zip_content = self.get_data_from_response(resp, 'application/zip')
        return zip_content

    def get_job_zip_file(self, job_id, local_dir, timeout=1000):
        """
        Get and save a job's zip file into a local directory.
        """
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)
        zip_content = self.get_job_zip_data(job_id, timeout)
        fpath = os.path.join(local_dir, job_id + '.zip')
        with open(fpath, 'wb') as f:
            f.write(zip_content)

    def get_job_files(self, job_id, local_dir, timeout=1000):
        """
        Get a job's output files unpacked within a local directory.
        """
        zip_content = self.get_job_zip_data(job_id, timeout)
        memory_zip_file = io.BytesIO(zip_content)
        with zipfile.ZipFile(memory_zip_file, 'r', zipfile.ZIP_DEFLATED) as job_data_zip:
            filenames = job_data_zip.namelist()
            print('Number of files to decompress at %s: %s' % (local_dir, len(filenames)))
            for fname in filenames:
                content = job_data_zip.read(fname)
                fpath = os.path.join(local_dir, fname.lstrip('/'))
                fpath_basedir = os.path.dirname(fpath)
                if not os.path.exists(fpath_basedir):
                    os.makedirs(fpath_basedir)
                with open(fpath, 'wb') as f:
                    f.write(content)

    def get(self, url, timeout=30):
        """
        Make a GET request to pfcon.
        """
        try:
            if self.username or self.password:
                r = requests.get(url,
                                 auth=(self.username, self.password),
                                 timeout=timeout)
            else:
                r = requests.get(url, timeout=timeout)
        except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
            raise PfconRequestException(str(e))
        return r

    def post(self, url, data, data_file=None, timeout=30):
        """
        Make a POST request to pfcon.
        """
        if data_file is None:
            headers = {'Content-Type': 'application/json'}
            files = None
            data = json.dumps(data)
        else:
            # this is a multipart request
            headers = None
            files = {'data_file': data_file}
        try:
            if self.username or self.password:
                r = requests.post(url, files=files, data=data,
                                  auth=(self.username, self.password),
                                  timeout=timeout, headers=headers)
            else:
                r = requests.post(url, files=files, data=data, timeout=timeout,
                                  headers=headers)
        except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
            raise PfconRequestException(str(e))
        return r

    def delete(self, url, timeout=30):
        """
        Make a DELETE request to pfcon.
        """
        try:
            if self.username or self.password:
                r = requests.delete(url,
                                    auth=(self.username, self.password),
                                    timeout=timeout)
            else:
                r = requests.delete(url, timeout=timeout)
        except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
            raise PfconRequestException(str(e))

    @staticmethod
    def get_data_from_response(response, content_type='application/json'):
        """
        Static method to get the data dictionary from a response object.
        """
        if response.status_code != 200:
            raise PfconRequestException(response.text)
        if content_type == 'application/json':
            data = response.json()
        else:
            data = response.content
        return data

    @staticmethod
    def create_zip_file(local_dir):
        """
        Create job zip file ready for transmission to the remote from a local directory.
        """
        if not os.path.isdir(local_dir):
            raise ValueError('Invalid local input dir: %s' % local_dir)
        memory_zip_file = io.BytesIO()
        with zipfile.ZipFile(memory_zip_file, 'w', zipfile.ZIP_DEFLATED) as job_data_zip:
            for root, dirs, files in os.walk(local_dir):
                for filename in files:
                    local_file_path = os.path.join(root, filename)
                    arc_path = local_file_path.replace(local_dir, '', 1).lstrip('/')
                    job_data_zip.write(local_file_path, arcname=arc_path)
        memory_zip_file.seek(0)
        return memory_zip_file
