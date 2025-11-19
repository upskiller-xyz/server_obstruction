#!/usr/bin/env python3
"""
Test script to check registered Flask routes
Run this inside the Docker container or on the VM
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from main import create_app

def test_routes():
    """Test and display all registered routes"""
    app = create_app()

    print("=" * 60)
    print("REGISTERED ROUTES")
    print("=" * 60)

    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': sorted(rule.methods - {'HEAD', 'OPTIONS'}),
            'path': rule.rule
        })

    # Sort by path
    routes.sort(key=lambda x: x['path'])

    for route in routes:
        methods = ', '.join(route['methods'])
        print(f"{route['path']:30} {methods:15} -> {route['endpoint']}")

    print("=" * 60)
    print(f"Total routes: {len(routes)}")
    print("=" * 60)

    # Test if key routes exist
    expected_routes = [
        ('/', 'GET'),
        ('/obstruction', 'POST'),
        ('/horizon_angle', 'POST'),
        ('/zenith_angle', 'POST'),
        ('/obstruction_all', 'POST'),
    ]

    print("\nRoute Check:")
    for path, method in expected_routes:
        found = any(r['path'] == path and method in r['methods'] for r in routes)
        status = "✓" if found else "✗"
        print(f"  {status} {method:6} {path}")

if __name__ == '__main__':
    test_routes()
