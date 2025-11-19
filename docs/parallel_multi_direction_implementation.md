# Parallel Multi-Direction Obstruction Calculation

## Overview

This implementation calculates obstruction angles from a window point toward 64 different directions in a half-circle field of view, using **parallel HTTP requests** to a microservice.

## Architecture

### Components

1. **DirectionCalculator** ([direction_calculator.py](../src/components/direction_calculator.py))
   - Handles angle transformations from half-circle to absolute world coordinates
   - Implements the coordinate system described in requirements

2. **ParallelObstructionService** ([parallel_obstruction_service.py](../src/server/services/parallel_obstruction_service.py))
   - Manages parallel HTTP requests using `aiohttp` and `asyncio`
   - Coordinates 64 simultaneous requests to microservice
   - Assembles results into arrays

3. **ObstructionController** ([obstruction_controller.py](../src/server/controllers/obstruction_controller.py))
   - Added `calculate_parallel_multi_direction` method
   - Handles request validation and response formatting

4. **Endpoint** ([main.py](../src/main.py))
   - New `/obstruction_parallel` endpoint
   - Accepts microservice URL and optional GCP auth token

## Direction Calculation

### Coordinate System

The system uses a half-circle coordinate system relative to the window's normal (facing direction):

- **0°** = 90° counter-clockwise from window normal (left edge of view)
- **90°** = window normal direction (straight ahead)
- **180°** = 90° clockwise from window normal (right edge of view)

### Default Configuration

Defined in [constants.py](../src/components/constants.py):

```python
class AllDirectionDefaults:
    NUM_DIRECTIONS = 64
    START_ANGLE_DEGREES = 17.5   # Skips extreme left edge
    END_ANGLE_DEGREES = 162.5     # Skips extreme right edge
```

### Angle Transformation

```python
# 1. Generate half-circle angles
half_circle_angles = np.linspace(17.5°, 162.5°, 64)

# 2. Transform to absolute world directions
absolute_angles = base_direction - 90° + half_circle_angle
```

## Parallel Request Strategy

### Architecture

1. **Single aiohttp session** - Reuses HTTP connections for efficiency
2. **Task creation** - Create 64 async tasks (one per direction)
3. **Parallel execution** - `asyncio.gather()` executes all simultaneously
4. **Result collection** - Results returned in same order as tasks

### Implementation Pattern

```python
async with aiohttp.ClientSession() as session:
    tasks = [
        calculate_single_direction(session, x, y, z, angle, mesh)
        for angle in direction_angles
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
```

### Request Payload

Each of the 64 requests contains:

```json
{
  "x": 0.0,
  "y": 0.0,
  "z": 1.5,
  "direction_angle": 0.785,  // radians
  "mesh": [
    [x1, y1, z1],
    [x2, y2, z2],
    // thousands of vertices
  ]
}
```

### Response Data

Each response returns:

```json
{
  "status": "success",
  "data": {
    "horizon": {
      "obstruction_angle_degrees": 45.2,
      "obstruction_angle_radians": 0.789,
      "highest_point": {"x": 5.0, "y": 0.0, "z": 5.0}
    },
    "zenith": {
      "obstruction_angle_degrees": 30.5,
      "obstruction_angle_radians": 0.532,
      "highest_point": {"x": 5.0, "y": 0.0, "z": 3.0}
    }
  }
}
```

## Result Assembly

The 64 responses are assembled into arrays:

```python
{
  "status": "success",
  "data": {
    "horizon_angles": [45.2, 44.8, 44.1, ...],      // 64 values
    "zenith_angles": [30.5, 31.2, 32.0, ...],       // 64 values
    "direction_angles_degrees": [17.5, 20.0, ...],  // 64 values
    "num_directions": 64,
    "total_time_seconds": 2.5,
    "results": [...]  // Full detailed results
  }
}
```

## API Usage

### Endpoint

```
POST /obstruction_parallel
```

### Request Body

```json
{
  "x": 0.0,
  "y": 0.0,
  "z": 1.5,
  "mesh": [[x1, y1, z1], ...],
  "microservice_url": "http://your-service.run.app/obstruction",
  "auth_token": "optional-gcp-bearer-token",
  "num_directions": 64,
  "start_angle_degrees": 17.5,
  "end_angle_degrees": 162.5
}
```

### Example Request

See [parallel_request_example.py](../example/parallel_request_example.py):

```python
import requests

payload = {
    "x": 0.0,
    "y": 0.0,
    "z": 1.5,
    "mesh": mesh_vertices,
    "microservice_url": "http://localhost:8081/obstruction"
}

response = requests.post(
    "http://localhost:8081/obstruction_parallel",
    json=payload
)

result = response.json()
print(f"Calculated {result['data']['num_directions']} directions")
print(f"Total time: {result['data']['total_time_seconds']:.2f}s")
```

