#!/usr/bin/python3
import os, sys
import subprocess
import argparse
from typing import Tuple

class CIKustomize(object):
    def __init__(self, service_name: str, environment: str, version: str) -> None:
        self.service_name = service_name
        self.environment = environment
        self.version = version
        
        self.build_dir = './build'
        self.artifacts_dir = f'{self.build_dir}/artifacts/{self.environment}'

    
    def run_cmd(self, cmd: str) -> Tuple[any, any]:
        p1 = subprocess.Popen(cmd.split(' '),
                              universal_newlines=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
        output, err = p1.communicate()
        
        return output, err


    def push(self) -> None:
        compressed_artifact = f'{self.build_dir}/{self.environment}.tgz'
        if not os.path.isfile(compressed_artifact):
            print(f'could not find {compressed_artifact}')
            sys.exit(1)
        
        out, err = self.run_cmd(f'aws s3 cp {compressed_artifact} s3://secrets.gyg.io/spinnaker/charts/{self.service_name}/{self.version}/{self.environment}/{self.environment}.tgz')
        if err:
            print(err)
            sys.exit(1)
        
        print(out)

    def build(self, path: str) -> None:
        _, _ = self.run_cmd(f'rm -Rf {self.build_dir}/{self.environment}')
        _, _ = self.run_cmd(f'mkdir -p {self.artifacts_dir}/templates/')

        _, err = self.run_cmd(f'kustomize build {path} -o {self.artifacts_dir}/templates/manifests.yml')
        if err:
            print(err)
            sys.exit(1)
        
        # write values.yml
        with open(f'{self.artifacts_dir}/values.yml', 'w') as v:
            values = f'''cluster: null
environment: {self.environment}
version: {self.version}
'''
            v.write(values)
        
        # write Chart.yml
        with open(f'{self.artifacts_dir}/Chart.yml', 'w') as c:
            values = f'name: {self.service_name}'
            c.write(values)
        
        # tar the artifacts to be pushed to s3
        _, _ = self.run_cmd(f'tar -czvf {self.build_dir}/{self.environment}.tgz -C {self.artifacts_dir}/ .')
        

if __name__ == '__main__':
    is_drone = os.getenv('DRONE', False)
    default_version = 'latest'
    if os.getenv('DRONE_BUILD_NUMBER') and os.getenv('DRONE_COMMIT_SHA'):   
        default_version = f'v{os.getenv("DRONE_BUILD_NUMBER")}.{os.getenv("DRONE_COMMIT_SHA")[0:7]}'
    
    parser = argparse.ArgumentParser(prog='ci-kustomize')
    parser.add_argument('--version', action='store', default=default_version)
    parser.add_argument('--service', action='store', default=os.getenv("DRONE_REPO_NAME", False))
    parser.add_argument('--push', action='store_true', default=is_drone)

    args = parser.parse_args()

    if not args.service:
        print('required: --service or DRONE_REPO_NAME')
        sys.exit(1)

    for environment in os.listdir('./overlays'):
        print(f'producing overlay artifact: {environment}')

        ci = CIKustomize(service_name=args.service, environment=environment, version=args.version)
        ci.build(path=f'overlays/{environment}')
        if args.push:
            ci.push()
