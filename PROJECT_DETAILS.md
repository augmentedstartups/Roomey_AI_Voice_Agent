# 🎙️ Roomey AI Voice Agent - Project Details

## 📋 Project Overview

Roomey is an ultra-low latency AI Voice Agent designed to seamlessly integrate into daily life through natural voice interactions. Built with Python and powered by Google's Gemini API, Roomey provides lightning-fast responses and advanced natural language processing capabilities with remarkable accuracy.

### 🎯 Core Purpose
- Provide ultra-low latency voice-based AI assistance
- Integrate with multiple services and smart home devices
- Offer natural, conversational interactions
- Support extensible functionality through modular integrations

### 🏗️ Technical Architecture
- **Voice Recognition**: Advanced speech-to-text processing using Google's Gemini API
- **Natural Language Understanding**: Contextual comprehension powered by Gemini 2.5 Flash
- **Agent Framework**: Intelligent decision-making and task execution
- **Integration Layer**: Modular system connecting to various services and APIs
- **Voice Synthesis**: Natural-sounding text-to-speech responses
- **MCP Support**: Model Context Protocol integration for extensible functionality

## ✨ Features

### 🎤 Core Voice Features
- **Ultra-Low Latency**: Millisecond response times
- **Natural Conversations**: Fluid, human-like dialogue
- **Push-to-Talk**: Press 't' to toggle audio recording
- **Contextual Memory**: Remembers preferences and previous conversations
- **Real-time Audio Processing**: Continuous audio streaming with activity detection

### 🌐 Web & Information
- **Web Search**: Find information from the internet instantly using Google Search
- **Real-time Data**: Access to current information and live data

### 🏠 Smart Home Integration
- **Home Assistant Control**: Adjust lights and other connected devices
- **Climate Control**: Manage thermostats and HVAC systems
- **Room-based Control**: Control devices by room or area
- **Entity Discovery**: Find and control devices by name

### 📅 Productivity Features
- **Google Calendar Integration**: Access schedule and upcoming events
- **Reminder System**: Set, manage, and track personal reminders
- **LinkedIn Post Generation**: Create viral LinkedIn posts from context

### 🔧 Advanced Features
- **MCP Integration**: Dynamic server connections through Model Context Protocol
- **Multi-modal Support**: Text, voice, and optional video/screen capture
- **Conversation Logging**: Optional logging of all interactions
- **Modular Architecture**: Easy to extend with new integrations

## 📁 Project Structure

```
Roomey_AI_Voice_Agent/
├── 📄 main_mac.py              # Main application entry point for macOS
├── 📄 main_rpi.py              # Main application for Raspberry Pi
├── 📄 tools.py                 # Core tools and function declarations
├── 📄 requirements.txt         # Python dependencies for macOS
├── 📄 windows_requirements.txt # Python dependencies for Windows/Linux
├── 📄 .env.sample             # Environment variables template
├── 📄 .gitignore              # Git ignore rules
├── 📄 README.md               # Project documentation
├── 📄 CHANGELOG.md            # Version history
├── 📄 sample.pcm              # Sample audio file
├── 📁 assets/                 # Media and branding assets
│   ├── 🖼️ IMG_1982.JPG        # Device photo
│   └── 🖼️ Main logo_purple.png # Augmented AI logo
├── 📁 integrations/           # Modular integration system
│   ├── 📁 calendar/           # Google Calendar integration
│   ├── 📁 homeassistant/      # Home Assistant integration
│   ├── 📁 linkedinformater/   # LinkedIn post generator
│   ├── 📁 mcp/                # Model Context Protocol
│   ├── 📁 reminders/          # Personal reminders system
│   └── 📁 respeaker_leds/     # LED control for ReSpeaker devices
├── 📁 utils/                  # Utility functions
│   └── 📄 instructions.py     # System instructions
├── 📁 archive/                # Archived/legacy code
├── 📁 logs/                   # Conversation logs (auto-created)
└── 📁 myenv/                  # Python virtual environment
```

## 🗂️ File Importance Analysis

### 🚀 Core Application Files

#### `main_mac.py` - **CRITICAL**
- **Purpose**: Primary application entry point for macOS systems
- **Key Functions**:
  - Audio processing and streaming
  - Gemini API integration and session management
  - Push-to-talk functionality using pynput
  - Error handling and graceful shutdown
  - MCP client initialization
  - Video/screen capture support
- **Dependencies**: tools.py, integrations, environment variables

#### `main_rpi.py` - **CRITICAL**
- **Purpose**: Raspberry Pi optimized version
- **Differences**: Likely optimized for ARM architecture and ReSpeaker hardware

