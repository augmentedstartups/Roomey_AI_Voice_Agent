import os
import json
import asyncio
import warnings
import sys
import io
from contextlib import redirect_stderr, redirect_stdout
from mcp_use import MCPClient
from mcp_use.connectors.stdio import StdioConnector

# Suppress mcp-use warnings about non-text/non-data parts globally
warnings.filterwarnings("ignore", message=".*non-text parts.*")
warnings.filterwarnings("ignore", message=".*non-data parts.*")
warnings.filterwarnings("ignore", message=".*returning concatenated.*")
warnings.filterwarnings("ignore", message=".*executable_code.*")
warnings.filterwarnings("ignore", message=".*code_execution_result.*")

# More comprehensive warning suppression for all mcp-use related modules
try:
    import mcp_use
    warnings.filterwarnings("ignore", category=UserWarning, module="mcp_use.*")
    warnings.filterwarnings("ignore", category=UserWarning, module=".*mcp.*")
except ImportError:
    pass

MCP_CONFIG_PATH = os.getenv("MCP_CONFIG_PATH", os.path.join(os.path.dirname(__file__), "mcp_servers.json"))


def load_mcp_server_config(path=MCP_CONFIG_PATH):
    with open(path, "r") as f:
        return json.load(f)["mcpServers"]


