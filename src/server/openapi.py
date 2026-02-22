"""OpenAPI specification generator from Pydantic models for auto-documentation"""
from typing import Dict, Any


class OpenAPISpecGenerator:
    """Generates OpenAPI 3.0 specification for Flask API using Pydantic models"""

    @staticmethod
    def generate_spec(
        title: str = "Obstruction Calculation API",
        description: str = "Service for calculating horizon and zenith obstruction angles from 3D mesh data",
        version: str = "1.0.0",
        base_url: str = "/"
    ) -> Dict[str, Any]:
        """
        Generate OpenAPI 3.0 specification from Pydantic models.

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
                    "summary": "Get server status",
                    "description": "Health check endpoint returning server status",
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
            "/horizon": {
                "post": {
                    "summary": "Calculate horizon obstruction angle",
                    "description": "Calculate the maximum horizon obstruction angle from a 3D mesh",
                    "tags": ["Obstruction Calculation"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ObstructionCalculationRequest"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Horizon obstruction angle calculated successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string", "example": "success"},
                                            "data": {"$ref": "#/components/schemas/ObstructionAngleResponse"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request - invalid input",
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
                    "description": "Calculate the maximum zenith obstruction angle from a 3D mesh",
                    "tags": ["Obstruction Calculation"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ObstructionCalculationRequest"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Zenith obstruction angle calculated successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string", "example": "success"},
                                            "data": {"$ref": "#/components/schemas/ObstructionAngleResponse"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request - invalid input",
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
                    "summary": "Calculate both horizon and zenith angles",
                    "description": "Calculate both horizon and zenith obstruction angles in a single request",
                    "tags": ["Obstruction Calculation"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ObstructionCalculationRequest"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Both angles calculated successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string", "example": "success"},
                                            "data": {"$ref": "#/components/schemas/CombinedObstructionResponse"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request - invalid input",
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
                    "summary": "Calculate obstruction angles for multiple directions",
                    "description": "Calculate horizon and zenith angles for multiple directions around a window",
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
                            "description": "Multi-direction angles calculated successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string", "example": "success"},
                                            "data": {"$ref": "#/components/schemas/MultiDirectionResponse"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request - invalid input",
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
        """Generate OpenAPI schemas from Pydantic models"""
        return {
            "ObstructionCalculationRequest": {
                "type": "object",
                "required": ["x", "y", "z", "direction_angle", "mesh"],
                "properties": {
                    "x": {"type": "number", "description": "Window center X coordinate"},
                    "y": {"type": "number", "description": "Window center Y coordinate"},
                    "z": {"type": "number", "description": "Window center Z coordinate (height)"},
                    "direction_angle": {
                        "type": "number",
                        "description": "Window direction angle in radians (0-2π)"
                    },
                    "mesh": {
                        "oneOf": [
                            {
                                "type": "array",
                                "items": {
                                    "type": "array",
                                    "items": {"type": "number"},
                                    "minItems": 3,
                                    "maxItems": 3
                                },
                                "description": "Flat list of vertices [[x,y,z],...]"
                            },
                            {
                                "type": "object",
                                "properties": {
                                    "horizon": {
                                        "type": "array",
                                        "items": {
                                            "type": "array",
                                            "items": {"type": "number"}
                                        }
                                    },
                                    "zenith": {
                                        "type": "array",
                                        "items": {
                                            "type": "array",
                                            "items": {"type": "number"}
                                        }
                                    }
                                },
                                "description": "Nested format {horizon: [...], zenith: [...]}"
                            }
                        ]
                    }
                },
                "example": {
                    "x": 0.0,
                    "y": 0.0,
                    "z": 3.0,
                    "direction_angle": 0.0,
                    "mesh": {
                        "horizon": [
                            [10.0, -5.0, 0.0],
                            [10.0, -5.0, 5.0],
                            [10.0, 5.0, 0.0]
                        ]
                    }
                }
            },
            "MultiDirectionRequest": {
                "type": "object",
                "required": ["x", "y", "z", "direction_angle", "mesh"],
                "properties": {
                    "x": {"type": "number"},
                    "y": {"type": "number"},
                    "z": {"type": "number"},
                    "direction_angle": {"type": "number"},
                    "mesh": {
                        "type": "array",
                        "items": {"type": "array", "items": {"type": "number"}}
                    },
                    "num_directions": {"type": "integer", "default": 64},
                    "start_angle_degrees": {"type": "number", "default": -90.0},
                    "end_angle_degrees": {"type": "number", "default": 90.0}
                }
            },
            "Point3DResponse": {
                "type": "object",
                "properties": {
                    "x": {"type": "number"},
                    "y": {"type": "number"},
                    "z": {"type": "number"}
                }
            },
            "ObstructionAngleResponse": {
                "type": "object",
                "properties": {
                    "obstruction_angle_degrees": {"type": "number"},
                    "obstruction_angle_radians": {"type": "number"},
                    "highest_point": {"$ref": "#/components/schemas/Point3DResponse"}
                },
                "example": {
                    "obstruction_angle_degrees": 11.31,
                    "obstruction_angle_radians": 0.197,
                    "highest_point": {"x": 10.0, "y": 0.0, "z": 5.0}
                }
            },
            "CombinedObstructionResponse": {
                "type": "object",
                "properties": {
                    "horizon": {"$ref": "#/components/schemas/ObstructionAngleResponse"},
                    "zenith": {"$ref": "#/components/schemas/ObstructionAngleResponse"}
                }
            },
            "MultiDirectionResponse": {
                "type": "object",
                "properties": {
                    "horizon_angles": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Horizon angles in degrees"
                    },
                    "zenith_angles": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Zenith angles in degrees"
                    },
                    "directions": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Direction angles in radians"
                    },
                    "num_directions": {"type": "integer"}
                }
            },
            "ErrorResponse": {
                "type": "object",
                "properties": {
                    "error": {"type": "string"},
                    "error_type": {"type": "string"}
                },
                "example": {
                    "error": "Invalid mesh format",
                    "error_type": "ValueError"
                }
            },
            "StatusResponse": {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "version": {"type": "string"},
                    "services": {"type": "object"}
                },
                "example": {
                    "status": "running",
                    "version": "1.0.0"
                }
            }
        }
