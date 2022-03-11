import paramiko
import sys
from getpass import getpass

host = '10.81.120.155'
username = 'harshil'
password = getpass('Enter Password:')

results = []
def ssh_connect():
    session =paramiko.SSHClient()
    session.load_system_host_keys()

    session.connect(hostname=host,
                    username=username,
                    password=password)

    ssh_stdin, ssh_stdout, ssh_stderr = session.exec_command('ls')

    for line in ssh_stdout:
        results.append(line.strip('\n'))

ssh_connect()
for i in results:
    print(i.strip())

sys.exit()