## GCP Deployment

### Cloud Run Configuration

For optimal parallel execution performance:

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
      containerConcurrency: 80      # Handle 80 concurrent requests
      timeoutSeconds: 300           # 5 minute timeout
      containers:
      - image: gcr.io/PROJECT/obstruction-server
        resources:
          limits:
            memory: 4Gi             # 4 GiB for large meshes
            cpu: "4"                # 4 vCPUs for parallel performance
```

### Recommended Settings

- **Memory**: 4 GiB (minimum 2 GiB)
- **CPU**: 4 vCPUs (minimum 2 vCPUs)
- **Concurrency**: 80-100 requests per instance
- **Timeout**: 300 seconds
- **Min instances**: 1 (avoid cold starts)
- **Max instances**: 10-20 (based on load)

### Authentication

```bash
# Get GCP auth token
AUTH_TOKEN=$(gcloud auth print-identity-token)

# Use in request
curl -X POST https://service.run.app/obstruction_parallel \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d @payload.json
```

### Performance Characteristics

- **Parallelization**: 64 concurrent HTTP requests
- **Execution time**: ≈ single obstruction calculation time (fully parallelized)
- **Network efficiency**: Single aiohttp session with connection pooling
- **Scalability**: Cloud Run auto-scales based on request volume

### Monitoring

Key metrics to monitor in GCP:

- **Request latency** (p50, p95, p99)
- **Instance count** (min/max scaling behavior)
- **CPU utilization** (should be high during parallel execution)
- **Memory utilization** (watch for mesh size impact)
- **Error rate** (failed parallel requests)

## Design Patterns Used

### Object-Oriented Principles

1. **Single Responsibility Principle**
   - `DirectionCalculator`: Only handles angle calculations
   - `ParallelObstructionService`: Only handles parallel HTTP coordination
   - `ParallelRequestBuilder`: Only builds request payloads

2. **Factory Pattern**
   - `ParallelObstructionServiceFactory`: Creates service instances

3. **Builder Pattern**
   - `ParallelRequestBuilder`: Constructs complex request payloads

4. **Strategy Pattern**
   - Async HTTP requests via aiohttp
   - Parallel execution via asyncio.gather

5. **Dependency Injection**
   - Services injected through constructors
   - Logger, microservice URL, auth token injected

6. **Enumerator Pattern**
   - `AllDirectionDefaults`: Constants instead of magic numbers
   - `ResponseField`: Field names as enums

## Implementation Details

### Key Classes

#### DirectionCalculator

```python
class DirectionCalculator:
    @staticmethod
    def calculate_direction_angles(
        base_direction_radians: float,
        num_directions: int = None,
        start_angle_degrees: float = None,
        end_angle_degrees: float = None
    ) -> np.ndarray:
        # Generates 64 evenly spaced absolute direction angles
        ...
```

#### ParallelObstructionService

```python
class ParallelObstructionService:
    async def calculate_all_directions_parallel(
        self,
        request: ObstructionRequest,
        num_directions: int = None,
        start_angle_degrees: float = None,
        end_angle_degrees: float = None
    ) -> Dict[str, Any]:
        # Coordinates 64 parallel HTTP requests
        ...
```

### Error Handling

- **HTTP errors**: Caught per-request, logged, marked in results
- **Network timeouts**: Handled by aiohttp ClientSession
- **Invalid responses**: Caught as exceptions in gather()
- **Validation errors**: Caught in controller layer

## Testing

Run the example:

```bash
# Start server
python -m src.main

# Run parallel request example
python example/parallel_request_example.py
```

Expected output:

```
Sending request to http://localhost:8081/obstruction_parallel...
Window position: (0.0, 0.0, 1.5)
Number of directions: 64
Mesh vertices: 6

✓ Request successful!

Results:
  - Directions calculated: 64
  - Total time: 2.50s

  Horizon angles (first 5):
    Direction 0: 45.20°
    Direction 1: 44.80°
    Direction 2: 44.10°
    ...
```

## Troubleshooting

### Common Issues

1. **"Parallel obstruction service not configured"**
   - Ensure `microservice_url` is provided in request body

2. **Authentication errors**
   - Verify GCP token is valid: `gcloud auth print-identity-token`
   - Check token expiration (tokens expire after 1 hour)

3. **Timeout errors**
   - Increase Cloud Run timeout in service.yaml
   - Check mesh size (large meshes take longer)

4. **Connection pool exhausted**
   - Increase `containerConcurrency` in Cloud Run config
   - Reduce `num_directions` if needed

## References

- [aiohttp Documentation](https://docs.aiohttp.org/)
- [asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Project Development Guidelines](../CLAUDE.md)
