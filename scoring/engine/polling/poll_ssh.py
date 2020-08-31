import time, timeout_decorator
from paramiko import client
from paramiko.ssh_exception import *
import socket

from .poller import PollInput, PollResult, Poller

class SshPollInput(PollInput):
    """
    A PollInput for the SshPoller.

    Attributes:
        task (str, optional): A Bash task to be performed on the target system.
        server (str, optional): IP address or FQDN of a service to poll
        port (int, optional): Port of the service to poll
    """
    def __init__(self, task=None, server=None, port=None):
        self.task = task
        super(SshPollInput, self).__init__(server, port)


class SshPollResult(PollResult):
    """
    A PollResult for the SshPoller.

    Attributes:
        authenticated (bool): Did the SshPoller authenticate successfully?
        output (str, optional): The output returned by the given PollInput task
        exception (Exception, optional): The Exception, if any, generated by the SshPoller
    """
    def __init__(self, authenticated, output=None, exception=None):
        super(SshPollResult, self).__init__(exception)
        self.authenticated = authenticated
        self.output = output


class SshPoller(Poller):
    """
    A Poller for the SSH service
    """

    @timeout_decorator.timeout(20, use_signals=False)
    def poll(self, poll_input):
        """
        Poll the SSH service.

        Arguments:
            poll_input (SshPollInput): The input to the SshPoller.

        Returns:
            SshPollResult: The result obtained by the poller.
        """
        username = poll_input.credentials.username
        password = poll_input.credentials.password

        try:
            # Set up the SSH client
            cli = client.SSHClient()
            cli.load_host_keys('/dev/null')
            cli.set_missing_host_key_policy(client.AutoAddPolicy())

            # Attempt to connect
            cli.connect(poll_input.server, poll_input.port, username, password)

            if poll_input.task is not None:
                # If there is a task to complete, execute it, and retrieve the output
                stdin, stdout, stderr = cli.exec_command(poll_input.task)
                out = stdout.read().decode('utf-8')
                err = stderr.read().decode('utf-8')
                output = (out, err)
                result = SshPollResult(True, output)
            else:
                # Otherwise authentication was successful
                result = SshPollResult(True)

            cli.close()
            return result
        except (Exception, socket.error) as e:
            # Authentication failed or some other error occurred.
            result = SshPollResult(False, exception=Exception(str(e)))
            return result
