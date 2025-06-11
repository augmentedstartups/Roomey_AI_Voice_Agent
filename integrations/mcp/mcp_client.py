import os
import json
import subprocess
import time
import asyncio
import shutil # Import shutil for path discovery
from contextlib import AsyncExitStack
# Correct import for the official MCP client
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MCP_CONFIG_PATH = os.getenv("MCP_CONFIG_PATH", os.path.join(os.path.dirname(__file__), "mcp_servers.json"))


def load_mcp_server_config(path=MCP_CONFIG_PATH):
    with open(path, "r") as f:
        return json.load(f)["mcpServers"]


class MultiMCPClient:
    def __init__(self):
        self.processes = {}
        self.clients = {}
        self.exit_stack = AsyncExitStack() # For managing async contexts
        self._initialized = False
        self.config = load_mcp_server_config()
        self._gemini_tool_declarations = []
        self._gemini_tool_map = {} # Maps gemini_tool_name to (server_name, original_tool_name)

    async def initialize(self):
        if self._initialized:
            return

        self.processes = launch_mcp_servers(self.config)
        # Give servers some time to start up
        await asyncio.sleep(3)

        for name, server_info in self.config.items():
            try:
                # Use StdioServerParameters to configure the client
                server_params_obj = StdioServerParameters(
                    command=server_info["command"],
                    args=server_info["args"],
                    env=server_info.get("env")
                )
                read_stream, write_stream = await self.exit_stack.enter_async_context(stdio_client(server_params_obj))
                session = await self.exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
                await session.initialize()
                self.clients[name] = session
                print(f"[MCP] Successfully connected to {name} server.")

                # Log and store available tools for this specific MCP server
                try:
                    tools_response = await session.list_tools()
                    if tools_response and tools_response.tools:
                        
                        for tool in tools_response.tools:
                            gemini_tool_name = f"mcp_{name}_{tool.name}"
                            # Convert MCP tool declaration to Gemini format
                            gemini_decl = {
                                "name": gemini_tool_name,
                                "description": f"Tool from {name} server: {tool.description}",
                                "parameters": tool.inputSchema  # Use the schema directly, not as JSON string
                            }
                            self._gemini_tool_declarations.append(gemini_decl)
                            self._gemini_tool_map[gemini_tool_name] = (name, tool.name)
                            
                    else:
                        print(f"[MCP] No tools found from {name} server.")
                except Exception as tool_list_e:
                    print(f"[MCP] Error listing tools from {name} server: {tool_list_e}")

            except Exception as e:
                print(f"[MCP] Failed to connect to {name} server: {e}")
                # Optionally, re-raise or handle as needed
        self._initialized = True

    def get_gemini_tool_declarations(self):
        return self._gemini_tool_declarations

    async def execute_gemini_mcp_tool(self, gemini_tool_name, parameters):
        if not self._initialized:
            await self.initialize()

        server_name, original_tool_name = self._gemini_tool_map.get(gemini_tool_name, (None, None))
        if not server_name or not original_tool_name:
            raise ValueError(f"Unknown Gemini MCP tool name: {gemini_tool_name}")

        if server_name not in self.clients:
            raise ValueError(f"MCP server '{server_name}' not configured or failed to connect.")
        
        client_session = self.clients[server_name]
        print(f"[MCP] Executing Gemini-mapped tool: {gemini_tool_name} (Server: {server_name}, Original: {original_tool_name}) with params: {parameters}")
        return await client_session.call_tool(original_tool_name, arguments=parameters)

    async def cleanup(self):
        # Clear initialized flag to prevent further operations
        self._initialized = False
        
        # Clear clients first to prevent new operations
        clients_to_close = list(self.clients.items())
        self.clients.clear()
        
        # Close client sessions with robust error handling
        for name, client_session in clients_to_close:
            try:
                await client_session.aclose()
                print(f"[MCP] Closed client session for {name}.")
            except Exception as e:
                print(f"[MCP] Error closing client session for {name}: {e}")

        # Skip AsyncExitStack cleanup to avoid anyio issues during shutdown
        # The exit stack will be garbage collected naturally
        print(f"[MCP] Skipping AsyncExitStack cleanup to avoid shutdown issues.")
        
        # Terminate subprocesses with enhanced error handling
        processes_to_cleanup = list(self.processes.items())
        self.processes.clear()
        
        for name, proc in processes_to_cleanup:
            try:
                if proc.poll() is None: # If process is still running
                    print(f"[MCP] Terminating {name} server with PID {proc.pid}")
                    proc.terminate()
                    
                    # Give it a moment to terminate gracefully
                    try:
                        proc.wait(timeout=2)
                        print(f"[MCP] {name} server terminated gracefully.")
                    except subprocess.TimeoutExpired:
                        # Force kill if it doesn't terminate within timeout
                        proc.kill()
                        print(f"[MCP] Forcefully killed {name} server with PID {proc.pid}")
                        try:
                            proc.wait(timeout=1)
                        except subprocess.TimeoutExpired:
                            print(f"[MCP] Warning: {name} server may still be running.")
                else:
                    print(f"[MCP] {name} server already terminated (PID: {proc.pid})")
            except Exception as e:
                print(f"[MCP] Error during {name} server cleanup: {e}")
        
        print(f"[MCP] All MCP servers cleanup completed.")

def launch_mcp_servers(config):
    processes = {}
    # Dynamically find the Node.js binary path
    nodejs_bin_path = os.getenv("NODEJS_BIN_PATH")

    # Determine npx_path and node_path early for consistent access
    npx_path = shutil.which("npx")
    node_path = shutil.which("node")

    if not nodejs_bin_path:
        # Try to find npx directly
        if npx_path:
            nodejs_bin_path = os.path.dirname(npx_path)
        else:
            # If npx not found, try to find node and infer npx path
            if node_path:
                nodejs_bin_path = os.path.dirname(node_path)

    if not nodejs_bin_path:
        print("[MCP] Warning: Could not automatically find Node.js binary path. MCP servers may fail to launch if npx/node is not in system PATH or NODEJS_BIN_PATH is not set.")

    for name, server in config.items():
        env = os.environ.copy()

        # Build the command list to execute
        command_list = [server["command"]] + server["args"]

        # Special handling for .cmd/.bat files on Windows to resolve WinError 2
        # Use cmd.exe /c to explicitly run the command
        if os.name == 'nt' and command_list and command_list[0].lower() == 'npx' and npx_path:
            command_list = ["cmd.exe", "/c", npx_path] + server["args"]
        
        if nodejs_bin_path:
            if "PATH" in env:
                env["PATH"] = nodejs_bin_path + os.pathsep + env["PATH"]
            else:
                env["PATH"] = nodejs_bin_path
        
        if "env" in server:
            env.update(server["env"])

        proc = subprocess.Popen(
            command_list,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        processes[name] = proc
        print(f"[MCP] Launched {name} server with PID {proc.pid}")
    return processes
