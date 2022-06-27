from os import environ as env

import urllib3
from kubernetes import config
from kubernetes.client import Configuration
from kubernetes.client.apis import core_v1_api
from kubernetes.stream import stream

config.load_incluster_config()

config_client = Configuration()
config_client.verify_ssl = False
# config_client.assert_hostname = False
urllib3.disable_warnings()
Configuration.set_default(config_client)

api = core_v1_api.CoreV1Api()

response = api.list_namespaced_pod(namespace=env["NAMESPACE"],
                                   label_selector=env["LABEL"])

for x in response.items:
    name = x.spec.hostname

    response = api.read_namespaced_pod(name=name, namespace=env["NAMESPACE"])

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
    )

    print("=== kube-exec %s: ===\n%s\n" %
          (name, response if response else "<no output>"))
