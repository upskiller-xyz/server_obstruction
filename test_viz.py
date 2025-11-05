"""Test visualization coordinate system"""
import numpy as np
from example.viz_utils import DirectionVectorCalculator, ProjectionPlaneBuilder

# Test forward-looking window
window_center = [0.0, 3.0, 0.0]
window_angles = [0.0, 0.0]  # Forward

calc = DirectionVectorCalculator()
dir_vec = calc.from_angles(*window_angles)

print("Direction vector (calculation space):", dir_vec)
print("  - Should be [1, 0, 0] for forward")
print()

# Check horizontal component
horiz = calc.get_horizontal_component(dir_vec)
print("Horizontal component:", horiz)
print("  - Should be [1, 0, 0]")
print()

# Check projection plane axes
plane = ProjectionPlaneBuilder(window_center, horiz)
print("Projection plane u-axis (horizontal):", plane.u_axis)
print("  - Should be [1, 0, 0]")
print()
print("Projection plane v-axis (vertical):", plane.v_axis)
print("  - Should be [0, 1, 0] in calc space")
print("  - Will become [0, 0, 1] when plotted (Y->Z swap)")
print()

# Test a point projection
test_point = np.array([10.0, 5.0, 0.0])  # 10m forward, 5m up
projected = plane.project_point(test_point)
print("Test point [10, 5, 0] projected:", projected)
print("  - u component:", projected[0], "(should be 10)")
print("  - v component:", projected[1], "(should be 2)")
