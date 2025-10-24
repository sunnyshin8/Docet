"""
Fivetran Documentation Connector

This connector fetches, processes, and stores documentation data from various sources
including Swagger/OpenAPI, ReDoc, GitHub Wiki, and other documentation platforms.
Built using the Fivetran Connector SDK with an Object-Oriented Programming approach.

See the Technical Reference documentation:
https://fivetran.com/docs/connectors/connector-sdk/technical-reference#update
"""

# Import required classes from fivetran_connector_sdk
from fivetran_connector_sdk import Connector
from fivetran_connector_sdk import Logging as log
from fivetran_connector_sdk import Operations as op

import json
from typing import Dict, List, Any
import asyncio
from datetime import datetime

# Import our existing connector system
import sys
import os

# Add the backend directory to path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from app.connectors.detector import DocumentTypeDetector
from app.connectors.registry import ConnectorRegistry  
from app.connectors.swagger_connector import SwaggerConnector

# Import table definitions
from tables.documents_table import DocumentsTable
from tables.endpoints_table import EndpointsTable
from tables.schemas_table import SchemasTable

# Selected tables for this connector
SELECTED_TABLES = [DocumentsTable, EndpointsTable, SchemasTable]


def validate_configuration(configuration: dict):
    """
    Validate the configuration dictionary to ensure it contains all required parameters.
    
    Args:
        configuration: a dictionary that holds the configuration settings for the connector.
        
    Raises:
        ValueError: if any required configuration parameter is missing.
    """
    # Validate required configuration parameters
    if "documentation_url" not in configuration:
        raise ValueError("Missing required configuration value: 'documentation_url'")
    
    # Optional parameters with defaults
    if "connector_type" not in configuration:
        configuration["connector_type"] = "auto"  # Auto-detect by default
    
    if "include_versions" not in configuration:
        configuration["include_versions"] = "true"  # Include all versions by default
    
    if "chunk_size" not in configuration:
        configuration["chunk_size"] = "1000"
    
    if "chunk_overlap" not in configuration:
        configuration["chunk_overlap"] = "200"
    
    # Convert string values to appropriate types
    configuration["include_versions"] = configuration["include_versions"].lower() == "true"
    configuration["chunk_size"] = int(configuration["chunk_size"])
    configuration["chunk_overlap"] = int(configuration["chunk_overlap"])
    
    print(f"Configuration validated for URL: {configuration['documentation_url']}")


def schema(configuration: dict):
    """
    Define the schema function which configures the schema your connector delivers.
    
    Args:
        configuration: a dictionary that holds the configuration settings for the connector.
        
    Returns:
        List of schema dictionaries for each table
    """
    print("Generating schema for documentation connector")
    
    output = []
    for table_class in SELECTED_TABLES:
        table_instance = table_class(configuration=configuration)
        schema_dict = table_instance.assign_schema()
        output.append(schema_dict)
        print(f"Added schema for table: {table_class.table_name()}")
    
    return output


