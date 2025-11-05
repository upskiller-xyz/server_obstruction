# Coordinate System and Obstruction Angle Calculation

> **Quick Reference**: Looking for API usage? See [API Documentation](api.md) | Want interactive examples? Try the [Demo Notebook](../example/demo.ipynb)

## Table of Contents
- [Quick Reference](#quick-reference)
- [Coordinate System](#coordinate-system)
- [Window Direction Vector](#window-direction-vector)
- [Projection Plane](#projection-plane)
- [Obstruction Angle Calculation](#obstruction-angle-calculation)
- [Mathematical Details](#mathematical-details)
- [Examples](#examples)

---

## Quick Reference

**TL;DR:**
- **Coordinate System**: Right-handed XYZ (X=forward, Y=up, Z=right)
- **Direction Angles**: `rad_x` = pitch (up/down), `rad_y` = yaw (left/right)
- **Direction Vector**: `(cos(rad_y)*cos(rad_x), sin(rad_x), sin(rad_y)*cos(rad_x))`
- **Projection Plane**: Vertical plane through window containing viewing direction
- **Obstruction Angle**: `arctan(height_difference / horizontal_distance)`

---

## Coordinate System

The raytracing server uses a **right-handed 3D coordinate system** with the following axes:

```
      +Y (Up)
       |
       |
       |
       +------- +X (Forward)
      /
     /
   +Z (Right)
```

### Axis Definitions

- **X-axis**: Horizontal axis representing forward/backward direction
  - Positive X: Forward
  - Negative X: Backward

- **Y-axis**: Vertical axis representing height
  - Positive Y: Up (toward the sky)
  - Negative Y: Down (toward the ground)
  - Ground level is at Y = 0

- **Z-axis**: Horizontal axis representing left/right width
  - Positive Z: Right (when facing +X)
  - Negative Z: Left (when facing +X)

---

## Window Direction Vector

The window's viewing direction is defined by two rotation angles: `rad_x` (pitch) and `rad_y` (yaw).

### Rotation Angles

- **`rad_x`** (pitch): Rotation around the X-axis
  - Positive: Looking upward
  - Negative: Looking downward
  - Zero: Looking horizontally

- **`rad_y`** (yaw): Rotation around the Y-axis
  - Positive: Looking rightward (toward +Z)
  - Negative: Looking leftward (toward -Z)
  - Zero: Looking straight ahead (toward +X)

### Direction Vector Calculation

The unit direction vector is calculated from the angles:

```python
direction_x = cos(rad_y) * cos(rad_x)
direction_y = sin(rad_x)
direction_z = sin(rad_y) * cos(rad_x)
```

This produces a **unit vector** (magnitude = 1) representing the viewing direction.

### Common Direction Examples

| `rad_x` | `rad_y` | Direction Vector | Description |
|---------|---------|------------------|-------------|
| 0 | 0 | (1, 0, 0) | Forward (+X) |
| π/2 | 0 | (0, 1, 0) | Up (+Y) |
| -π/2 | 0 | (0, -1, 0) | Down (-Y) |
| 0 | π/2 | (0, 0, 1) | Right (+Z) |
| 0 | -π/2 | (0, 0, -1) | Left (-Z) |
| 0 | π | (-1, 0, 0) | Backward (-X) |
| π/4 | 0 | (0.707, 0.707, 0) | Up-Forward (45°) |

---

## Projection Plane

The projection plane is a **vertical plane** used for orthographic projection of 3D geometry.

### Plane Properties

1. **Passes through the window center point**
2. **Contains the viewing direction vector** (the direction lies within the plane)
3. **Contains the world up vector** (Y-axis direction)
4. **Is always vertical** (perpendicular to the horizontal XZ-plane)

### Plane Basis Vectors

The projection plane is defined by three vectors:

#### 1. **u_axis** (Horizontal Basis)
The horizontal component of the viewing direction:

```python
u_axis = normalize([direction_x, 0, direction_z])
```

This vector lies in the XZ-plane and represents the horizontal viewing direction.

#### 2. **v_axis** (Vertical Basis)
Always the world up vector:

```python
v_axis = [0, 1, 0]
```

This ensures the plane is always vertical.

#### 3. **normal** (Geometric Normal)
Perpendicular to both the viewing direction and world up:

```python
normal = normalize(cross(direction_vector, world_up))
```

This is the geometric normal to the plane surface.

### Plane Visualization

```
                    ^ v_axis (up)
                    |
                    |
        Window •----+----> u_axis (horizontal viewing direction)
                   /
                  / normal (perpendicular to plane)
                 ↙

        [Projection Plane - vertical surface]
```

### Edge Case: Looking Straight Up/Down

When `rad_x = ±π/2` (looking straight up or down), the viewing direction is parallel to world up. In this case:
- Use a default horizontal direction: `u_axis = [1, 0, 0]`
- The plane becomes a vertical plane perpendicular to the default direction

---

## Obstruction Angle Calculation

The obstruction angle measures the **vertical angle** from the window's horizontal viewing direction to the highest obstructing point.

### Algorithm

1. **Project all mesh vertices** onto the projection plane
2. **Filter points**: Only keep points in front of the window (positive distance along viewing direction)
3. **Check intersection**: If no valid points, return angle = 0° (mesh behind window or no obstruction)
4. **Find the highest point** (maximum Y-coordinate in 3D space)
5. **Calculate vertical distance**: `Δy = highest_point.y - window_center.y`
6. **Calculate horizontal distance**: Distance along horizontal viewing direction
7. **Compute angle**: `angle = arctan(Δy / horizontal_distance)`

### Horizontal Distance Calculation

The horizontal distance is calculated using **only the horizontal component** of the viewing direction:

```python
# Extract horizontal viewing direction (remove Y component)
horizontal_direction = [direction_x, 0, direction_z]
horizontal_direction = normalize(horizontal_direction)

# Vector from window to point
point_vector = highest_point - window_center

# Project onto horizontal viewing direction
horizontal_distance = dot(point_vector, horizontal_direction)
```

This ensures accurate angle calculation even when the window is tilted up or down.

### Why Use Horizontal Component?

When the viewing direction has a vertical component (tilted up/down), the full 3D distance includes both horizontal and vertical displacement. For obstruction angle calculation, we need:

- **Vertical distance**: Actual height difference (always use Y-component)
- **Horizontal distance**: Ground-level distance in the viewing direction (use only XZ-components)

This separation ensures the angle represents the **vertical obstruction** independent of the viewing tilt.

---

## Mathematical Details

### Projection onto Plane

For a point **P** in 3D space, its projection onto the plane is calculated as:

```python
# Vector from plane origin to point
relative = P - window_center

# Project onto plane basis vectors
u = dot(relative, u_axis)  # Horizontal coordinate
v = dot(relative, v_axis)  # Vertical coordinate

# Projected point in 2D plane coordinates
projected = (u, v)
```

### Angle Formula

The obstruction angle θ is calculated as:

```
θ = arctan(vertical_distance / horizontal_distance)

where:
  vertical_distance = highest_point.y - window_center.y
  horizontal_distance = dot(point_vector, horizontal_direction)
```

**Constraints**:
- If `vertical_distance ≤ 0`: angle = 0° (no obstruction)
- If `horizontal_distance ≈ 0`: angle = 90° (point directly above)

### Unit Vector Properties

All direction vectors are **unit vectors** (magnitude = 1):

```
magnitude = sqrt(x² + y² + z²) = 1
```

This ensures consistent scale-independent calculations.

---

## Examples

### Example 1: Horizontal Forward View

**Setup:**
- Window: `(0, 1.5, 0)` (1.5m above ground)
- Direction: `rad_x = 0, rad_y = 0` → `(1, 0, 0)` (looking forward)
- Building: 10m away, 5m tall

**Calculation:**
```
vertical_distance = 5.0 - 1.5 = 3.5m
horizontal_distance = 10.0m
angle = arctan(3.5 / 10.0) = 19.29°
```

### Example 2: Tilted Upward View

**Setup:**
- Window: `(0, 1.5, 0)`
- Direction: `rad_x = π/6, rad_y = 0` → `(0.866, 0.5, 0)` (30° upward)
- Building: 10m away, 5m tall

**Calculation:**
```
# Horizontal component of direction: (0.866, 0, 0)
vertical_distance = 5.0 - 1.5 = 3.5m
horizontal_distance = 10.0m  (same as Example 1)
angle = arctan(3.5 / 10.0) = 19.29°
```

**Note**: The angle is the same because we use only the horizontal component for distance calculation.

### Example 3: Angled View (Right and Up)

**Setup:**
- Window: `(0, 2.0, 0)`
- Direction: `rad_x = π/4, rad_y = π/4` → `(0.5, 0.707, 0.5)` (45° right, 45° up)
- Building: Corner at `(8, 6, 8)`

**Calculation:**
```
direction_vector = (0.5, 0.707, 0.5)
horizontal_direction = normalize([0.5, 0, 0.5]) = (0.707, 0, 0.707)

vertical_distance = 6.0 - 2.0 = 4.0m

point_vector = (8, 4, 8)
horizontal_distance = dot((8, 4, 8), (0.707, 0, 0.707))
                    = 8*0.707 + 0 + 8*0.707
                    = 11.31m

angle = arctan(4.0 / 11.31) = 19.48°
```

---

## Implementation References

### Code Locations

- **Direction Vector Calculation**: `src/components/geometry.py` - `Vector3D.from_angles()`
- **Projection Plane Creation**: `src/components/projection.py` - `OrthographicProjectionCalculator.create_projection_plane()`
- **Point Projection**: `src/components/projection.py` - `OrthographicProjectionCalculator.project_point()`
- **Obstruction Angle**: `src/components/obstruction_calculator.py` - `MaxHeightObstructionCalculator.calculate_obstruction_angle()`

### API Usage

See `docs/api.md` for REST API endpoint details.

---

## Visualization

For interactive visualizations demonstrating the coordinate system and calculations, see:

- **Jupyter Notebook**: `example/demo.ipynb`
  - 3D visualization of projection plane and viewing directions
  - 2D side-view showing angle calculation
  - Multiple scenario comparisons

---

## Common Pitfalls

### ❌ Incorrect: Using Full 3D Distance

```python
# WRONG: This includes vertical component
distance = norm(highest_point - window_center)
angle = arctan(vertical_distance / distance)
```

**Problem**: When viewing upward/downward, this underestimates the horizontal distance.

### ✅ Correct: Using Horizontal Distance

```python
# CORRECT: Use only horizontal component
horizontal_dir = normalize([direction_x, 0, direction_z])
horizontal_distance = dot(point_vector, horizontal_dir)
angle = arctan(vertical_distance / horizontal_distance)
```

---

## Summary

1. **Coordinate System**: Right-handed XYZ with Y pointing up
2. **Direction Vector**: Calculated from `rad_x` and `rad_y` angles
3. **Projection Plane**: Vertical plane containing viewing direction and world up
4. **Horizontal Distance**: Use only XZ-components of viewing direction
5. **Obstruction Angle**: `arctan(vertical / horizontal)` measured from horizontal reference

This methodology ensures accurate and consistent obstruction angle calculations regardless of viewing direction or geometry orientation.
