# GitHub Actions Workflows

This directory contains automated workflows for CI/CD and release management.

## Workflows

### `tests.yml`
Runs the test suite with code coverage on every push and pull request.

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

**Actions:**
- Sets up Python 3.10
- Installs dependencies from `requirements.txt`
- Runs `pytest tests --cov=src`
- Uploads coverage reports to Codecov

**Status Badge:**
Add to README: `![Tests](https://github.com/OWNER/REPO/actions/workflows/tests.yml/badge.svg)`

### `changelog.yml`
Automatically generates changelog entries based on [conventional commits](./COMMIT_CONVENTION.md).

**Triggers:**
- Push of version tags (e.g., `v1.0.0`)
- Manual trigger via `workflow_dispatch`

**Actions:**
- Uses `conventional-changelog-cli` to parse commit history
- Generates `CHANGELOG.md` grouped by type (feat, fix, docs, etc.)
- Creates GitHub Release with changelog as release notes
- Commits updates back to repository

**Usage:**

1. **Automatic (on tag push):**
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```
   The workflow will automatically generate the changelog and create a GitHub Release.

2. **Manual:**
   - Go to **Actions** → **Generate Changelog**
   - Click **Run workflow**
   - Select branch and click **Run workflow**
   - Download the generated `CHANGELOG.md` artifact

## Conventional Commits

To ensure proper changelog generation, follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

See [COMMIT_CONVENTION.md](./COMMIT_CONVENTION.md) for detailed guidelines and examples.

## Common Types

- `feat`: New feature (→ MINOR version bump)
- `fix`: Bug fix (→ PATCH version bump)
- `feat!`: Breaking change (→ MAJOR version bump)
- `docs`: Documentation updates
- `refactor`: Code restructuring
- `test`: Test additions/fixes
- `chore`: Dependency/tooling updates

## Examples

```bash
# Bug fix
git commit -m "fix(models): handle None mesh correctly"

# New feature
git commit -m "feat(api): add gap-based calculation"

# Breaking change
git commit -m "feat(api)!: change mesh parameter format

BREAKING CHANGE: API now accepts single mesh instead of horizon_mesh/zenith_mesh"
```

## Configuration

### Python Version
Edit `tests.yml` to test against multiple Python versions:
```yaml
python-version: ["3.9", "3.10", "3.11"]
```

### Branches
Edit `tests.yml` and `changelog.yml` to change which branches trigger workflows:
```yaml
branches:
  - main
  - production
```

### Release Tags
Edit `changelog.yml` to match your version tag format:
```yaml
tags:
  - 'v*.*.*'
  - 'release-*'
```

## Troubleshooting

### Changelog generation fails
- Ensure branch has clean git history
- Check that commits follow conventional commits format
- Review logs in Actions tab

### Coverage upload fails
- Codecov token may need to be added to repository secrets
- Or disable codecov step if not needed

### Tests fail on PR
- Review test output in Actions tab
- Fix failing tests before merging
- Can also run locally: `pytest tests --cov=src`

## Future Improvements

- [ ] Auto-bump version in `src/__version__.py`
- [ ] Publish to PyPI on release
- [ ] Docker image build and push
- [ ] Code quality checks (linting, type checking)
- [ ] Security scanning
