# Releasing

`agent-spec-vault` publishes to PyPI from GitHub Actions using Trusted
Publishing. The release workflow builds a wheel and source distribution, smoke
tests the wheel, then uploads to PyPI when a version tag is pushed.

## One-Time PyPI Setup

Create a pending trusted publisher at:

```text
https://pypi.org/manage/account/publishing/
```

Use these values:

```text
PyPI project name: agent-spec-vault
Owner: xixifast
Repository name: agent-spec-vault
Workflow filename: publish-to-pypi.yml
Environment name: pypi
```

## Publish A Release

Update the version in `pyproject.toml` and `specv/__init__.py`, commit it, then
push a matching tag:

```bash
git tag v0.1.0
git push origin v0.1.0
```

After PyPI publishes the package, users should install it with:

```bash
pipx install agent-spec-vault
specv init
```
