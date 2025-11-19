<a name="readme-top"></a>

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]



<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/upskiller-xyz/server_obstruction">
    <img src="https://github.com/upskiller-xyz/DaylightFactor/blob/main/docs/images/logo_upskiller.png" alt="Logo" height="100" >
  </a>

  <h3 align="center">Obstruction Server</h3>

  <p align="center">
    Calculate horizon and zenith obstruction angles from 3D mesh geometry
    <br />
    <a href="https://github.com/upskiller-xyz/server_obstruction">View Demo</a>
    ·
    <a href="https://github.com/upskiller-xyz/server_obstruction/issues">Report Bug</a>
    ·
    <a href="https://github.com/upskiller-xyz/server_obstruction/issues">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a>
        <li><a href="#api-endpoints">API Endpoints</a></li>
        <li><a href="#deployment">Deployment</a>
          <li><a href="#locally">Local deployment</a></li>
        </li>
    </li>
    <li><a href="#design">Design</a>
      <li><a href="#architecture">Architecture</a></li>
    </li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contribution">Contribution</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#attribution">Attribution</a></li>
    <li><a href="#trademark-notice">Trademark notice</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

Server for calculating obstruction angles (horizon and zenith) from 3D mesh geometry using plane-triangle intersection algorithms.



<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Built With