#### `tools.py` - **CRITICAL**
- **Purpose**: Central tool management and function declarations
- **Key Functions**:
  - Tool declarations for Gemini API
  - Integration management (Calendar, Home Assistant, LinkedIn, MCP)
  - Function mapping and execution
  - Dynamic MCP tool registration
- **Architecture**: Modular system allowing conditional integration loading

### 📦 Configuration Files

#### `.env.sample` - **ESSENTIAL**
- **Purpose**: Environment variables template
- **Contains**: All configuration options for customization

#### `requirements.txt` / `windows_requirements.txt` - **ESSENTIAL**
- **Purpose**: Python dependency management
- **Contains**: All required packages for different platforms

### 🔧 Integration Modules

#### `integrations/calendar/` - **HIGH PRIORITY**
- **Purpose**: Google Calendar integration
- **Files**:
  - `google_calendar.py`: Main calendar functionality
  - `authenticate.py`: OAuth authentication
  - `test_auth.py`: Authentication testing

#### `integrations/homeassistant/` - **HIGH PRIORITY**
- **Purpose**: Smart home device control
- **Files**:
  - `ha_tools.py`: Core Home Assistant tools
  - `control_device.py`: Device control logic
  - `list_devices.py`: Device discovery

#### `integrations/mcp/` - **HIGH PRIORITY**
- **Purpose**: Model Context Protocol support
- **Files**:
  - `mcp_client.py`: MCP client implementation
  - `mcp_servers.json`: Server configuration

#### `integrations/reminders/` - **MEDIUM PRIORITY**
- **Purpose**: Personal reminder system
- **Files**:
  - `reminders.py`: Reminder management logic
  - `reminders.json`: Reminder data storage

#### `integrations/linkedinformater/` - **MEDIUM PRIORITY**
- **Purpose**: LinkedIn post generation
- **Files**:
  - `linkedin_formatter.py`: Post generation logic

#### `integrations/respeaker_leds/` - **LOW PRIORITY**
- **Purpose**: LED control for ReSpeaker hardware
- **Use Case**: Visual feedback on hardware devices

### 📊 Support Files

#### `utils/instructions.py` - **MEDIUM PRIORITY**
- **Purpose**: System instructions and prompts

#### `logs/` - **LOW PRIORITY**
- **Purpose**: Conversation logging (auto-created)
- **Format**: Daily log files with timestamped conversations

#### `archive/` - **LOW PRIORITY**
- **Purpose**: Legacy code and deprecated functionality

## 🔐 Environment Variables

### 🎯 Core Configuration

#### **GEMINI_API_KEY** - **REQUIRED**
- **Purpose**: Google Gemini API authentication
- **Usage**: Primary AI model access
- **Obtainable**: https://aistudio.google.com/apikey

#### **PERSONALIZED_PROMPT** - **RECOMMENDED**
- **Purpose**: Customize AI personality and user context
- **Default**: "You are a helpful assistant. My name is [Your Name], [add personal details here]."
- **Usage**: Helps AI understand user preferences and context

### 🌐 Optional API Keys

#### **OPENROUTER_API_KEY** - **OPTIONAL**
- **Purpose**: Alternative AI model access
- **Usage**: Fallback or alternative AI provider
- **Status**: Currently commented out

### 🔧 Integration Toggles

#### **LINKEDIN_FORMATTER_INTEGRATION** - **OPTIONAL**
- **Purpose**: Enable/disable LinkedIn post generation
- **Default**: `true`
- **Values**: `true`/`false`

#### **GOOGLE_CALENDAR_INTEGRATION** - **OPTIONAL**
- **Purpose**: Enable/disable Google Calendar features
- **Default**: `false`
- **Requires**: `GOOGLE_CALENDAR_EMAIL` if enabled

#### **HASS_INTEGRATION** - **OPTIONAL**
- **Purpose**: Enable/disable Home Assistant integration
- **Default**: `false`
- **Requires**: `HASS_URL` and `HASS_TOKEN` if enabled

### 🏠 Home Assistant Configuration

#### **HASS_URL** - **CONDITIONAL**
- **Purpose**: Home Assistant server URL
- **Example**: `http://localhost:8123`
- **Required**: Only if `HASS_INTEGRATION=true`

#### **HASS_TOKEN** - **CONDITIONAL**
- **Purpose**: Home Assistant long-lived access token
- **Security**: Keep secure, provides full HA access
- **Required**: Only if `HASS_INTEGRATION=true`

### 📅 Calendar Configuration