async def async_update(configuration: dict, state: dict):
    """
    Async version of the update function for handling async operations.
    """
    log.info("Starting documentation connector sync")
    
    # Validate configuration
    validate_configuration(configuration=configuration)
    
    # Initialize document detector and registry
    detector = DocumentTypeDetector()
    registry = ConnectorRegistry()
    
    # Register our Swagger connector
    registry.register_connector(
        'swagger', 
        SwaggerConnector,
        supported_types=['swagger_ui', 'openapi_spec', 'redoc']
    )
    
    documentation_url = configuration["documentation_url"]
    connector_type = configuration.get("connector_type", "auto")
    
    try:
        # Step 1: Detect document type if auto-detection is enabled
        if connector_type == "auto":
            log.info(f"Auto-detecting document type for: {documentation_url}")
            detection_result = await detector.detect_document_type(documentation_url)
            detected_type = detection_result['type']
            confidence = detection_result['confidence']
            
            log.info(f"Detected type: {detected_type} (confidence: {confidence})")
            
            # Get appropriate connector
            connector_class = registry.get_connector_for_type(detected_type)
            if not connector_class:
                raise ValueError(f"No connector available for detected type: {detected_type}")
        else:
            # Use specified connector type
            connector_class = registry.get_connector_by_name(connector_type)
            if not connector_class:
                raise ValueError(f"Unknown connector type: {connector_type}")
        
        # Step 2: Extract documentation using the connector
        log.info(f"Extracting documentation using {connector_class.__name__}")
        
        async with connector_class(documentation_url) as connector:
            # Get source information and versions
            source_info = await connector.get_document_source_info()
            
            log.info(f"Found {len(source_info.versions)} versions for {source_info.title}")
            
            # Process each version
            all_documents = []
            version_stats = {}
            
            for version_info in source_info.versions:
                log.info(f"Processing version: {version_info.version}")
                
                try:
                    documents = await connector.extract_documents_for_version(version_info)
                    all_documents.extend(documents)
                    version_stats[version_info.version] = {
                        'documents_count': len(documents),
                        'status': 'success'
                    }
                    
                    log.info(f"Extracted {len(documents)} documents from version {version_info.version}")
                    
                except Exception as e:
                    log.error(f"Error processing version {version_info.version}: {str(e)}")
                    version_stats[version_info.version] = {
                        'documents_count': 0,
                        'status': 'error',
                        'error': str(e)
                    }
            
            # Step 3: Process data for each table
            sync_timestamp = datetime.utcnow().isoformat()
            
            for table_class in SELECTED_TABLES:
                table_instance = table_class(configuration=configuration)
                
                log.info(f"Processing data for table: {table_class.table_name()}")
                
                # Process documents based on table type
                table_data = table_instance.process_documents(
                    documents=all_documents,
                    source_info=source_info,
                    sync_timestamp=sync_timestamp,
                    state=state
                )
                
                # Upsert data to Fivetran
                for row in table_data:
                    op.upsert(table_class.table_name(), row)
                
                log.info(f"Upserted {len(table_data)} rows to {table_class.table_name()}")
            
            # Update state for next sync
            state['last_sync'] = sync_timestamp
            state['last_url'] = documentation_url
            state['documents_processed'] = len(all_documents)
            state['version_stats'] = version_stats
            
            log.info(f"Sync completed successfully. Processed {len(all_documents)} documents")
            
    except Exception as e:
        log.error(f"Error during documentation sync: {str(e)}")
        raise
    
    finally:
        await detector.close()


def update(configuration: dict, state: dict):
    """
    Define the update function, which is required and called by Fivetran during each sync.
    
    Args:
        configuration: A dictionary containing connection details
        state: A dictionary containing state information from previous runs
    """
    log.info("Documentation Connector - Starting sync")
    
    # Run the async update function
    try:
        asyncio.run(async_update(configuration, state))
    except Exception as e:
        log.error(f"Sync failed: {str(e)}")
        raise


# Create the connector object for Fivetran
connector = Connector(update=update, schema=schema)


# Main entry point for testing
if __name__ == "__main__":
    # Debug: Print current working directory
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script directory: {os.path.dirname(__file__)}")
    
    # Try multiple configuration file locations
    config_paths = [
        "configuration.json",  # Current directory
        os.path.join(os.path.dirname(__file__), "configuration.json"),  # Script directory
        os.path.join(os.getcwd(), "configuration.json")  # Working directory
    ]
    
    configuration = None
    for config_path in config_paths:
        print(f"Trying config path: {config_path}")
        try:
            with open(config_path, "r") as f:
                configuration = json.load(f)
            print(f"Found configuration at: {config_path}")
            break
        except FileNotFoundError:
            continue
    
    if configuration:
        print("Testing documentation connector locally")
        connector.debug(configuration=configuration)
    else:
        print("configuration.json file not found. Please create it with required parameters.")
        print("\nExample configuration.json:")
        print(json.dumps({
            "documentation_url": "https://petstore.swagger.io/",
            "connector_type": "auto",
            "include_versions": True,
            "chunk_size": 1000,
            "chunk_overlap": 200
        }, indent=2))