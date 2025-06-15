#!/usr/bin/env python3
"""
Roomey AI Voice Agent Setup Wizard
Interactive configuration tool for environment variables
"""

import os
import sys
import re
import shutil
from typing import Dict, List, Tuple, Optional

class SetupWizard:
    def __init__(self):
        self.env_sample_path = '.env.sample'
        self.env_path = '.env'
        self.env_backup_path = '.env.bak'
        self.variables = []
        self.values = {}
        self.existing_env_values = {}
        self.setup_mode = 'fresh'  # 'fresh' or 'update'
        
    def display_header(self):
        """Display the setup wizard header."""
        print("=" * 70)
        print("🎙️  ROOMEY AI VOICE AGENT - SETUP WIZARD")
        print("=" * 70)
        print("This wizard will help you configure your environment variables.")
        print("Press Enter to use default values, or type 'skip' to leave empty.")
        print("=" * 70)
        print()

    def read_env_sample(self) -> bool:
        """Read and parse the .env.sample file."""
        if not os.path.exists(self.env_sample_path):
            print(f"❌ Error: {self.env_sample_path} not found!")
            print("Please run this script from the project root directory.")
            return False
        
        with open(self.env_sample_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        current_section = "General"
        current_description = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Detect section headers
            if line.startswith('###') and not line.startswith('####'):
                current_section = line.replace('###', '').strip()
                current_description = []
                continue
            elif line.startswith('##') and not line.startswith('###'):
                current_section = line.replace('##', '').strip()
                current_description = []
                continue
            
            # Collect description comments
            if line.startswith('#') and '=' not in line:
                desc = line.lstrip('#').strip()
                if desc:
                    current_description.append(desc)
                continue
            
            # Parse variable definitions
            if '=' in line:
                # Handle commented variables
                is_commented = line.startswith('#')
                if is_commented:
                    line = line.lstrip('#')
                
                # Split on first '=' only
                parts = line.split('=', 1)
                if len(parts) == 2:
                    var_name = parts[0].strip()
                    default_value = parts[1].strip()
                    
                    # Clean up default value
                    if default_value.startswith('"') and default_value.endswith('"'):
                        default_value = default_value[1:-1]
                    
                    # Determine variable type and validation
                    var_type = self._determine_variable_type(var_name, default_value)
                    
                    self.variables.append({
                        'name': var_name,
                        'default': default_value,
                        'section': current_section,
                        'description': ' '.join(current_description) if current_description else '',
                        'type': var_type,
                        'required': var_name in ['GEMINI_API_KEY'],
                        'commented': is_commented
                    })
                    
                    current_description = []  # Reset description after each variable
        
        return True

    def read_existing_env(self) -> bool:
        """Read existing .env file and extract values."""
        if not os.path.exists(self.env_path):
            return False
        
        try:
            with open(self.env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                
                # Skip empty lines and comments (but not commented variables)
                if not line or (line.startswith('#') and '=' not in line):
                    continue
                
                # Handle commented variables
                if line.startswith('#') and '=' in line:
                    line = line.lstrip('#')
                
                # Parse variable definitions
                if '=' in line:
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        var_name = parts[0].strip()
                        value = parts[1].strip()
                        
                        # Clean up value
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        
                        # Convert true/false to T/F for boolean variables for internal consistency
                        if var_name in ['LINKEDIN_FORMATTER_INTEGRATION', 'GOOGLE_CALENDAR_INTEGRATION', 
                                       'HASS_INTEGRATION', 'MCP_ENABLED', 'FOCUS_AWARE_INPUT', 'LOG_CONVERSATION']:
                            if value.lower() == 'true':
                                value = 'T'
                            elif value.lower() == 'false':
                                value = 'F'
                        
                        self.existing_env_values[var_name] = value
            
            return True
        except Exception as e:
            print(f"❌ Error reading existing .env file: {e}")
            return False

    def _determine_variable_type(self, var_name: str, default_value: str) -> str:
        """Determine the expected type of a variable."""
        boolean_vars = ['LINKEDIN_FORMATTER_INTEGRATION', 'GOOGLE_CALENDAR_INTEGRATION', 
                       'HASS_INTEGRATION', 'MCP_ENABLED', 'FOCUS_AWARE_INPUT', 'LOG_CONVERSATION']
        
        if var_name in boolean_vars:
            return 'boolean'
        elif var_name.endswith('_URL') or var_name.startswith('HASS_URL'):
            return 'url'
        elif var_name.endswith('_EMAIL'):
            return 'email'
        elif var_name.endswith('_KEY') or var_name.endswith('_TOKEN'):
            return 'secret'
        elif var_name in ['CHANNELS', 'SEND_SAMPLE_RATE', 'RECEIVE_SAMPLE_RATE', 'CHUNK_SIZE']:
            return 'integer'
        elif var_name in ['DEFAULT_MODE']:
            return 'choice'
        elif var_name == 'PUSH_TO_TALK_KEY':
            return 'single_char'
        elif var_name == 'MIC_DEVICE_INDEX':
            return 'integer'
        elif var_name == 'MIC_CHANGE_KEY':
            return 'single_char'
        else:
            return 'string'

    def _get_conditional_dependencies(self, var_name: str) -> Optional[Tuple[str, str]]:
        """Get the dependency condition for a variable (parent_var, required_value)."""
        dependencies = {
            'HASS_URL': ('HASS_INTEGRATION', 'T'),
            'HASS_TOKEN': ('HASS_INTEGRATION', 'T'),
            'MCP_CONFIG_PATH': ('MCP_ENABLED', 'T'),
            'GOOGLE_CALENDAR_EMAIL': ('GOOGLE_CALENDAR_INTEGRATION', 'T')
        }
        return dependencies.get(var_name)

    def _should_prompt_variable(self, var_info: Dict) -> bool:
        """Check if a variable should be prompted based on its dependencies."""
        dependency = self._get_conditional_dependencies(var_info['name'])
        if dependency:
            parent_var, required_value = dependency
            parent_value = self.values.get(parent_var, '')
            return parent_value == required_value
        return True

    def validate_input(self, var_name: str, value: str, var_type: str) -> Tuple[bool, str]:
        """Validate user input based on variable type."""
        if not value and var_type == 'boolean':
            return True, 'F'  # Default for boolean
        
        if var_type == 'boolean':
            if value.lower() in ['true', 'false', 't', 'f', 'yes', 'no', 'y', 'n', '1', '0']:
                return True, 'T' if value.lower() in ['true', 't', 'yes', 'y', '1'] else 'F'
            return False, "Please enter T/F or true/false"
        
        elif var_type == 'email':
            if not value:
                return True, value
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if re.match(email_pattern, value):
                return True, value
            return False, "Please enter a valid email address"
        
        elif var_type == 'url':
            if not value:
                return True, value
            if value.startswith(('http://', 'https://')):
                return True, value
            return False, "Please enter a valid URL starting with http:// or https://"
        
        elif var_type == 'integer':
            if not value:
                return True, value
            try:
                int(value)
                return True, value
            except ValueError:
                return False, "Please enter a valid integer"
        
        elif var_type == 'choice' and var_name == 'DEFAULT_MODE':
            if not value:
                return True, 'none'
            if value in ['none', 'camera', 'screen']:
                return True, value
            return False, "Please enter 'none', 'camera', or 'screen'"
        
        elif var_type == 'single_char':
            if not value:
                return True, 't'
            if len(value) == 1 and value.isalpha():
                return True, value.lower()
            return False, "Please enter a single letter"
        
        return True, value

    def choose_setup_mode(self) -> str:
        """Choose between update or fresh setup when .env exists."""
        print("🔧 EXISTING .ENV FILE DETECTED")
        print("-" * 50)
        print("Choose an option:")
        print("1. Update existing values with defaults from .env.sample (keeps your current values)")
        print("2. Fresh setup - backup existing .env to .env.bak and start over")
        print()
        
        while True:
            try:
                choice = input("Enter your choice (1/2): ").strip()
                if choice == '1':
                    return 'update'
                elif choice == '2':
                    return 'fresh'
                else:
                    print("❌ Please enter 1 or 2")
            except KeyboardInterrupt:
                print("\n\n❌ Setup cancelled by user.")
                sys.exit(1)

    def backup_existing_env(self) -> bool:
        """Backup existing .env file to .env.bak."""
        try:
            shutil.copy2(self.env_path, self.env_backup_path)
            print(f"✅ Existing .env backed up to {self.env_backup_path}")
            return True
        except Exception as e:
            print(f"❌ Error backing up .env file: {e}")
            return False

    def prompt_for_variable(self, var_info: Dict) -> str:
        """Prompt user for a single variable value."""
        name = var_info['name']
        default = var_info['default']
        description = var_info['description']
        var_type = var_info['type']
        required = var_info['required']
        
        # Get existing value if in update mode
        existing_value = self.existing_env_values.get(name, '') if self.setup_mode == 'update' else ''
        
        print(f"\n📝 {name}")
        if description:
            print(f"   {description}")
        
        # Show existing value if available
        if existing_value and self.setup_mode == 'update':
            if var_type == 'secret':
                print(f"   Current: [HIDDEN]")
            else:
                print(f"   Current: '{existing_value}'")
        
        # Special handling for different types
        if var_type == 'boolean':
            print("   Type: T/F or true/false")
        elif var_type == 'secret':
            print("   Type: API Key/Token (sensitive)")
        elif var_type == 'choice' and name == 'DEFAULT_MODE':
            print("   Choices: none, camera, screen")
        elif var_type == 'single_char':
            print("   Type: Single character (a-z)")
        
        # Determine what to show as default
        if self.setup_mode == 'update' and existing_value:
            if var_type == 'secret':
                prompt = "   New value (Enter to keep existing) > "
            else:
                prompt = f"   New value (Enter to keep '{existing_value}') > "
        elif default and not var_info['commented']:
            prompt = f"   Default: '{default}' > "
        else:
            prompt = "   Value > "
        
        while True:
            try:
                value = input(prompt).strip()
                
                # Handle skip
                if value.lower() == 'skip':
                    return ''
                
                # Handle empty input - use existing value, default, or empty
                if not value:
                    if self.setup_mode == 'update' and existing_value:
                        value = existing_value
                    elif default and not var_info['commented']:
                        value = default
                
                # Validate required fields
                if required and not value:
                    print("   ❌ This field is required!")
                    continue
                
                # Type validation
                is_valid, validated_value = self.validate_input(name, value, var_type)
                if is_valid:
                    return validated_value
                else:
                    print(f"   ❌ {validated_value}")
                    continue
                    
            except KeyboardInterrupt:
                print("\n\n❌ Setup cancelled by user.")
                sys.exit(1)

    def collect_values(self):
        """Collect values for all variables."""
        current_section = None
        
        for var_info in self.variables:
            # Print section header when it changes
            if var_info['section'] != current_section:
                current_section = var_info['section']
                print(f"\n🔧 {current_section.upper()}")
                print("-" * 50)
            
            value = self.prompt_for_variable(var_info)
            self.values[var_info['name']] = value

    def write_env_file(self) -> bool:
        """Write the .env file with collected values."""
        try:
            with open(self.env_path, 'w', encoding='utf-8') as f:
                f.write("# Roomey AI Voice Agent Configuration\n")
                f.write("# Generated by setup wizard\n")
                f.write(f"# Created: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                current_section = None
                for var_info in self.variables:
                    # Write section headers
                    if var_info['section'] != current_section:
                        current_section = var_info['section']
                        f.write(f"\n# {current_section}\n")
                    
                    # Write variable
                    name = var_info['name']
                    value = self.values.get(name, '')
                    
                    # Add description as comment if available
                    if var_info['description']:
                        f.write(f"# {var_info['description']}\n")
                    
                    # Write the variable line
                    if value:
                        # Convert T/F to true/false for boolean variables
                        if var_info['type'] == 'boolean':
                            final_value = 'true' if value == 'T' else 'false'
                        # Quote string values that contain spaces or special characters
                        elif (var_info['type'] == 'string' and 
                            (' ' in value or any(c in value for c in ['#', '"', "'"]))):
                            final_value = f'"{value}"'
                        else:
                            final_value = value
                        
                        f.write(f'{name}={final_value}\n')
                    else:
                        f.write(f'#{name}=\n')
                    f.write('\n')
                    
            return True
        except Exception as e:
            print(f"❌ Error writing .env file: {e}")
            return False

    def display_summary(self):
        """Display setup summary."""
        print("\n" + "=" * 70)
        print("✅ SETUP COMPLETE!")
        print("=" * 70)
        print(f"Configuration saved to: {self.env_path}")
        print("\nConfigured variables:")
        
        configured_count = 0
        for var_info in self.variables:
            name = var_info['name']
            value = self.values.get(name, '')
            if value:
                configured_count += 1
                if var_info['type'] == 'secret':
                    print(f"  ✓ {name}: [HIDDEN]")
                else:
                    print(f"  ✓ {name}: {value}")
        
        print(f"\nTotal: {configured_count}/{len(self.variables)} variables configured")
        print("\n🚀 You can now run: python main_mac.py")
        print("💡 To reconfigure later, run: python setup.py")

    def run(self):
        """Run the setup wizard."""
        self.display_header()
        
        # Check if .env already exists and handle accordingly
        if os.path.exists(self.env_path):
            # Choose setup mode
            self.setup_mode = self.choose_setup_mode()
            
            if self.setup_mode == 'fresh':
                # Backup existing .env file
                if not self.backup_existing_env():
                    print("❌ Setup cancelled due to backup failure.")
                    return
                print()
            elif self.setup_mode == 'update':
                # Read existing .env values
                if not self.read_existing_env():
                    print("❌ Failed to read existing .env file. Switching to fresh setup.")
                    self.setup_mode = 'fresh'
                    if not self.backup_existing_env():
                        print("❌ Setup cancelled due to backup failure.")
                        return
                print()
        
        # Read and parse .env.sample
        if not self.read_env_sample():
            return
        
        print(f"📖 Found {len(self.variables)} configuration variables")
        if self.setup_mode == 'update':
            print("🔄 Update mode: Existing values will be preserved unless you change them")
        print("⌨️  Starting interactive configuration...\n")
        
        # Collect values from user
        self.collect_values()
        
        # Write .env file
        if self.write_env_file():
            self.display_summary()
            if self.setup_mode == 'fresh' and os.path.exists(self.env_backup_path):
                print(f"📁 Previous configuration backed up to: {self.env_backup_path}")
        else:
            print("❌ Setup failed!")

def main():
    """Main entry point."""
    try:
        wizard = SetupWizard()
        wizard.run()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
