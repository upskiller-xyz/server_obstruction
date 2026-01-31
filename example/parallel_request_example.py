"""
Example request for parallel multi-direction obstruction calculation

This script demonstrates how to call the /obstruction_parallel endpoint
to calculate obstruction angles for 64 directions in parallel using
HTTP requests to a microservice.

Usage:
    python example/parallel_request_example.py
"""

import requests
import json
from sample_constructions import SimpleWall


def create_parallel_obstruction_request():
    """
    Create example request for parallel multi-direction obstruction calculation

    Returns:
        Dictionary with request payload
    """
    # Create a simple wall mesh for testing
    wall = SimpleWall(
        center_x=5.0,
        center_y=0.0,
        center_z=1.5,
        width=10.0,
        height=3.0
    )

    # Window position (looking at the wall)
    window_x = 0.0
    window_y = 0.0
    window_z = 1.5

    # Extract mesh vertices
    mesh_vertices = [
        [v.x, v.y, v.z]
        for triangle in wall.mesh.triangles
        for v in [triangle.v1, triangle.v2, triangle.v3]
    ]

    # Build request payload
    request_payload = {
        # Window position
        "x": window_x,
        "y": window_y,
        "z": window_z,

        # Mesh geometry
        "mesh": mesh_vertices,

        # Microservice URL (replace with your actual service URL)
        # This should point to the /obstruction endpoint of your deployed service
        "microservice_url": "http://localhost:8081/obstruction",

        # Optional: Number of directions (default 64)
        "num_directions": 64,

        # Optional: Angle range (default 17.5° to 162.5°)
        "start_angle_degrees": 17.5,
        "end_angle_degrees": 162.5,

        # Optional: GCP authentication token
        # "auth_token": "your-gcp-bearer-token-here"
    }

    return request_payload


def send_parallel_request(server_url: str, request_payload: dict):
    """
    Send parallel obstruction request to server

    Args:
        server_url: Base URL of the server
        request_payload: Request payload dictionary

    Returns:
        Response dictionary
    """
    endpoint = f"{server_url}/obstruction_parallel"

    print(f"Sending request to {endpoint}...")
    print(f"Window position: ({request_payload['x']}, {request_payload['y']}, {request_payload['z']})")
    print(f"Number of directions: {request_payload.get('num_directions', 64)}")
    print(f"Mesh vertices: {len(request_payload['mesh'])}")

    # Send POST request
    response = requests.post(
        endpoint,
        json=request_payload,
        headers={"Content-Type": "application/json"}
    )

    # Check response
    if response.status_code == 200:
        result = response.json()
        print("\n✓ Request successful!")

        if result.get("status") == "success":
            data = result.get("data", {})
            print(f"\nResults:")
            print(f"  - Directions calculated: {data.get('num_directions', 0)}")
            print(f"  - Total time: {data.get('total_time_seconds', 0):.2f}s")

            # Print sample of horizon angles
            horizon_angles = data.get("horizon", [])
            if horizon_angles:
                print(f"\n  Horizon angles (first 5):")
                for i, angle in enumerate(horizon_angles[:5]):
                    print(f"    Direction {i}: {angle:.2f}°")

            # Print sample of zenith angles
            zenith_angles = data.get("zenith", [])
            if zenith_angles:
                print(f"\n  Zenith angles (first 5):")
                for i, angle in enumerate(zenith_angles[:5]):
                    print(f"    Direction {i}: {angle:.2f}°")

            return result
        else:
            print(f"\n✗ Error: {result.get('error', 'Unknown error')}")
            return None
    else:
        print(f"\n✗ HTTP Error {response.status_code}")
        print(f"Response: {response.text}")
        return None


def main():
    """Main example execution"""
    # Server configuration
    SERVER_URL = "http://localhost:8081"

    # Create request payload
    request_payload = create_parallel_obstruction_request()

    # Send request
    result = send_parallel_request(SERVER_URL, request_payload)

    # Save result to file
    if result:
        output_file = "example/parallel_obstruction_result.json"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nFull result saved to: {output_file}")


if __name__ == "__main__":
    main()
