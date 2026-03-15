#!/usr/bin/env python3
#
# (c) 2017-2025 Fetal-Neonatal Neuroimaging & Developmental Science Center
#                   Boston Children's Hospital
#
#              http://childrenshospital.org/FNNDSC/
#                        dev@babyMRI.org
#

from argparse import ArgumentParser

from .client import Client, JobType


parser = ArgumentParser(description='Manage pfcon service resources')
parser.add_argument('url', help="url of pfcon service")
parser.add_argument('-a', '--auth_token', help="authorization token for pfcon service")
parser.add_argument('-t', '--timeout', help="requests' timeout")
subparsers = parser.add_subparsers(dest='subparser_name', title='subcommands',
                                   description='valid subcommands',
                                   help='sub-command help')

# create the parser for the "auth" command
parser_auth = subparsers.add_parser('auth', help='get an auth token')
parser_auth.add_argument('--pfcon_user', help="pfcon user", required=True)
parser_auth.add_argument('--pfcon_password', help="pfcon user's password", required=True)

# create the parser for the "submit" command
parser_submit = subparsers.add_parser('submit', help='submit a new job')
parser_submit.add_argument('--job_type', choices=['copy', 'plugin', 'upload', 'delete'],
                           required=True, help='type of job to submit')
parser_submit.add_argument('--jid', help="job id", required=True)
parser_submit.add_argument('--input_dirs', nargs='+',
                           help='input directories (repeatable)')
parser_submit.add_argument('--output_dir', help='output directory')
parser_submit.add_argument('--job_output_path', help='job output path (for upload jobs)')
submit_plugin_group = parser_submit.add_argument_group('plugin job parameters')
submit_plugin_group.add_argument('--entrypoint', nargs='+',
                                 help='entrypoint command parts (e.g. python3 /usr/local/bin/simplefsapp)')
submit_plugin_group.add_argument('--args', nargs='+', help='cmd arguments')
submit_plugin_group.add_argument('--auid', help='user id')
submit_plugin_group.add_argument('--number_of_workers', help='number of workers')
submit_plugin_group.add_argument('--cpu_limit', help='cpu limit')
submit_plugin_group.add_argument('--memory_limit', help='memory limit')
submit_plugin_group.add_argument('--gpu_limit', help='gpu limit')
submit_plugin_group.add_argument('--image', help='docker image')
submit_plugin_group.add_argument('--type', help='plugin type', choices=['fs', 'ds', 'ts'])

# create the parser for the "status" command
parser_status = subparsers.add_parser('status', help='get the exec status of a job')
parser_status.add_argument('--job_type', choices=['copy', 'plugin', 'upload', 'delete'],
                           required=True, help='type of job')
parser_status.add_argument('--jid', help="job id", required=True)

# create the parser for the "poll" command
parser_poll = subparsers.add_parser('poll',
                                    help='poll the exec status of a job until finished')
parser_poll.add_argument('--job_type', choices=['copy', 'plugin', 'upload', 'delete'],
                         required=True, help='type of job')
parser_poll.add_argument('--jid', help="job id", required=True)
parser_poll.add_argument('--poll_initial_wait',
                         help='initial wait time in seconds to poll for job status')
parser_poll.add_argument('--poll_max_wait',
                         help='maximum wait time in seconds to poll for job status')

# create the parser for the "delete" command
parser_delete = subparsers.add_parser('delete', help='delete an existing job')
parser_delete.add_argument('--job_type', choices=['copy', 'plugin', 'upload', 'delete'],
                           required=True, help='type of job')
parser_delete.add_argument('--jid', help="job id", required=True)


def main():
    # parse the arguments and perform the appropriate action with the client
    args = parser.parse_args()
    timeout = args.timeout or 1000

    if args.subparser_name == 'auth':
        auth_url = args.url + 'auth-token/'
        token = Client.get_auth_token(auth_url, args.pfcon_user, args.pfcon_password)
        print(f'\ntoken: {token}\n')
    else:
        cl = Client(args.url, args.auth_token)

        if args.subparser_name == 'submit':
            job_type = JobType(args.job_type)
            d_job_descriptors = {}

            if args.input_dirs:
                d_job_descriptors['input_dirs'] = args.input_dirs
            if args.output_dir:
                d_job_descriptors['output_dir'] = args.output_dir
            if args.job_output_path:
                d_job_descriptors['job_output_path'] = args.job_output_path
            if args.entrypoint:
                d_job_descriptors['entrypoint'] = args.entrypoint
            if args.args:
                d_job_descriptors['args'] = args.args
            if args.auid:
                d_job_descriptors['auid'] = args.auid
            if args.number_of_workers:
                d_job_descriptors['number_of_workers'] = args.number_of_workers
            if args.cpu_limit:
                d_job_descriptors['cpu_limit'] = args.cpu_limit
            if args.memory_limit:
                d_job_descriptors['memory_limit'] = args.memory_limit
            if args.gpu_limit:
                d_job_descriptors['gpu_limit'] = args.gpu_limit
            if args.image:
                d_job_descriptors['image'] = args.image
            if args.type:
                d_job_descriptors['type'] = args.type

            resp_data = cl.submit_job(job_type, args.jid, d_job_descriptors, timeout)
            print(f'\n{resp_data}\n')

        elif args.subparser_name == 'status':
            job_type = JobType(args.job_type)
            d_resp = cl.get_job_status(job_type, args.jid, timeout)
            status = d_resp['compute']['status']
            print('\nJob %s status: %s' % (args.jid, status))

        elif args.subparser_name == 'poll':
            job_type = JobType(args.job_type)
            if args.poll_initial_wait:
                cl.initial_wait = args.poll_initial_wait
            if args.poll_max_wait:
                cl.max_wait = args.poll_max_wait
            cl.poll_job_status(job_type, args.jid, timeout)

        elif args.subparser_name == 'delete':
            job_type = JobType(args.job_type)
            cl.delete_job(job_type, args.jid, timeout)
            print('\nDeleted job %s' % args.jid)


if __name__ == "__main__":
    main()
