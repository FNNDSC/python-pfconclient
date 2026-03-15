
import io
import os
import shutil
import zipfile
import random
from unittest import TestCase
from unittest import mock

from pfconclient import client
from pfconclient.client import JobType


class ClientTests(TestCase):

    def setUp(self):
        self.pfcon_url = "http://localhost:30006/api/v1/"
        self.pfcon_user = 'pfcon'
        self.pfcon_password = 'pfcon1234'
        self.pfcon_auth_url = self.pfcon_url + 'auth-token/'

        self.copy_job_descriptors = {
            'input_dirs': ['home/user/cube'],
            'output_dir': 'home/user/cube_out',
        }

        self.plugin_job_descriptors = {
            'entrypoint': ['python3', '/usr/local/bin/simpledsapp'],
            'args': ['--prefix', 'le'],
            'auid': 'cube',
            'number_of_workers': 1,
            'cpu_limit': 1000,
            'memory_limit': 200,
            'gpu_limit': 0,
            'image': 'fnndsc/pl-simpledsapp',
            'type': 'ds',
            'input_dirs': ['home/user/cube'],
            'output_dir': 'home/user/cube_out',
        }

        self.upload_job_descriptors = {
            'job_output_path': 'home/user/cube_out',
        }

        self.delete_job_descriptors = {}

    # ------------------------------------------------------------------ #
    # Unit tests
    # ------------------------------------------------------------------ #

    def test_submit_copy_job(self):
        """
        Test whether submit_job for a copy job makes the appropriate request.
        """
        response_mock = mock.Mock()
        response_mock.status_code = 201
        response_mock.json = mock.Mock(return_value={'compute': {'status': 'notStarted'}})
        with mock.patch.object(client.requests, 'post',
                               return_value=response_mock) as post_mock:
            job_id = 'chris-jid-1'
            cl = client.Client(self.pfcon_url, 'a@token')

            expected_data = self.copy_job_descriptors.copy()
            expected_data['jid'] = job_id

            cl.submit_job(JobType.COPY, job_id, self.copy_job_descriptors.copy())

            post_mock.assert_called_with(
                self.pfcon_url + 'copyjobs/',
                files=None,
                data=expected_data,
                headers={'Authorization': 'Bearer a@token'},
                timeout=1000,
            )

    def test_submit_plugin_job(self):
        """
        Test whether submit_job for a plugin job makes the appropriate request.
        """
        response_mock = mock.Mock()
        response_mock.status_code = 201
        response_mock.json = mock.Mock(return_value={'data': {}, 'compute': {'status': 'notStarted'}})
        with mock.patch.object(client.requests, 'post',
                               return_value=response_mock) as post_mock:
            job_id = 'chris-jid-1'
            cl = client.Client(self.pfcon_url, 'a@token')

            expected_data = self.plugin_job_descriptors.copy()
            expected_data['jid'] = job_id

            cl.submit_job(JobType.PLUGIN, job_id, self.plugin_job_descriptors.copy())

            post_mock.assert_called_with(
                self.pfcon_url + 'pluginjobs/',
                files=None,
                data=expected_data,
                headers={'Authorization': 'Bearer a@token'},
                timeout=1000,
            )

    def test_submit_upload_job(self):
        """
        Test whether submit_job for an upload job makes the appropriate request.
        """
        response_mock = mock.Mock()
        response_mock.status_code = 201
        response_mock.json = mock.Mock(return_value={'compute': {'status': 'finishedSuccessfully'}})
        with mock.patch.object(client.requests, 'post',
                               return_value=response_mock) as post_mock:
            job_id = 'chris-jid-1'
            cl = client.Client(self.pfcon_url, 'a@token')

            expected_data = self.upload_job_descriptors.copy()
            expected_data['jid'] = job_id

            cl.submit_job(JobType.UPLOAD, job_id, self.upload_job_descriptors.copy())

            post_mock.assert_called_with(
                self.pfcon_url + 'uploadjobs/',
                files=None,
                data=expected_data,
                headers={'Authorization': 'Bearer a@token'},
                timeout=1000,
            )

    def test_submit_delete_job(self):
        """
        Test whether submit_job for a delete job makes the appropriate request.
        """
        response_mock = mock.Mock()
        response_mock.status_code = 201
        response_mock.json = mock.Mock(return_value={'compute': {'status': 'notStarted'}})
        with mock.patch.object(client.requests, 'post',
                               return_value=response_mock) as post_mock:
            job_id = 'chris-jid-1'
            cl = client.Client(self.pfcon_url, 'a@token')

            expected_data = self.delete_job_descriptors.copy()
            expected_data['jid'] = job_id

            cl.submit_job(JobType.DELETE, job_id, self.delete_job_descriptors.copy())

            post_mock.assert_called_with(
                self.pfcon_url + 'deletejobs/',
                files=None,
                data=expected_data,
                headers={'Authorization': 'Bearer a@token'},
                timeout=1000,
            )

    def test_get_job_status(self):
        """
        Test whether get_job_status makes the appropriate request for each job type.
        """
        for job_type, url_segment in [
            (JobType.COPY, 'copyjobs'),
            (JobType.PLUGIN, 'pluginjobs'),
            (JobType.UPLOAD, 'uploadjobs'),
            (JobType.DELETE, 'deletejobs'),
        ]:
            response_mock = mock.Mock()
            response_mock.status_code = 200
            response_mock.json = mock.Mock(return_value={'compute': {'status': 'started'}})
            with mock.patch.object(client.requests, 'get',
                                   return_value=response_mock) as get_mock:
                job_id = 'chris-jid-1'
                cl = client.Client(self.pfcon_url, 'a@token')
                cl.get_job_status(job_type, job_id)

                url = self.pfcon_url + url_segment + '/' + job_id + '/'
                get_mock.assert_called_with(
                    url,
                    headers={'Authorization': 'Bearer a@token'},
                    timeout=1000,
                )

    def test_get_plugin_job_json_data(self):
        """
        Test whether get_plugin_job_json_data makes the appropriate request.
        """
        response_mock = mock.Mock()
        response_mock.status_code = 200
        response_mock.json = mock.Mock(return_value={
            'job_output_path': 'home/user/cube_out',
            'rel_file_paths': ['output.txt'],
        })
        with mock.patch.object(client.requests, 'get',
                               return_value=response_mock) as get_mock:
            job_id = 'chris-jid-1'
            output_path = 'home/user/cube_out'
            cl = client.Client(self.pfcon_url, 'a@token')
            cl.pfcon_innetwork = True
            resp = cl.get_plugin_job_json_data(job_id, output_path)

            url = self.pfcon_url + 'pluginjobs/' + job_id + '/file/?job_output_path=' + output_path
            get_mock.assert_called_with(
                url,
                headers={'Authorization': 'Bearer a@token'},
                timeout=1000,
            )
            self.assertIn('rel_file_paths', resp)

    def test_submit_plugin_job_with_zip(self):
        """
        Test whether submit_job sends a multipart request when a data_file is provided
        (not in-network legacy mode).
        """
        zip_file = io.BytesIO()
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('test.txt', 'Test file')
        zip_file.seek(0)
        zip_content = zip_file.getvalue()

        response_mock = mock.Mock()
        response_mock.status_code = 201
        response_mock.json = mock.Mock(return_value={'data': {}, 'compute': {'status': 'notStarted'}})
        with mock.patch.object(client.requests, 'post',
                               return_value=response_mock) as post_mock:
            job_id = 'chris-jid-1'
            cl = client.Client(self.pfcon_url, 'a@token')

            descriptors = self.plugin_job_descriptors.copy()
            expected_data = descriptors.copy()
            expected_data['jid'] = job_id

            cl.submit_job(JobType.PLUGIN, job_id, descriptors, zip_content)

            post_mock.assert_called_with(
                self.pfcon_url + 'pluginjobs/',
                files={'data_file': zip_content},
                data=expected_data,
                headers={'Authorization': 'Bearer a@token'},
                timeout=1000,
            )

    def test_get_plugin_job_zip_data(self):
        """
        Test whether get_plugin_job_zip_data makes the appropriate request.
        """
        response_mock = mock.Mock()
        response_mock.status_code = 200
        response_mock.content = b'zip file content'
        with mock.patch.object(client.requests, 'get',
                               return_value=response_mock) as get_mock:
            job_id = 'chris-jid-1'
            cl = client.Client(self.pfcon_url, 'a@token')
            resp_data = cl.get_plugin_job_zip_data(job_id)

            self.assertEqual(resp_data, response_mock.content)
            url = self.pfcon_url + 'pluginjobs/' + job_id + '/file/'
            get_mock.assert_called_with(
                url,
                headers={'Authorization': 'Bearer a@token'},
                timeout=1000,
            )

    def test_delete_job(self):
        """
        Test whether delete_job makes the appropriate DELETE request for each job type.
        """
        for job_type, url_segment in [
            (JobType.COPY, 'copyjobs'),
            (JobType.PLUGIN, 'pluginjobs'),
            (JobType.UPLOAD, 'uploadjobs'),
            (JobType.DELETE, 'deletejobs'),
        ]:
            response_mock = mock.Mock()
            response_mock.status_code = 204
            with mock.patch.object(client.requests, 'delete',
                                   return_value=response_mock) as delete_mock:
                job_id = 'chris-jid-1'
                cl = client.Client(self.pfcon_url, 'a@token')
                cl.delete_job(job_type, job_id)

                url = self.pfcon_url + url_segment + '/' + job_id + '/'
                delete_mock.assert_called_with(
                    url,
                    headers={'Authorization': 'Bearer a@token'},
                    timeout=1000,
                )

    # ------------------------------------------------------------------ #
    # Integration / end-to-end tests
    # ------------------------------------------------------------------ #

    def test_integration_get_server_info(self):
        """
        Test whether the get_server_info method returns expected server info from pfcon.
        """
        auth_token = client.Client.get_auth_token(self.pfcon_auth_url, self.pfcon_user,
                                                  self.pfcon_password)
        cl = client.Client(self.pfcon_url, auth_token)
        resp_data = cl.get_server_info()
        self.assertIn('server_version', resp_data)

    def test_integration_full_fslink_flow(self):
        """
        End-to-end test of the full fslink flow: copy -> plugin -> file metadata ->
        upload (no-op) -> delete -> remove containers.
        """
        job_id = 'chris-jid-%s' % random.randint(10**3, 10**7)
        output_dir = 'home/user/cube_out/' + job_id

        # Set up test data and output directory on the shared filesystem.
        # tests/test_client.py -> repo root is 2 levels up, pfcon_fork is a sibling
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        storebase = os.environ.get(
            'STOREBASE',
            os.path.join(repo_root, '..', 'pfcon_fork', 'CHRIS_REMOTE_FS'),
        )
        storebase = os.path.abspath(storebase)

        # Create input test data
        input_abs = os.path.join(storebase, 'home', 'user', 'cube')
        test_dir = os.path.join(input_abs, 'test')
        os.makedirs(test_dir, exist_ok=True)

        test_file = os.path.join(test_dir, 'test_file.txt')
        if not os.path.exists(test_file):
            with open(test_file, 'w') as f:
                f.write('test file')

        chrislink = os.path.join(input_abs, 'test.chrislink')
        if not os.path.exists(chrislink):
            with open(chrislink, 'w') as f:
                f.write('home/user/cube/test')

        # Create a fresh output directory (required in fslink mode)
        output_abs = os.path.join(storebase, output_dir)
        os.makedirs(output_abs, exist_ok=True)

        auth_token = client.Client.get_auth_token(self.pfcon_auth_url, self.pfcon_user,
                                                  self.pfcon_password)
        cl = client.Client(self.pfcon_url, auth_token)
        cl.max_wait = 2 ** 6

        try:
            # Step 1: Submit copy job
            copy_descriptors = {
                'input_dirs': ['home/user/cube'],
                'output_dir': output_dir,
            }
            resp = cl.submit_job(JobType.COPY, job_id, copy_descriptors)
            self.assertIn('compute', resp)
            self.assertEqual(resp['compute']['jid'], job_id)

            # Step 2: Poll copy status
            status = cl.poll_job_status(JobType.COPY, job_id)
            self.assertEqual(status, 'finishedSuccessfully')

            # Step 3: Submit plugin job
            plugin_descriptors = {
                'entrypoint': ['python3', '/usr/local/bin/simpledsapp'],
                'args': ['--prefix', 'le'],
                'auid': 'cube',
                'number_of_workers': 1,
                'cpu_limit': 1000,
                'memory_limit': 200,
                'gpu_limit': 0,
                'image': 'fnndsc/pl-simpledsapp',
                'type': 'ds',
                'input_dirs': ['home/user/cube'],
                'output_dir': output_dir,
            }
            resp = cl.submit_job(JobType.PLUGIN, job_id, plugin_descriptors)
            self.assertIn('compute', resp)

            # Step 4: Poll plugin status
            status = cl.poll_job_status(JobType.PLUGIN, job_id)
            self.assertEqual(status, 'finishedSuccessfully')

            # Step 5: Get output file metadata
            cl.get_server_info()
            resp = cl.get_plugin_job_json_data(job_id, output_dir)
            self.assertIn('rel_file_paths', resp)
            self.assertTrue(len(resp['rel_file_paths']) > 0)

            # Step 6: Submit upload job (no-op for fslink)
            upload_descriptors = {
                'job_output_path': output_dir,
            }
            resp = cl.submit_job(JobType.UPLOAD, job_id, upload_descriptors)
            self.assertIn('compute', resp)
            self.assertEqual(resp['compute']['status'], 'finishedSuccessfully')
            self.assertEqual(resp['compute']['message'], 'uploadSkipped')

            # Step 7: Submit delete job
            resp = cl.submit_job(JobType.DELETE, job_id, {})
            self.assertIn('compute', resp)

            # Step 8: Poll delete status
            status = cl.poll_job_status(JobType.DELETE, job_id)
            self.assertEqual(status, 'finishedSuccessfully')

            # Step 9: Remove all containers
            cl.delete_job(JobType.COPY, job_id)
            cl.delete_job(JobType.PLUGIN, job_id)
            cl.delete_job(JobType.DELETE, job_id)
        finally:
            # Clean up the output directory
            if os.path.isdir(output_abs):
                shutil.rmtree(output_abs)
