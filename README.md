# Drone Plugin for Kustomize + Spinnaker

Drone plugin to build and deploy Kustomize manifests on Spinnaker.

## Dronefile

```yml
pipeline:
  build-artifacts:
    image: cainelli/drone-kustomize-plugin
    when:
      event: push
  deploy-artifacts:
    image: cainelli/drone-kustomize-plugin
    commands:
    - deploy
    when:
      event: push
      branch: master
```

## supported parameters


| Parameter             | Description                                                   | Example              |
|-----------------------|---------------------------------------------------------------|----------------------|
| ${parameters.cluster} | cluster name                                                  | frankfurt1, testing1 |
| ${parameters.version} | build version v$(DRONE_BUILD_NUMBER).$(DRONE_COMMIT_SHA[0:7]) | v617.47de901         |
| ${parameters.author}  | commit author                                                 | userX                |
| ${parameters.service} | repository name                                               | fishfarm             |


