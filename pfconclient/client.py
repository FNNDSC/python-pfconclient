"""
Pfcon API client module.
"""

from .request import Request
from .exceptions import PfconRequestException


class Client(object):
    """
    A pfcon API client.
    """

    def __init__(self, url, username=None, password=None, timeout=1000):
        self.url = url
        self.username = username
        self.password = password
        self.timeout = timeout
        self.content_type = 'application/json'

    def run_job(self, job_id, job_description, data_file):
        """
        Run a new job.
        """

    def submit_job(self, job_id, job_description, data_file):
        """
        Submit a new job.
        """
        data = {'name': name, 'dock_image': dock_image}
        collection = self.post(self.url, data, descriptor_file)
        result = self.get_data_from_collection(collection)
        return result['data'][0]

    def get_job_status(self, job_id):
        """
        Get a job's execution status.
        """

    def get_job_zip_file(self, job_id):
        """
        Get a job's zip data file.
        """

    def get_job_data(self, job_id, local_path):
        """
        Get a job's data unpacked within a local path.
        """

    def register_service_file(self, data):
        """
        Register a new PACS file with CUBE.
        """
        if not self.service_files_url: self.set_urls()
        req = Request(self.username, self.password, self.content_type, self.timeout)
        coll = req.post(self.service_files_url, data)
        result = req.get_data_from_collection(coll)
        return result['data'][0]
