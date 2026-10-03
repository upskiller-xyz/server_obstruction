# Changelog

All notable changes to this project will be documented in this file.

## [1.0.5] - 2026-10-03
### CI/CD

- *(release)* Deploy the tagged image to the Scaleway container (#54)
- *(changelog)* Generate with git-cliff instead of conventional-changelog (#55)


## [1.0.4] - 2026-10-03
### Bug Fixes

- Adjust changelog workflow (#43)
- Set logging options (#46)
- Bump packages (#47)
- Patch (#48)
- Return full sky instead of fully obstructed when no geometry remains (#52)

### CI/CD

- Add workflows for GCP container building (#45)

### Miscellaneous

- *(deps)* Bump actions/setup-python from 4 to 6 (#39)
- *(deps)* Bump actions/setup-node from 6 to 7 (#44)
- *(deps)* Bump actions/setup-python from 6 to 7 (#49)

### Security

- Gunicorn CVE, no error leakage, 256 MiB body limit, non-root (#51)


## [1.0.3] - 2026-07-05
### Features

- Add chunk size as envvar (#42)


## [1.0.2] - 2026-07-05
### Features

- Faster obstruction calculation (#41)


## [1.0.1] - 2026-07-04
### Bug Fixes

- Serverless container deployment (#40)


## [1.0.0] - 2026-06-21
### Bug Fixes

- Edit deployment files
- Improve Python version handling and add Docker deployment
- Add route debugging and logging for troubleshooting
- Only stop application's own containers during deployment
- Refactor; fix: speed up the calculation
- Issues in obstruction calculation; chore: refactor
- Counting only closeby horizontal surfaces for zenith angle
- Solve the case when closer obstructions were neglected; chore: set regulation-based min and max buffer for both horizon and zenith calculations
- Add missing package; heighten the min/max borders
- Parallel request
- Lambda
- Using less workers and more cores
- Simplify surface filters by removing pre-distance filtering
- Update validators to accept nested mesh format {horizon, zenith}
- Rename zenith_angle and horizon_angle back to horizon and zenith
- Make debug logging to env var
- Minor fixes
- Minor fixes
- *(GeometryValidator)* Fixes a false-positive mesh hit on triangles with barycentric coordinates
- Postfix
- Postfix och concurrency (#23)
- Immutable tag (#24)
- Dependabot och hard tags (#25)
- Orjson for mesh parsing (#30)
- Test flow and failing stale tests (#34)

### Documentation

- Finalize demo.ipynb
- Update readme
- Update demo
- Add master branch integration summary

### Features

- Implement horizon angle calculation
- Add obstruction calculation (both angles in one endpoint)
- Add mesh sorting and filtering; change input parameter to direction_angle instead of two directions of a unit vector; docs: add uml; fix: correct visualization utils
- Optimize obstruction calculation to under 1 sec
- Add VM deployment files and documentation
- Add comprehensive debug logging support
- Add parallel calculation
- Add worker/thread configuration to deployment files
- Update .env.docker with worker configuration
- Early stopping
- Add zenith early stopping
- Add zenith early stopping
- Vectorize window on mesh validation
- Add debug env var
- Add endpoint format support with reference point calculation
- Accept split horizon_mesh + zenith_mesh input
- Gap-based unified obstruction calculator
- Accept flat mesh list format in ObstructionRequest
- Add VectorizedElevationAngleCollector for batch plane-triangle intersection
- Wire VectorizedElevationAngleCollector into gap-based pipeline
- Hoist height filter to service layer and pack triangle arrays once
- Replace ProcessPoolExecutor with ThreadPoolExecutor

### Miscellaneous

- Refactored obstruction_calculators
- Add parallel request to the notebook
- Update the docs and the ops
- Remove unnecessary
- Add dev notebook; feat: add obstruction visualization
- Modify tests
- Version after the breaking change
- Refactor; add fastapi docs
- Refactor according to SRP
- Bring the input parameters back to single mesh; feat: add testing and changelog CICD
- Pr fixes; restore unstable version
- Add .claudeignore to protect secrets from Claude Code
- Add cicd
- *(deps)* Bump actions/checkout from 4 to 7 (#35)
- *(deps)* Bump actions/upload-artifact from 3 to 7 (#29)
- *(deps)* Bump codecov/codecov-action from 3 to 7 (#26)
- *(deps)* Bump actions/setup-node from 3 to 6 (#27)

### Performance

- Increase workers and threads for parallel processing
- Vectorize zenith filter and optimize array construction
- Optimize obstruction calculations with combined filtering
- Increase worker count for better parallel processing
- Optimise array packning (#32)

### Refactoring

- Use nested mesh format {horizon, zenith} in request parsing
- Replace magic strings with ANGLES enum members



