"""
Schema validation service using JSON Schema.

This service provides validation capabilities for data payloads using 
JSON Schema files generated from TypeScript Zod schemas. It ensures 
type safety and consistency between frontend and backend.
"""

import json
import pathlib
from typing import Dict, Any, Optional, List
from functools import lru_cache
import logging

from jsonschema import validate as js_validate, ValidationError, Draft202012Validator
from jsonschema.exceptions import SchemaError

# Configure logging
logger = logging.getLogger(__name__)

# Schema directory path
SCHEMA_DIR = pathlib.Path(__file__).resolve().parent.parent / "schema" / "json"


class SchemaValidationError(Exception):
    """Custom exception for schema validation errors."""
    
    def __init__(self, schema_name: str, message: str, validation_errors: Optional[List[str]] = None):
        self.schema_name = schema_name
        self.validation_errors = validation_errors or []
        super().__init__(message)


class SchemaNotFoundError(Exception):
    """Exception raised when a requested schema file is not found."""
    
    def __init__(self, schema_name: str):
        self.schema_name = schema_name
        super().__init__(f"Schema '{schema_name}' not found in {SCHEMA_DIR}")


@lru_cache(maxsize=32)
def load_schema(name: str) -> Dict[str, Any]:
    """
    Load and cache a JSON schema by name.
    
    Args:
        name: Schema name (without .schema.json extension)
        
    Returns:
        Parsed JSON schema dictionary
        
    Raises:
        SchemaNotFoundError: If schema file doesn't exist
        SchemaValidationError: If schema file is invalid JSON
    """
    schema_path = SCHEMA_DIR / f"{name}.schema.json"
    
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        raise SchemaNotFoundError(name)
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        
        # Validate the schema itself
        Draft202012Validator.check_schema(schema)
        
        logger.debug(f"Successfully loaded schema: {name}")
        return schema
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in schema {name}: {e}")
        raise SchemaValidationError(name, f"Invalid JSON schema file: {e}")
    
    except SchemaError as e:
        logger.error(f"Invalid JSON Schema format in {name}: {e}")
        raise SchemaValidationError(name, f"Invalid JSON Schema format: {e}")


def validate_payload(name: str, data: Dict[str, Any], strict: bool = True) -> None:
    """
    Validate a data payload against a named schema.
    
    Args:
        name: Schema name to validate against
        data: Data payload to validate
        strict: If True, raise exception on validation failure.
                If False, log warning and continue.
                
    Raises:
        SchemaValidationError: If validation fails and strict=True
        SchemaNotFoundError: If schema doesn't exist
    """
    try:
        schema = load_schema(name)
        
        # Create validator instance for better error reporting
        validator = Draft202012Validator(schema)
        
        # Perform validation
        errors = list(validator.iter_errors(data))
        
        if errors:
            error_messages = []
            for error in errors:
                # Build a more readable error message
                path = " -> ".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
                error_messages.append(f"At '{path}': {error.message}")
            
            error_summary = f"Validation failed for schema '{name}'"
            full_message = f"{error_summary}:\n" + "\n".join(f"  - {msg}" for msg in error_messages)
            
            if strict:
                logger.error(full_message)
                raise SchemaValidationError(name, error_summary, error_messages)
            else:
                logger.warning(full_message)
        else:
            logger.debug(f"Payload successfully validated against schema: {name}")
            
    except (SchemaNotFoundError, SchemaValidationError):
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error during validation of {name}: {e}")
        raise SchemaValidationError(name, f"Unexpected validation error: {e}")


def get_available_schemas() -> List[str]:
    """
    Get list of available schema names.
    
    Returns:
        List of schema names (without .schema.json extension)
    """
    if not SCHEMA_DIR.exists():
        logger.warning(f"Schema directory does not exist: {SCHEMA_DIR}")
        return []
    
    schemas = []
    for schema_file in SCHEMA_DIR.glob("*.schema.json"):
        schema_name = schema_file.stem.replace(".schema", "")
        schemas.append(schema_name)
    
    return sorted(schemas)


def validate_multiple_payloads(validations: List[tuple[str, Dict[str, Any]]], 
                             strict: bool = True) -> Dict[str, Optional[List[str]]]:
    """
    Validate multiple payloads against their respective schemas.
    
    Args:
        validations: List of (schema_name, payload) tuples
        strict: If True, raise exception on first validation failure
        
    Returns:
        Dictionary mapping schema names to validation errors (None if valid)
        
    Raises:
        SchemaValidationError: If any validation fails and strict=True
    """
    results = {}
    
    for schema_name, payload in validations:
        try:
            validate_payload(schema_name, payload, strict=False)
            results[schema_name] = None  # No errors
        except SchemaValidationError as e:
            results[schema_name] = e.validation_errors
            if strict:
                raise
    
    return results


# Convenience functions for common schemas
def validate_company(data: Dict[str, Any], strict: bool = True) -> None:
    """Validate Company payload."""
    validate_payload("Company", data, strict)


def validate_product(data: Dict[str, Any], strict: bool = True) -> None:
    """Validate Product payload."""
    validate_payload("Product", data, strict)


def validate_signal(data: Dict[str, Any], strict: bool = True) -> None:
    """Validate Signal payload."""
    validate_payload("Signal", data, strict)


def validate_capability(data: Dict[str, Any], strict: bool = True) -> None:
    """Validate Capability payload."""
    validate_payload("Capability", data, strict)


# Health check for schema system
def schema_system_health() -> Dict[str, Any]:
    """
    Check health of schema validation system.
    
    Returns:
        Health status dictionary with schema availability and errors
    """
    health = {
        "status": "healthy",
        "schema_directory_exists": SCHEMA_DIR.exists(),
        "available_schemas": [],
        "errors": []
    }
    
    try:
        health["available_schemas"] = get_available_schemas()
        
        if not health["schema_directory_exists"]:
            health["status"] = "degraded"
            health["errors"].append(f"Schema directory not found: {SCHEMA_DIR}")
        
        if not health["available_schemas"]:
            health["status"] = "degraded" 
            health["errors"].append("No schema files found")
            
    except Exception as e:
        health["status"] = "unhealthy"
        health["errors"].append(f"Error checking schema system: {e}")
    
    return health