class MultiMCPClient:
    def __init__(self):
        self.mcp_client = None
        self.sessions = {}
        self._initialized = False
        self.config = load_mcp_server_config()
        self._tool_declarations = []
        self._tool_map = {}  # Maps tool_name to (server_name, original_tool_name)

    async def initialize(self):
        if self._initialized:
            return

        if not self.config:
            print("[MCP] No MCP servers configured.")
            return

        try:
            # Convert config to mcp-use format
            mcp_use_config = {}
            for name, server_info in self.config.items():
                mcp_use_config[name] = {
                    "command": server_info["command"],
                    "args": server_info["args"],
                    "env": server_info.get("env", {})
                }

            # Create MCPClient with config
            self.mcp_client = MCPClient.from_dict({"mcpServers": mcp_use_config})
            
            print(f"[MCP] Attempting to connect to {len(mcp_use_config)} server(s)...")
            
            # Create sessions for all servers with better error handling
            successful_sessions = {}
            for server_name in mcp_use_config.keys():
                try:
                    print(f"[MCP] Connecting to {server_name} server...")
                    session = await self.mcp_client.create_session(server_name, auto_initialize=True)
                    successful_sessions[server_name] = session
                    print(f"[MCP] Successfully connected to {server_name} server.")
                except Exception as e:
                    print(f"[MCP] Failed to connect to {server_name} server: {e}")
                    # Continue with other servers
                    continue
            
            self.sessions = successful_sessions
            
            if not self.sessions:
                print("[MCP] No MCP servers could be connected.")
                self._initialized = False
                return
            
            print(f"[MCP] Successfully connected to {len(self.sessions)} server(s).")

            # Collect tools from all sessions
            for server_name, session in self.sessions.items():
                try:
                    # Get connector from session to access tools
                    connector = session.connector
                    if hasattr(connector, 'tools') and connector.tools:
                        for tool in connector.tools:
                            tool_name = f"mcp_{server_name}_{tool.name}"
                            
                            # Clean up the input schema to remove unsupported properties
                            cleaned_schema = self._clean_json_schema(tool.inputSchema)
                            
                            # Convert MCP tool declaration to standard format
                            tool_decl = {
                                "name": tool_name,
                                "description": f"Tool from {server_name} server: {tool.description}",
                                "parameters": cleaned_schema
                            }
                            self._tool_declarations.append(tool_decl)
                            self._tool_map[tool_name] = (server_name, tool.name)
                            
                        print(f"[MCP] Found {len(connector.tools)} tools from {server_name} server.")
                    else:
                        print(f"[MCP] No tools found from {server_name} server.")
                except Exception as tool_list_e:
                    print(f"[MCP] Error listing tools from {server_name} server: {tool_list_e}")

            self._initialized = len(self.sessions) > 0

        except Exception as e:
            print(f"[MCP] Failed to initialize MCP client: {e}")
            self._initialized = False

    def _clean_json_schema(self, schema):
        """
        Clean JSON schema to remove properties not supported by Gemini API.
        Recursively removes unsupported properties while preserving structure.
        """
        if not isinstance(schema, dict):
            return schema
        
        # Properties to remove that are not supported by Gemini
        unsupported_properties = {
            '$schema', 'additionalProperties', 'exclusiveMinimum', 'exclusiveMaximum',
            'multipleOf', 'patternProperties', 'dependencies', 'definitions',
            'allOf', 'anyOf', 'oneOf', 'not', 'if', 'then', 'else', ''
        }
        
        cleaned = {}
        for key, value in schema.items():
            if key in unsupported_properties:
                continue
                
            if isinstance(value, dict):
                cleaned[key] = self._clean_json_schema(value)
            elif isinstance(value, list):
                cleaned[key] = [
                    self._clean_json_schema(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                cleaned[key] = value
        
        return cleaned

    def _process_mcp_result(self, result):
        """
        Process MCP tool result to handle different response types properly.
        This reduces warnings from mcp-use library about non-text/non-data parts.
        """
        try:
            # If result has content parts, extract them properly
            if hasattr(result, 'content') and result.content:
                processed_content = []
                
                for content_part in result.content:
                    if hasattr(content_part, 'type'):
                        if content_part.type == 'text':
                            # Extract text content
                            if hasattr(content_part, 'text'):
                                processed_content.append({
                                    'type': 'text',
                                    'text': content_part.text
                                })
                        elif content_part.type == 'image':
                            # Handle image content
                            processed_content.append({
                                'type': 'image',
                                'data': getattr(content_part, 'data', None)
                            })
                        elif content_part.type == 'resource':
                            # Handle resource content
                            processed_content.append({
                                'type': 'resource',
                                'resource': getattr(content_part, 'resource', None)
                            })
                        elif content_part.type == 'executable_code':
                            # Handle executable code - extract the code
                            code = getattr(content_part, 'code', '')
                            language = getattr(content_part, 'language', 'text')
                            processed_content.append({
                                'type': 'text',
                                'text': f"Code ({language}):\n{code}"
                            })
                        elif content_part.type == 'code_execution_result':
                            # Handle code execution result
                            output = getattr(content_part, 'output', '')
                            processed_content.append({
                                'type': 'text',
                                'text': f"Execution Result:\n{output}"
                            })
                        else:
                            # Handle other content types as text
                            text_content = str(content_part)
                            processed_content.append({
                                'type': 'text',
                                'text': text_content
                            })
                    else:
                        # Fallback: convert to string
                        processed_content.append({
                            'type': 'text',
                            'text': str(content_part)
                        })
                
                # Return processed result with cleaned content
                if processed_content:
                    # Combine all text content for simpler handling
                    combined_text = []
                    for item in processed_content:
                        if item['type'] == 'text':
                            combined_text.append(item['text'])
                        else:
                            combined_text.append(str(item))
                    
                    return {
                        'content': '\n'.join(combined_text),
                        'isError': getattr(result, 'isError', False)
                    }
                
            # If no content parts, try to extract text directly
            if hasattr(result, 'text'):
                return {'content': result.text, 'isError': getattr(result, 'isError', False)}
            
            # Fallback: convert entire result to string
            return {'content': str(result), 'isError': False}
            
        except Exception as e:
            print(f"[MCP] Warning: Error processing result: {e}")
            # Fallback to original result
            return result

    def get_tool_declarations(self):
        return self._tool_declarations

    async def execute_mcp_tool(self, tool_name, parameters):
        if not self._initialized:
            await self.initialize()

        server_name, original_tool_name = self._tool_map.get(tool_name, (None, None))
        if not server_name or not original_tool_name:
            raise ValueError(f"Unknown MCP tool name: {tool_name}")

        if server_name not in self.sessions:
            raise ValueError(f"MCP server '{server_name}' not configured or failed to connect.")
        
        session = self.sessions[server_name]
        print(f"[MCP] Executing tool: {tool_name} (Server: {server_name}, Original: {original_tool_name}) with params: {parameters}")
        
        try:
            # Create a custom stderr filter to suppress mcp-use warnings
            class WarningFilter:
                def __init__(self, original_stderr):
                    self.original_stderr = original_stderr
                    self.buffer = []
                
                def write(self, text):
                    # Filter out specific warning patterns
                    if any(pattern in text.lower() for pattern in [
                        'warning: there are non-text parts',
                        'warning: there are non-data parts', 
                        'returning concatenated',
                        'executable_code',
                        'code_execution_result'
                    ]):
                        return  # Suppress this warning
                    
                    # Pass through other messages
                    self.original_stderr.write(text)
                
                def flush(self):
                    self.original_stderr.flush()
                
                def __getattr__(self, name):
                    return getattr(self.original_stderr, name)
            
            # Temporarily replace stderr to filter warnings
            original_stderr = sys.stderr
            filtered_stderr = WarningFilter(original_stderr)
            
            try:
                sys.stderr = filtered_stderr
                
                # Suppress warnings and execute tool
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", message=".*non-text parts.*")
                    warnings.filterwarnings("ignore", message=".*non-data parts.*")
                    warnings.filterwarnings("ignore", category=UserWarning, module="mcp_use")
                    
                    # Use the connector's call_tool method
                    result = await session.connector.call_tool(original_tool_name, parameters)
            finally:
                # Restore original stderr
                sys.stderr = original_stderr
            
            # Process the result to handle different response types properly
            processed_result = self._process_mcp_result(result)
            return processed_result
        except Exception as e:
            print(f"[MCP] Error executing tool {original_tool_name}: {e}")
            raise

    async def cleanup(self):
        print("[MCP] Starting cleanup process...")
        
        # Set a flag to prevent further operations
        self._initialized = False
        
        try:
            if self.sessions:
                # Close individual sessions first with timeout
                for server_name, session in list(self.sessions.items()):
                    try:
                        print(f"[MCP] Closing session for {server_name}...")
                        if hasattr(session, 'disconnect'):
                            await asyncio.wait_for(session.disconnect(), timeout=2.0)
                        elif hasattr(session.connector, 'disconnect'):
                            await asyncio.wait_for(session.connector.disconnect(), timeout=2.0)
                        print(f"[MCP] Session for {server_name} closed successfully.")
                    except asyncio.TimeoutError:
                        print(f"[MCP] Timeout closing session for {server_name}")
                    except Exception as e:
                        print(f"[MCP] Error closing session for {server_name}: {e}")
                
            if self.mcp_client:
                try:
                    # Close all sessions using mcp-use client with timeout
                    await asyncio.wait_for(self.mcp_client.close_all_sessions(), timeout=3.0)
                    print("[MCP] All sessions closed via MCP client.")
                except asyncio.TimeoutError:
                    print("[MCP] Timeout closing MCP client sessions")
                except Exception as e:
                    print(f"[MCP] Error closing MCP client sessions: {e}")
                
            # Clear references
            self.sessions.clear()
            self.mcp_client = None
            self._tool_declarations.clear()
            self._tool_map.clear()
            
        except Exception as e:
            print(f"[MCP] Error during cleanup: {e}")
        finally:
            print("[MCP] Cleanup completed successfully")
