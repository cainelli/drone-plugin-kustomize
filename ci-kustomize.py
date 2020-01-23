#!/usr/bin/python3
import os, sys
import json
import subprocess
import argparse
import requests

from typing import Tuple, List

DRONE_SECRET = 'dronesecret'
SPINNAKER_WEBHOOK_ENDPOINT = 'https://spin-gate.frankfurt1.gygkube.com/webhooks/webhook/drone'

class CIKustomize(object):
    def __init__(self, service_name: str, environment: str, version: str) -> None:
        self.service_name = service_name
        self.environment = environment
        self.version = version
        
        self.build_dir = './build'
        self.artifact = f'manifests-{self.environment}.yml'

    
    def run_cmd(self, cmd: str) -> Tuple[any, any]:
        print(f'running: {cmd}')

        p1 = subprocess.Popen(cmd.split(' '),
                              universal_newlines=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
        output, err = p1.communicate()
        
        return output, err


    def push(self) -> None:
        out, err = self.run_cmd(f'aws s3 cp {self.build_dir}/{self.artifact} s3://secrets.gyg.io/spinnaker/kustomize/{self.service_name}/{self.version}/manifests-{self.environment}.yml')
        if err:
            print(err)
            sys.exit(1)
        
        print(out)

    def build(self, path: str) -> None:
        _, _ = self.run_cmd(f'rm -Rf {self.build_dir}/{self.artifact}')
        _, _ = self.run_cmd(f'mkdir -p {self.build_dir}')

        cmd = f'kubectl kustomize {path}'
        out, err = self.run_cmd(cmd)
        if err:
            print(err)
            sys.exit(1)
        
        with open(f'{self.build_dir}/{self.artifact}', 'w') as f:
            f.write(out)

    def deploy(self) -> None:
        for cluster in self._get_clusters_by_environment(self.environment):
            payload = json.dumps({
                'application': self.service_name,
                'environment': self.environment,
                'secret': DRONE_SECRET,
                'engine': 'kustomize',
                'parameters': {
                    'cluster': cluster,
                    'version': self.version,
                    'author': os.getenv('DRONE_COMMIT_AUTHOR', 'unknown'),
                    'service': self.service_name,
                }
            })
        
            print(f'calling spinnaker webhook {payload}')
            res = requests.post(SPINNAKER_WEBHOOK_ENDPOINT, data=payload, headers={'Content-Type': 'application/json'})
            print(res.text)
    
    # TODO: Get it from an API, dss or k8s.
    def _get_clusters_by_environment(self, environment: str) -> List[str]:
        if environment == 'testing':
            return [(lambda x: f'testing{x}')(x) for x in range(1, 13)]
        elif environment == 'production':
            return [(lambda x: f'frankfurt{x}')(x) for x in range(1, 2)]

if __name__ == '__main__':
    is_drone = os.getenv('DRONE', False)
    default_version = 'latest'
    if os.getenv('DRONE_BUILD_NUMBER') and os.getenv('DRONE_COMMIT_SHA'):   
        default_version = f'v{os.getenv("DRONE_BUILD_NUMBER")}.{os.getenv("DRONE_COMMIT_SHA")[0:7]}'
    
    parser = argparse.ArgumentParser(prog='ci-kustomize')
    parser.add_argument('--version', action='store', default=default_version)
    parser.add_argument('--service', action='store', default=os.getenv("DRONE_REPO_NAME", False))
    args = parser.parse_args()

    if not args.service:
        print('required: --service or DRONE_REPO_NAME')
        sys.exit(1)

    for environment in os.listdir('./overlays'):
        ci = CIKustomize(service_name=args.service, environment=environment, version=args.version)
        print(f'producing overlay artifact: {environment}')
        ci.build(path=f'./overlays/{environment}/')
        ci.push()        
        ci.deploy()
