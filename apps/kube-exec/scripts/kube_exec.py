from os import environ as env

from kubernetes import client, config
from kubernetes.stream import stream

config.load_incluster_config()
api = client.CoreV1Api()

response = api.list_namespaced_pod(namespace=env["NAMESPACE"],
                                   label_selector=env["LABEL"])

for pod in response.items:
    name = pod.metadata.name
    exec_command = ["/bin/sh", "-c", env["COMMAND"]]
    response = stream(
        api.connect_get_namespaced_pod_exec,
        name,
        env["NAMESPACE"],
        command=exec_command,
        stderr=True,
        stdin=False,
        stdout=True,
        tty=False,
        _preload_content=False,
    )

    while response.is_open():
        response.update(timeout=1)
        if response.peek_stdout():
            print(response.read_stdout())
        if response.peek_stderr():
            print(response.read_stderr())
