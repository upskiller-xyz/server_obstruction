"""OpenAPI specification generator from Pydantic models for auto-documentation"""
from typing import Any, Dict


class OpenAPISpecGenerator:
    """Generates OpenAPI 3.0 specification for Flask API using Pydantic models"""

    @staticmethod
    def generate_spec(
        title: str = "Obstruction Calculation API",
        description: str = "Service for calculating horizon and zenith obstruction angles from 3D mesh data",
        version: str = "0.1.0",
        base_url: str = "/"
    ) -> Dict[str, Any]:
        """
        Generate OpenAPI 3.0 specification.

        Args:
            title: API title
            description: API description
            version: API version
            base_url: Base URL for API endpoints

        Returns:
            OpenAPI 3.0 specification dict
        """
        return {
            "openapi": "3.0.0",
            "info": {
                "title": title,
                "description": description,
                "version": version,
                "contact": {
                    "name": "API Support"
                }
            },
            "servers": [
                {
                    "url": base_url,
                    "description": "Obstruction Calculation Server"
                }
            ],
            "paths": OpenAPISpecGenerator._generate_paths(),
            "components": {
                "schemas": OpenAPISpecGenerator._generate_schemas()
            }
        }

    @staticmethod
    def _generate_paths() -> Dict[str, Any]:
        """Generate API paths from endpoint definitions"""
        return {
            "/": {
                "get": {
                    "summary": "Server health check",
                    "description": "Returns server status and version information.",
                    "tags": ["Server"],
                    "responses": {
                        "200": {
                            "description": "Server status",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/StatusResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/routes": {
                "get": {
                    "summary": "List registered routes",
                    "description": "Returns all HTTP routes registered on the server.",
                    "tags": ["Server"],
                    "responses": {
                        "200": {
                            "description": "List of registered routes",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/RoutesResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/horizon": {
                "post": {
                    "summary": "Calculate horizon obstruction angle",
                    "description": (
                        "Calculates the maximum horizon obstruction angle (degrees above horizontal) "
                        "from the given window position looking in the given direction through the mesh."
                    ),
                    "tags": ["Obstruction Calculation"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ObstructionRequest"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Horizon angle calculated successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SingleAngleEnvelope"}
                                }
                            }
                        },
                        "400": {
                            "description": "Invalid request (missing fields, bad mesh format, window on mesh surface)",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        },
                        "500": {
                            "description": "Internal server error",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/zenith": {
                "post": {
                    "summary": "Calculate zenith obstruction angle",
                    "description": (
                        "Calculates the maximum zenith obstruction angle (degrees below vertical) "
                        "from the given window position looking in the given direction through the mesh."
                    ),
                    "tags": ["Obstruction Calculation"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ObstructionRequest"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Zenith angle calculated successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SingleAngleEnvelope"}
                                }
                            }
                        },
                        "400": {
                            "description": "Invalid request",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        },
                        "500": {
                            "description": "Internal server error",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/obstruction": {
                "post": {
                    "summary": "Calculate horizon and zenith in one request",
                    "description": (
                        "Calculates both the horizon and zenith obstruction angles "
                        "for a single window position and direction."
                    ),
                    "tags": ["Obstruction Calculation"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ObstructionRequest"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Both angles calculated successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/BothAnglesEnvelope"}
                                }
                            }
                        },
                        "400": {
                            "description": "Invalid request",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        },
                        "500": {
                            "description": "Internal server error",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/obstruction_all": {
                "post": {
                    "summary": "Calculate obstruction for multiple directions (local)",
                    "description": (
                        "Calculates horizon and zenith obstruction angles across N evenly-spaced directions "
                        "using the gap-based algorithm locally. "
                        "Defaults: 64 directions, 17.5°–162.5° relative to window normal."
                    ),
                    "tags": ["Obstruction Calculation"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/MultiDirectionRequest"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Multi-direction results",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/MultiDirectionEnvelope"}
                                }
                            }
                        },
                        "400": {
                            "description": "Invalid request",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        },
                        "500": {
                            "description": "Internal server error",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/obstruction_parallel": {
                "post": {
                    "summary": "Calculate obstruction for multiple directions (parallel microservice)",
                    "description": (
                        "Fans out N direction calculations as parallel HTTP requests to the "
                        "obstruction microservice and assembles the results. "
                        "Shares the same request/response format as /obstruction_all. "
                        "Requires the MICROSERVICE_URL environment variable to be set."
                    ),
                    "tags": ["Obstruction Calculation"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/MultiDirectionRequest"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Parallel multi-direction results",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/MultiDirectionEnvelope"}
                                }
                            }
                        },
                        "400": {
                            "description": "Invalid request",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        },
                        "500": {
                            "description": "Internal server error",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/obstruction_parallel_bin": {
                "post": {
                    "summary": "Binary (multipart) variant of /obstruction_parallel",
                    "description": (
                        "Same computation as /obstruction_parallel, but the mesh is sent as a "
                        "binary NumPy .npy file (optionally gzip-compressed) in a multipart body "
                        "instead of an inline JSON array. Avoids the multi-second JSON mesh parse: "
                        "the mesh is decoded with np.load (~ms). The small window fields are sent "
                        "as a JSON 'params' form field."
                    ),
                    "tags": ["Obstruction Calculation"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "params": {
                                            "type": "string",
                                            "description": (
                                                "JSON object with the window/direction fields "
                                                "(same shape as MultiDirectionRequest, minus mesh)."
                                            ),
                                        },
                                        "mesh": {
                                            "type": "string",
                                            "format": "binary",
                                            "description": (
                                                "NumPy .npy file of an (N, 3) float vertex array "
                                                "(three vertices per triangle), optionally gzipped."
                                            ),
                                        },
                                    },
                                    "required": ["params", "mesh"],
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Parallel multi-direction results",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/MultiDirectionEnvelope"}
                                }
                            }
                        },
                        "400": {
                            "description": "Invalid request",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        },
                        "500": {
                            "description": "Internal server error",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                }
            }
        }

    @staticmethod
    def _generate_schemas() -> Dict[str, Any]:
        """Generate OpenAPI schemas"""
        return {
            # ── Request schemas ──────────────────────────────────────────────
            "ObstructionRequest": {
                "type": "object",
                "description": (
                    "Window position and mesh geometry for a single-direction obstruction calculation. "
                    "The window can be specified either as a pre-computed centre point (x, y, z) "
                    "or as two wall endpoints (x1, y1, z1, x2, y2, z2) with an optional room polygon "
                    "so the reference point can be derived automatically."
                ),
                "required": ["x", "y", "z", "direction_angle", "mesh"],
                "properties": {
                    "x": {
                        "type": "number",
                        "description": "Window centre X coordinate (centre format)"
                    },
                    "y": {
                        "type": "number",
                        "description": "Window centre Y coordinate (centre format)"
                    },
                    "z": {
                        "type": "number",
                        "description": "Window centre Z coordinate / height (centre format)"
                    },
                    "x1": {
                        "type": "number",
                        "description": "First endpoint X coordinate (endpoint format)"
                    },
                    "y1": {
                        "type": "number",
                        "description": "First endpoint Y coordinate (endpoint format)"
                    },
                    "z1": {
                        "type": "number",
                        "description": "First endpoint Z coordinate (endpoint format)"
                    },
                    "x2": {
                        "type": "number",
                        "description": "Second endpoint X coordinate (endpoint format)"
                    },
                    "y2": {
                        "type": "number",
                        "description": "Second endpoint Y coordinate (endpoint format)"
                    },
                    "z2": {
                        "type": "number",
                        "description": "Second endpoint Z coordinate (endpoint format)"
                    },
                    "room_polygon": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 2,
                            "maxItems": 3
                        },
                        "description": "Room floor polygon used to compute the outward-facing reference point (endpoint format)"
                    },
                    "direction_angle": {
                        "type": "number",
                        "description": "Window outward-facing direction in radians (0 = +X axis, counter-clockwise)"
                    },
                    "mesh": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 3,
                            "maxItems": 3,
                            "description": "Vertex [x, y, z]"
                        },
                        "description": (
                            "Flat list of triangle vertices. Every three consecutive vertices form one triangle. "
                            "Total vertex count must be divisible by 3."
                        )
                    }
                },
                "example": {
                    "x": 0.0,
                    "y": 0.0,
                    "z": 3.0,
                    "direction_angle": 0.0,
                    "mesh": [
                        [10.0, -5.0, 0.0],
                        [10.0, -5.0, 5.0],
                        [10.0,  5.0, 0.0]
                    ]
                }
            },
            "MultiDirectionRequest": {
                "type": "object",
                "description": (
                    "Window position and mesh geometry for a multi-direction sweep. "
                    "direction_angle is not required — the window normal is used as the base direction "
                    "and the sweep range is applied relative to it."
                ),
                "required": ["x", "y", "z", "mesh"],
                "properties": {
                    "x": {"type": "number", "description": "Window centre X coordinate"},
                    "y": {"type": "number", "description": "Window centre Y coordinate"},
                    "z": {"type": "number", "description": "Window centre Z / height"},
                    "mesh": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 3,
                            "maxItems": 3
                        },
                        "description": "Flat list of triangle vertices (same format as ObstructionRequest)"
                    },
                    "num_directions": {
                        "type": "integer",
                        "default": 64,
                        "minimum": 1,
                        "description": "Number of evenly-spaced directions to evaluate"
                    },
                    "start_angle_degrees": {
                        "type": "number",
                        "default": 17.5,
                        "description": "Start of the angular sweep range in degrees, relative to window normal"
                    },
                    "end_angle_degrees": {
                        "type": "number",
                        "default": 162.5,
                        "description": "End of the angular sweep range in degrees, relative to window normal"
                    }
                },
                "example": {
                    "x": 0.0,
                    "y": 0.0,
                    "z": 3.0,
                    "mesh": [
                        [10.0, -5.0, 0.0],
                        [10.0, -5.0, 5.0],
                        [10.0,  5.0, 0.0]
                    ],
                    "num_directions": 64,
                    "start_angle_degrees": 17.5,
                    "end_angle_degrees": 162.5
                }
            },
            # ── Shared sub-schemas ───────────────────────────────────────────
            "Point3D": {
                "type": "object",
                "properties": {
                    "x": {"type": "number"},
                    "y": {"type": "number"},
                    "z": {"type": "number"}
                }
            },
            "ObstructionAngle": {
                "type": "object",
                "description": "Obstruction angle result for one angular direction (horizon or zenith)",
                "properties": {
                    "obstruction_angle_degrees": {
                        "type": "number",
                        "description": "Obstruction angle in degrees"
                    },
                    "obstruction_angle_radians": {
                        "type": "number",
                        "description": "Obstruction angle in radians"
                    },
                    "highest_point": {
                        "oneOf": [
                            {"$ref": "#/components/schemas/Point3D"},
                            {"type": "null"}
                        ],
                        "description": "3D coordinates of the highest obstructing point, or null if none found"
                    }
                },
                "example": {
                    "obstruction_angle_degrees": 11.31,
                    "obstruction_angle_radians": 0.1974,
                    "highest_point": {"x": 10.0, "y": 0.0, "z": 5.0}
                }
            },
            "DirectionResult": {
                "type": "object",
                "description": "Horizon and zenith results for one evaluated direction",
                "properties": {
                    "direction_angle": {
                        "type": "number",
                        "description": "Absolute direction angle in radians"
                    },
                    "direction_angle_degrees": {
                        "type": "number",
                        "description": "Absolute direction angle in degrees"
                    },
                    "horizon": {"$ref": "#/components/schemas/ObstructionAngle"},
                    "zenith": {"$ref": "#/components/schemas/ObstructionAngle"}
                }
            },
            # ── Response envelope schemas ────────────────────────────────────
            "SingleAngleEnvelope": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "success"},
                    "data": {"$ref": "#/components/schemas/ObstructionAngle"}
                }
            },
            "BothAnglesEnvelope": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "success"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "horizon": {"$ref": "#/components/schemas/ObstructionAngle"},
                            "zenith": {"$ref": "#/components/schemas/ObstructionAngle"}
                        }
                    }
                }
            },
            "MultiDirectionEnvelope": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "success"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "results": {
                                "type": "array",
                                "items": {"$ref": "#/components/schemas/DirectionResult"},
                                "description": "One result object per evaluated direction"
                            },
                            "num_directions": {
                                "type": "integer",
                                "description": "Number of directions evaluated"
                            },
                            "total_time_seconds": {
                                "type": "number",
                                "description": "Total wall-clock time for the calculation"
                            }
                        }
                    }
                }
            },
            "StatusResponse": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "success"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "controller": {"type": "string", "example": "ready"},
                            "service": {"type": "object"}
                        }
                    }
                }
            },
            "RoutesResponse": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "success"},
                    "data": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string", "example": "/obstruction"},
                                "methods": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "example": ["POST"]
                                }
                            }
                        }
                    }
                }
            },
            "ErrorResponse": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "error"},
                    "error": {
                        "type": "string",
                        "description": "Human-readable error message"
                    }
                },
                "example": {
                    "status": "error",
                    "error": "Invalid mesh format: expected a list of vertices, got dict."
                }
            }
        }