#### **GOOGLE_CALENDAR_EMAIL** - **CONDITIONAL**
- **Purpose**: Google Calendar account email
- **Example**: `example@example.com`
- **Required**: Only if `GOOGLE_CALENDAR_INTEGRATION=true`

### 🎛️ MCP Settings

#### **MCP_ENABLED** - **OPTIONAL**
- **Purpose**: Enable Model Context Protocol
- **Default**: `true`
- **Usage**: Enables dynamic tool integration

#### **MCP_CONFIG_PATH** - **OPTIONAL**
- **Purpose**: Custom MCP configuration file path
- **Default**: Uses `integrations/mcp/mcp_servers.json`

#### **NODEJS_BIN_PATH** - **OPTIONAL**
- **Purpose**: Custom Node.js binary path for MCP servers
- **Usage**: Required for some MCP server implementations

### 🎤 Audio Configuration

#### **CHANNELS** - **ADVANCED**
- **Purpose**: Audio channel configuration
- **Default**: `1` (mono)
- **Values**: `1` (mono) or `2` (stereo)

#### **SEND_SAMPLE_RATE** - **ADVANCED**
- **Purpose**: Audio input sample rate
- **Default**: `16000` Hz
- **Usage**: Microphone audio processing

#### **RECEIVE_SAMPLE_RATE** - **ADVANCED**
- **Purpose**: Audio output sample rate
- **Default**: `24000` Hz
- **Usage**: AI voice output

#### **CHUNK_SIZE** - **ADVANCED**
- **Purpose**: Audio buffer size
- **Default**: `1024` frames
- **Usage**: Audio processing optimization

### 🎬 Video Configuration

#### **DEFAULT_MODE** - **OPTIONAL**
- **Purpose**: Default video capture mode
- **Default**: `none`
- **Values**: `none`, `camera`, `screen`

#### **VOICE_NAME** - **OPTIONAL**
- **Purpose**: Gemini voice selection
- **Default**: `Kore`
- **Usage**: AI voice personality

### 📝 Logging Configuration

#### **LOG_CONVERSATION** - **OPTIONAL**
- **Purpose**: Enable conversation logging
- **Default**: `true`
- **Usage**: Saves all interactions to daily log files

#### **WAKEUP_WORD** - **FUTURE**
- **Purpose**: Wake word configuration
- **Default**: `hey roomey`
- **Status**: Not yet fully implemented

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Git
- Internet connection
- Google Gemini API key

### Quick Setup
1. Clone repository
2. Create virtual environment: `python -m venv myenv`
3. Activate environment: `source myenv/bin/activate` (macOS/Linux) or `myenv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.sample` to `.env` and configure
6. Run: `python main_mac.py`

### Usage
- Press 't' to toggle recording
- Speak naturally to Roomey
- Type 'q' in message prompt to quit

## 🔄 Development Workflow

### Adding New Integrations
1. Create new folder in `integrations/`
2. Implement integration logic
3. Add tool declarations
4. Update `tools.py` function mapping
5. Add environment variables to `.env.sample`
6. Test integration functionality

### MCP Server Integration
1. Configure servers in `integrations/mcp/mcp_servers.json`
2. Servers auto-register with the system
3. Tools become available automatically
4. No code changes required for new MCP servers

## 📊 Performance Considerations

### Optimization Features
- **Async Processing**: Non-blocking audio and API operations
- **Task Groups**: Concurrent task management
- **Audio Buffering**: Optimized audio stream handling
- **Context Window Compression**: Efficient memory usage
- **Graceful Shutdown**: Proper resource cleanup

### Resource Management
- **Virtual Environment**: Isolated Python dependencies
- **Memory Efficient**: Streaming audio processing
- **CPU Optimized**: Async operations prevent blocking
- **Network Efficient**: Compressed audio streaming

## 🛡️ Security Considerations

### API Key Security
- Never commit `.env` files to version control
- Use environment variables for sensitive data
- Regularly rotate API keys
- Monitor API usage for unauthorized access

### Integration Security
- Home Assistant tokens provide full access
- Google Calendar OAuth requires secure handling
- MCP servers run with system permissions
- Audio data is processed locally before transmission

## 🔮 Future Roadmap

### Planned Features
- Multi-room support
- Voice customization
- Additional MCP integrations
- Wake word implementation
- Enhanced smart home controls
- Mobile app integration

### Technical Improvements
- Performance optimizations
- Better error handling
- Enhanced logging
- Improved documentation
- Automated testing

---

*This document provides a comprehensive overview of the Roomey AI Voice Agent project. For technical support or contributions, please refer to the project repository.*
