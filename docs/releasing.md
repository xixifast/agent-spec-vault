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

Update the version in `pyproject.toml` and `specv/__init__.py`, run tests and
metadata checks, commit it, then push a matching tag:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
git tag v<version>
git push origin v<version>
```

After PyPI publishes the package, users should install it with:

```bash
python3 -m pip install agent-spec-vault
specv init
```

`pipx install agent-spec-vault` is also a good option for users who want an
isolated CLI install.
