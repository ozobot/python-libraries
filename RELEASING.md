# Releasing
To release, create and push git tag in format `<project>-v<version>` or `<project>-v<version>-rc<release candidate>`. On tag push,
`publish.yml` workflow builds and uploads the artifacts to the package repository.

Releases get pushed to both PyPI and Test PyPI, while release candidates get pushed to Test PyPI only.

Example:
```
  git tag -a ozobot-ari-v0.0.0-rc1 -m "ari release rc1"
  git push origin ozobot-ari-v0.0.0-rc1
```
