

import io
import json
from unittest import TestCase
from unittest import mock

from pfconclient import client


class ClientTests(TestCase):

    def setUp(self):
        self.pfcon_url = "http://localhost:5006/api/v1/"
        self.client = client.Client(self.pfcon_url)

    def test_submit_job(self):
        """
        Test whether submit_job method can successfully submit a job for execution.
        """
        pass

    def test_get_job_status(self):
        """
        Test whether get_job_status method can get the status of a job from pfcon.
        """
        #response = self.client.get_plugin_by_id(1)
        #self.assertEqual(response['id'], 1)
        pass
