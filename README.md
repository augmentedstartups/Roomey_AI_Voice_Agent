# 🎙️ Roomey AI Voice Agent

<p align="center">
  <img src="assets/IMG_1982.JPG" alt="Roomey Device" width="100%"/>
</p>

<p align="center">
  <img src="assets/Main logo_purple.png" alt="Augmented AI Logo" width="300"/>
</p>

## 🚀 Introducing Roomey

Roomey is an ultra-low latency AI Voice Agent designed to seamlessly integrate into your daily life. With lightning-fast response times and advanced natural language processing, Roomey understands your commands and questions with remarkable accuracy.

### 📺 See Roomey in Action

<p align="center">
  <a href="https://youtube.com/shorts/UeJxdjDLhfI?feature=share" target="_blank">
    <img src="https://img.youtube.com/vi/UeJxdjDLhfI/0.jpg" alt="Roomey Demo Video" width="400"/>
  </a>
</p>

## ✨ Features

- **Ultra-Low Latency**: Get responses in milliseconds, not seconds
- **Natural Conversations**: Engage in fluid, human-like dialogue
- **Web Search**: Find information from the internet instantly
- **Smart Home Control**: Adjust lights and other connected devices
- **Financial Data**: Get real-time stock prices and market information
- **Calendar Integration**: Access your Google Calendar events and appointments
- **Contextual Memory**: Roomey remembers your preferences and previous conversations
- **LinkedIn Post Generation**: Generate viral LinkedIn posts based on provided context

## 🔧 Integrations

- **Google Calendar**: Access your schedule and upcoming events
- **Smart Home Devices**: Control lights and other connected devices
- **Financial APIs**: Get real-time stock market data
- **Web Search**: Find information from across the internet

## 🔮 Coming Soon

- [ ] **MCP Integration**: Enhanced capabilities through Model Context Protocol
- [ ] **Additional Tools**: Expanding Roomey's functionality with more integrations
- [ ] **Voice Customization**: Personalize Roomey's voice to your preferences
- [ ] **Multi-room Support**: Seamless experience across your entire home

## 🛠️ Technical Architecture

Roomey is built on a modular architecture that allows for easy expansion and customization:

- **Voice Recognition**: Advanced speech-to-text processing
- **Natural Language Understanding**: Contextual comprehension of user requests
- **Agent Framework**: Intelligent decision-making and task execution
- **Integration Layer**: Connects to various services and APIs
- **Voice Synthesis**: Natural-sounding text-to-speech responses

## 🚀 Getting Started

Follow these steps to set up and run Roomey on your system:

### Prerequisites

- Python 3.9+ installed on your system
- Git for cloning the repository
- Internet connection for API access
- Google Gemini API key 

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/augmentedstartups/Roomey_AI_Voice_Agent.git
   cd Roomey_AI_Voice_Agent
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv myenv
   ```

3. **Activate the environment**
   ```bash
   source myenv/bin/activate  # On macOS/Linux
   myenv\bin\activate  # On Windows
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt  # On macOS
   pip install -r windows_requirements.txt  # On linux/windows
   ```

5. **Set up environment variables**
   - Copy the `.env.sample` file to `.env` in the root directory
   - Update the environment variables
   - The `PERSONALIZED_PROMPT` allows you to customize the AI's understanding of who you are

6. **MCP Integration**

  - Roomey now supports dynamic MCP integration using a config file, not environment variables.
  - Configure one or more MCP servers in `integrations/mcp/mcp_servers.json` (see below).
  - The assistant can call any tool on any configured MCP server.
  - Example tool call:
    ```
    {
      "server_name": "calculator",
      "tool_name": "add",
      "parameters": {"a": 2, "b": 3}
    }
    ```

### Running Roomey

1. **Activate the environment** (if not already activated)
   ```bash
   source myenv/bin/activate
   ```

2. **Run the main application**
   ```bash
   python main_mac.py
   ```

3. **Interact with Roomey**
   - Speak naturally to Roomey
   - Ask questions, request information, or give commands
   - Explore the various integrations

## 📚 Documentation

Explore the `integrations` directory for detailed documentation on each integration module.

## 🤝 Contributing

We are a team of developers passionate about the future of AI and open-source software. With years of experience in both fields, we believe in the power of community-driven development and are excited to build tools that make AI more accessible and personalized.

We welcome all forms of contributions:

- Bug reports and feature requests
- Documentation improvements
- Code contributions
- Testing and feedback
- Community support

How to contribute:

Fork the repository
1. Create your feature branch (git checkout -b roomey/feature/amazing-feature)
2. Make your changes
3. Commit your changes (git commit -m 'Add some amazing feature')
4. Push to the branch (git push origin roomey/feature/amazing-feature)
5. Open a Pull Request

Join us in building the future of AI memory management! Your contributions help make Roomey even better for everyone.

## MCP Integration (Multi-Server, Dynamic Launch)

Roomey can now launch and connect to any number of MCP servers, defined in a JSON config file. No environment variable is needed to enable MCP; if `integrations/mcp/mcp_servers.json` exists and is valid, all servers will be launched and available as tools.

### Configuration

1. **Edit or create `integrations/mcp/mcp_servers.json`:**

```json
{
  "mcpServers": {
    "calculator": {
      "command": "uvx",
      "args": ["mcp-server-calculator"]
    }
  }
}
```

- Each server entry defines how to launch the server (command, args, and optional env vars).
- You can add as many servers as you like.
- The config file path can be overridden with the `MCP_CONFIG_PATH` environment variable.

2. **On startup, Roomey will:**
   - Launch each server as a subprocess.
   - Wait briefly for servers to start.
   - Register a `call_mcp_tool` function for Gemini, allowing you to call any tool on any configured server.

### Usage

- The `call_mcp_tool` function is available if at least one server is configured.
- You can call tools on any server by specifying the `server_name` (as in the config), `tool_name`, and parameters.

### Example

To add a new server, add an entry to `mcp_servers.json`:

```json
"my_custom_server": {
  "command": "uvx",
  "args": ["npx", "-y", "@modelcontextprotocol/server-custom", "--option"]
}
```

**Note:** MCP integration is now fully config-driven. There is no need for any MCP-related environment variable.

---

<p align="left">
  <a href="https://augmentedstartups.com">
    <img src="assets/Main logo_purple.png" alt="Augmented AI Logo" width="300"/>
  </a>
  <br>
</p>