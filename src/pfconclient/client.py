"""
Pfcon API client module.
"""

import os
import io
import time
import zipfile
import json
import requests
from enum import Enum

from .exceptions import PfconRequestException, PfconRequestInvalidTokenException


class JobType(Enum):
    COPY = 'copy'
    PLUGIN = 'plugin'
    UPLOAD = 'upload'
    DELETE = 'delete'


class Client(object):
    """
    A pfcon API client.
    """

    def __init__(self, url: str, auth_token: str):
        self.url = url
        self.set_auth_token(auth_token)
        self.pfcon_innetwork = None
        self.requires_copy_job = None
        self.requires_upload_job = None

        # initial and maximum wait time (seconds) for exponential-backoff-based retries
        self.initial_wait = 2
        self.max_wait = 2**15

    def set_auth_token(self, auth_token: str):
        if not auth_token:
            raise PfconRequestInvalidTokenException(f'Invalid auth token: {auth_token}')
        self.auth_token = auth_token

    def get_server_info(self, timeout: int = 30) -> dict:
        """
        Get info about the PFCON server.
        """
        url = self.url + self._get_job_url_base_path(JobType.PLUGIN)
        resp = self.get(url, timeout)
        data = self.get_data_from_response(resp)
        self.pfcon_innetwork = data.get('pfcon_innetwork')
        self.requires_copy_job = data.get('requires_copy_job')
        self.requires_upload_job = data.get('requires_upload_job')
        return data

    def submit_job(self, job_type: JobType, job_id: str, d_job_descriptors: dict,
                   data_file: io.BytesIO = None, timeout: int = 1000) -> dict:
        """
        Submit a new job. When pfcon is not in-network, a zip data_file can be
        included as a multipart upload.
        """
        url_path = self._get_job_url_base_path(job_type)
        d_job_descriptors['jid'] = job_id
        url = self.url + url_path
        resp = self.post(url, d_job_descriptors, data_file, timeout)
        return self.get_data_from_response(resp)

    def get_job_status(self, job_type: JobType, job_id: str, timeout: int = 1000) -> dict:
        """
        Get a job's execution status.
        """
        url_path = self._get_job_url_base_path(job_type)
        url = self.url + url_path + job_id + '/'
        resp = self.get(url, timeout)
        return self.get_data_from_response(resp)

    def poll_job_status(self, job_type: JobType, job_id: str, timeout: int = 1000) -> str:
        """
        Poll for a job's execution status until 'undefined', 'finishedSuccessfully' or
        'finishedWithError'.
        """
        wait_time = self.initial_wait
        poll_num = 1
        status = 'undefined'

        while self.max_wait >= wait_time:
            print(f'Waiting for {wait_time}s before next polling for job status ...\n')
            time.sleep(wait_time)

            print(f'Polling job {job_id} status, poll number: {poll_num}')
            d_resp = self.get_job_status(job_type, job_id, timeout)
            status = d_resp['compute']['status']
            print(f'Job {job_id} status: {status}')

            if status in ('undefined', 'finishedSuccessfully', 'finishedWithError'):
                break
            else:
                wait_time = self.initial_wait * 2 ** poll_num
                poll_num += 1
        return status

    def get_plugin_job_zip_data(self, job_id: str, timeout: int = 1000) -> bytes:
        """
        Get a plugin job's zip file content. Only available when pfcon is not in-network.
        """
        url_base = self._get_job_url_base_path(JobType.PLUGIN)
        url = self.url + url_base + job_id + '/file/'
        resp = self.get(url, timeout)
        return self.get_data_from_response(resp, 'application/zip')

    def get_plugin_job_zip_file(self, job_id: str, local_dir: str,
                                timeout: int = 1000):
        """
        Get and save a plugin job's zip file into a local directory.
        """
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)

        zip_content = self.get_plugin_job_zip_data(job_id, timeout)
        fpath = os.path.join(local_dir, job_id + '.zip')

        with open(fpath, 'wb') as f:
            f.write(zip_content)

    def get_plugin_job_files(self, job_id: str, local_dir: str, timeout: int = 1000):
        """
        Get a plugin job's output files unpacked within a local directory.
        """
        zip_content = self.get_plugin_job_zip_data(job_id, timeout)
        memory_zip_file = io.BytesIO(zip_content)

        with zipfile.ZipFile(memory_zip_file, 'r', zipfile.ZIP_DEFLATED) as job_data_zip:
            filenames = job_data_zip.namelist()
            print(f'Number of files to decompress at {local_dir}: {len(filenames)}')

            for fname in filenames:
                content = job_data_zip.read(fname)
                fpath = os.path.join(local_dir, fname.lstrip('/'))
                fpath_basedir = os.path.dirname(fpath)

                if not os.path.exists(fpath_basedir):
                    os.makedirs(fpath_basedir)

                with open(fpath, 'wb') as f:
                    f.write(content)

    def get_plugin_job_json_data(self, job_id: str, job_output_path: str,
                                 timeout: int = 1000) -> dict:
        """
        Get a plugin job's JSON file content. Only available when pfcon is in-network.
        """
        if self.pfcon_innetwork is None:
            self.get_server_info()

        if not self.pfcon_innetwork:
            raise PfconRequestException('JSON data is only available for PFCON server '
                                        'operating in-network')

        url_base = self._get_job_url_base_path(JobType.PLUGIN)
        url = self.url + url_base + job_id + '/file/?job_output_path=' + job_output_path
        resp = self.get(url, timeout)
        return self.get_data_from_response(resp)

    def get_plugin_job_json_file(self, job_id: str, job_output_path: str,
                                 local_dir: str, timeout: int = 1000):
        """
        Get and save a plugin job's JSON file into a local directory. Only available
        when pfcon is in-network.
        """
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)

        json_content = self.get_plugin_job_json_data(job_id, job_output_path, timeout)
        fpath = os.path.join(local_dir, job_id + '.json')

        with open(fpath, 'w') as f:
            json.dump(json_content, f)

    def delete_job(self, job_type: JobType, job_id: str, timeout: int = 1000):
        """
        Delete an existing job.
        """
        url_base = self._get_job_url_base_path(job_type)
        url = self.url + url_base + job_id + '/'
        resp = self.delete(url, timeout)

        if resp.status_code != 204:
            if resp.status_code == 401:
                raise PfconRequestInvalidTokenException(resp.text, code=resp.status_code)
            raise PfconRequestException(resp.text, code=resp.status_code)

    def get(self, url, timeout=30):
        """
        Make a GET request to pfcon.
        """
        try:
            r = requests.get(url,
                             headers={'Authorization': 'Bearer ' + self.auth_token},
                             timeout=timeout)
        except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
            raise PfconRequestException(str(e))
        return r

    def post(self, url, data, data_file=None, timeout=30):
        """
        Make a POST request to pfcon.
        """
        headers = {'Authorization': 'Bearer ' + self.auth_token}

        if data_file is not None:
            files = {'data_file': data_file}
        else:
            files = None

        try:
            r = requests.post(url, files=files, data=data,
                              headers=headers,
                              timeout=timeout)
        except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
            raise PfconRequestException(str(e))
        return r

    def delete(self, url, timeout=30):
        """
        Make a DELETE request to pfcon.
        """
        try:
            r = requests.delete(url,
                                headers={'Authorization': 'Bearer ' + self.auth_token},
                                timeout=timeout)
        except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
            raise PfconRequestException(str(e))
        return r

    def _get_job_url_base_path(self, job_type: JobType) -> str:
        """
        Get a job's url base path given the job type.
        """
        match job_type:
            case JobType.COPY:
                return 'copyjobs/'
            case JobType.PLUGIN:
                return 'pluginjobs/'
            case JobType.UPLOAD:
                return 'uploadjobs/'
            case JobType.DELETE:
                return 'deletejobs/'
            case _:
                raise ValueError(f'Unsupported job type: {job_type}')

    @staticmethod
    def get_auth_token(pfcon_auth_url, pfcon_user, pfcon_password, timeout=30):
        """
        Make a POST request to obtain an auth token.
        """
        try:
            r = requests.post(pfcon_auth_url,
                              json={'pfcon_user': pfcon_user,
                                    'pfcon_password': pfcon_password},
                              timeout=timeout)
        except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
            raise PfconRequestException(str(e))

        if r.status_code != 200:
            raise PfconRequestException(r.text, code=r.status_code)
        return r.json().get('token')

    @staticmethod
    def get_data_from_response(response, content_type='application/json'):
        """
        Static method to get the data dictionary from a response object.
        """
        if response.status_code not in (200, 201):
            if response.status_code == 401:
                raise PfconRequestInvalidTokenException(response.text,
                                                        code=response.status_code)
            raise PfconRequestException(response.text, code=response.status_code)

        if content_type == 'application/json':
            data = response.json()
        else:
            data = response.content
        return data

    @staticmethod
    def create_zip_file(local_dir: str) -> io.BytesIO:
        """
        Create job zip file ready for transmission to the remote from a local directory.
        """
        if not os.path.isdir(local_dir):
            raise ValueError(f'Invalid local input dir: {local_dir}')

        memory_zip_file = io.BytesIO()

        with zipfile.ZipFile(memory_zip_file, 'w', zipfile.ZIP_DEFLATED) as job_data_zip:
            for root, dirs, files in os.walk(local_dir):
                for filename in files:
                    local_file_path = os.path.join(root, filename)
                    arc_path = local_file_path.replace(local_dir, '', 1).lstrip('/')
                    job_data_zip.write(local_file_path, arcname=arc_path)

        memory_zip_file.seek(0)
        return memory_zip_file