* [Python](https://www.python.org/)
* [Flask](https://flask.palletsprojects.com/)
* [NumPy](https://numpy.org/)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->
## Getting Started

To get a local copy up and running follow these simple steps.

### Prerequisites

* [Python 3.13+](https://www.python.org/downloads/)
* [Poetry](https://python-poetry.org/docs/#installation)

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/upskiller-xyz/server_obstruction.git
   cd server_obstruction
   ```

2. Install dependencies using Poetry:
   ```sh
   poetry install
   ```

3. Activate the virtual environment:
   ```sh
   poetry shell
   ```

4. Set environment variables (optional):
   ```sh
   export PORT=8081               # Server port
   ```

5. Run the server:
   ```sh
   python -m src.main
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- USAGE EXAMPLES -->
## Usage

### 📚 Documentation

- **[Coordinate System & Calculations](docs/coordinate_system_and_calculations.md)** - Detailed explanation of the 3D coordinate system, viewing directions, and obstruction angle calculation methodology
- **[API Reference](docs/api.md)** - REST API endpoints and request/response formats

### 🎯 Interactive Demo

**Start here!** For hands-on examples and visualizations, see the **[Playground Notebook](example/demo.ipynb)**:

```bash
# Install Jupyter and start the demo
poetry run jupyter notebook example/demo.ipynb
```

### 🔧 API Endpoints

The server provides REST API endpoints for horizon and zenith angle calculations:

#### Health Check
Check if the server is running:

```python
import requests

response = requests.get("http://localhost:8081/")
print(response.json())
# Output: {"status": "ready", "timestamp": "2025-01-01T00:00:00Z"}
```

#### Obstruction Calculation (Both Angles)
Calculate both horizon and zenith angles in a single request:

```python
import requests

payload = {
    "x": 0.0,
    "y": 3.0,
    "z": 0.0,
    "direction_angle": 0.0,  # Horizontal viewing direction in radians
    "mesh": [                # Triangle mesh vertices (groups of 3)
        [10.0, 0.0, -5.0],
        [10.0, 5.0, -5.0],
        [10.0, 0.0, 5.0],
        [10.0, 0.0, 5.0],
        [10.0, 5.0, -5.0],
        [10.0, 5.0, 5.0]
    ]
}

response = requests.post("http://localhost:8081/obstruction", json=payload)
result = response.json()
print(f"Horizon: {result['data']['horizon']['obstruction_angle_degrees']:.2f}°")
print(f"Zenith: {result['data']['zenith']['obstruction_angle_degrees']:.2f}°")
```

#### Parallel Multi-Direction Obstruction Calculation
Calculate obstruction angles for 64 directions in parallel using HTTP requests to a microservice:

```python
import requests

payload = {
    "x": 0.0,
    "y": 0.0,
    "z": 1.5,
    "mesh": [                # Triangle mesh vertices (groups of 3)
        [5.0, -5.0, 0.0],
        [5.0, 5.0, 0.0],
        [5.0, -5.0, 3.0],
        # ... more vertices
    ],

    # Microservice URL to call in parallel
    "microservice_url": "http://your-service.run.app/obstruction",

    # Optional: GCP authentication token
    "auth_token": "your-gcp-bearer-token",

    # Optional: Customize direction sampling (defaults shown)
    "num_directions": 64,
    "start_angle_degrees": 17.5,
    "end_angle_degrees": 162.5
}

response = requests.post("http://localhost:8081/obstruction_parallel", json=payload)
result = response.json()

if result['status'] == 'success':
    data = result['data']
    print(f"Calculated {data['num_directions']} directions in {data['total_time_seconds']:.2f}s")
    print(f"Horizon angles: {data['horizon_angles']}")
    print(f"Zenith angles: {data['zenith_angles']}")
```

**Example Script**: See [parallel_request_example.py](example/parallel_request_example.py) for a complete working example.

#### GCP Deployment Recommendations for Parallel Execution

When deploying on Google Cloud Platform to handle parallel multi-direction requests:

**Cloud Run Configuration:**
- **Memory**: 2 GiB minimum (4 GiB recommended for large meshes)
- **CPU**: 2 vCPUs minimum (4 vCPUs for better parallel performance)
- **Concurrency**: 80-100 concurrent requests per instance
- **Timeout**: 300 seconds (5 minutes) for complex calculations
- **Min instances**: 1 (to avoid cold starts)
- **Max instances**: 10-20 (depending on expected load)

**Cloud Run Service YAML Example:**
```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: obstruction-server
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "1"
        autoscaling.knative.dev/maxScale: "10"
    spec:
      containerConcurrency: 80
      timeoutSeconds: 300
      containers:
      - image: gcr.io/YOUR-PROJECT/obstruction-server
        resources:
          limits:
            memory: 4Gi
            cpu: "4"
```

**Authentication Setup:**
```bash
# Get GCP authentication token
gcloud auth print-identity-token

# Use in request
AUTH_TOKEN=$(gcloud auth print-identity-token)
curl -X POST https://your-service.run.app/obstruction_parallel \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d @request_payload.json
```

**Performance Tips:**
- Each parallel request creates 64 concurrent HTTP calls
- Total execution time ≈ single obstruction time (parallelized)
- Monitor Cloud Run metrics for optimal instance sizing
- Use Cloud CDN for mesh data caching if meshes are reused
- Consider Cloud Load Balancing for high-traffic scenarios

### Deployment

#### Environment Configuration
Create a `.env` file with required configurations:
```sh
PORT=8081
GCP_REGION=us-central1
SERVER_NAME=obstruction-server
REPO_NAME=server_obstruction
IMAGE_NAME=obstruction-server

SCW_REGISTRY_NAMESPACE=nsp
SCW_PROJECT_ID=project-id
SCW_SERVER=serve-container
SCW_IMAGE=server_obstruction
```

#### Docker Deployment
Build and run using Docker:
```sh
docker build -t obstruction-server .
docker run -p 8081:8081 obstruction-server
```

#### Cloud Deployment
Deploy to Google Cloud Platform:
```sh
gcloud auth login
bash build.sh
```

or Scaleway:
```sh
bash build_scw.sh
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

#### Locally

Set up the server locally for development and testing:

1. **Clone the Repository**
   ```bash
   git clone https://github.com/upskiller-xyz/server_obstruction.git
   cd server_obstruction
   ```

2. **Install Dependencies with Poetry**
   ```bash
   poetry install
   ```

3. **Activate Virtual Environment**
   ```bash
   poetry shell
   ```

4. **Run the Server**
   ```bash
   python -m src.main
   ```
   The server will start on `http://localhost:8081` by default.

5. **Run Tests**
   ```bash
   poetry run pytest
   ```

6. **Code Quality Checks**
   ```bash
   poetry run ruff check .
   poetry run mypy .
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- DESIGN -->
## Design

### Architecture

The server follows object-oriented design principles with clean separation of concerns:

```
ObstructionService
├── TriangleFilter (pre-filters relevant geometry)
├── PlaneTriangleIntersector (efficient intersection calculations)
├── HorizonIntersectionCalculator (horizon obstruction)
└── ZenithIntersectionCalculator (zenith obstruction)
```

**Key Components:**
- **Triangle Filtering**: Pre-filters geometry based on spatial criteria (direction, distance, height)
- **Plane-Triangle Intersection**: Efficient algorithm that only processes relevant triangles
- **Dependency Injection**: All services are injected through constructors
- **Factory Patterns**: Services are created using factory classes
- **Single Responsibility**: Each class has one clear purpose
- **Abstract Base Classes**: Define contracts for implementations

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ROADMAP -->
## Roadmap

See the [open issues](https://github.com/upskiller-xyz/server_obstruction/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTRIBUTION -->
## Contribution

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

**Development Guidelines:**

* Follow Object-Oriented Programming principles and design patterns
* Use [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/)
* Follow [semantic versioning](https://semver.org/)
* Add type hints and documentation
* Write tests for new functionality
* Run `poetry run ruff check` and `poetry run mypy` before committing

See [CLAUDE.md](CLAUDE.md) for detailed development instructions.

### Top contributors:

<a href="https://github.com/upskiller-xyz/server_obstruction/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=upskiller-xyz/server_obstruction" alt="Top Contributors" />
</a>

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- LICENSE -->
## License

See [License](./docs/LICENSE) for more details - or [read a summary](https://choosealicense.com/licenses/gpl-3.0/).

In short:

Strong copyleft. You **can** use, distribute and modify this code in both academic and commercial contexts. At the same time you **have to** keep the code open-source under the same license (`GPL-3.0`) and give the appropriate [attribution](#attribution) to the authors.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Attribution

📖 **Academic/Industry Use**: Please cite this work as described in [CITATION.cff](docs/citation/CITATION.cff), [CITE.txt](docs/citation/CITE.txt) or [ATTRIBUTION.md](docs/citation/ATTRIBUTION.md).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Trademark Notice

- **"Upskiller"** is an informal collaborative name used by contributors affiliated with BIMTech Innovations AB.
- BIMTech Innovations AB owns all legal rights to the **Obstruction Server** project.
- The GPL-3.0 license applies to code, not branding. Commercial use of the names requires permission.

Contact: [Upskiller](mailto:info@upskiller.xyz)

## Contact

Stanislava Fedorova - [e-mail](mailto:stasya.fedorova@gmail.com)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* [README template](https://github.com/othneildrew/Best-README-Template)
* [Flask](https://flask.palletsprojects.com/) - Web framework
* [NumPy](https://numpy.org/) - Numerical computations

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/upskiller-xyz/server_obstruction.svg?style=for-the-badge
[contributors-url]: https://github.com/upskiller-xyz/server_obstruction/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/upskiller-xyz/server_obstruction.svg?style=for-the-badge
[forks-url]: https://github.com/upskiller-xyz/server_obstruction/network/members
[stars-shield]: https://img.shields.io/github/stars/upskiller-xyz/server_obstruction.svg?style=for-the-badge
[stars-url]: https://github.com/upskiller-xyz/server_obstruction/stargazers
[issues-shield]: https://img.shields.io/github/issues/upskiller-xyz/server_obstruction.svg?style=for-the-badge
[issues-url]: https://github.com/upskiller-xyz/server_obstruction/issues
[license-shield]: https://img.shields.io/github/license/upskiller-xyz/server_obstruction.svg?style=for-the-badge
[license-url]: https://github.com/upskiller-xyz/server_obstruction/blob/master/docs/LICENSE.txt
