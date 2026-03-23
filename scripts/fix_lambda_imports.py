#!/usr/bin/env python3
"""
Fix Lambda Handler Import Paths

This script fixes import paths in all Lambda handlers to work correctly
in the AWS Lambda environment.
"""

import os
import re
from pathlib import Path


def fix_handler_imports(handler_file: Path):
    """Fix imports in a single handler file."""
    print(f"Fixing imports in {handler_file.name}...")
    
    with open(handler_file, 'r') as f:
        content = f.read()
    
    # Skip if already fixed (contains the new import pattern)
    if 'engine_root = os.path.dirname(os.path.dirname(__file__))' in content:
        print(f"  ✅ {handler_file.name} already fixed")
        return
    
    # Pattern to match the old import section
    old_import_pattern = r'# Import shared modules\nimport sys\nimport os\nsys\.path\.append\(os\.path\.join\(os\.path\.dirname\(__file__\), \'\..\', \'shared\'\)\)\n\nfrom.*?import.*?\n(from.*?import.*?\n)*'
    
    # Find all shared module imports
    shared_imports = []
    
    # Extract current imports
    import_lines = re.findall(r'from (config|.*_client) import .*', content)
    for line in import_lines:
        if 'config' in line:
            shared_imports.append('import config')
        elif '_client' in line:
            module_name = re.search(r'from (\w+_client)', line).group(1)
            shared_imports.append(f'import {module_name}')
    
    # Also check for CLIENT_TYPES import
    if 'CLIENT_TYPES' in content:
        # Update the config import to include CLIENT_TYPES
        shared_imports = [imp.replace('import config', 'from config import config, CLIENT_TYPES') if 'config' in imp else imp for imp in shared_imports]
    
    # Create new import section
    new_import_section = """# Import shared modules
import sys
import os

# Add both the engine root and shared directory to path
engine_root = os.path.dirname(os.path.dirname(__file__))
shared_path = os.path.join(engine_root, 'shared')
if engine_root not in sys.path:
    sys.path.insert(0, engine_root)
if shared_path not in sys.path:
    sys.path.insert(0, shared_path)

# Import shared modules directly
""" + '\n'.join(shared_imports)
    
    # Replace the old import section
    # First, remove old sys.path.append lines
    content = re.sub(r'sys\.path\.append\(os\.path\.join\(os\.path\.dirname\(__file__\), \'\..\', \'shared\'\)\)\n\n', '', content)
    
    # Remove old import lines
    content = re.sub(r'from (config|.*_client) import .*\n', '', content)
    
    # Find where to insert new imports (after the existing import sys/os lines)
    insert_point = content.find('import sys\nimport os')
    if insert_point != -1:
        # Find the end of the basic imports
        lines = content.split('\n')
        insert_line = None
        for i, line in enumerate(lines):
            if line.strip() == 'import os':
                insert_line = i + 1
                break
        
        if insert_line:
            # Insert the new import section
            lines.insert(insert_line, '')
            lines.insert(insert_line + 1, '# Add both the engine root and shared directory to path')
            lines.insert(insert_line + 2, 'engine_root = os.path.dirname(os.path.dirname(__file__))')
            lines.insert(insert_line + 3, 'shared_path = os.path.join(engine_root, \'shared\')')
            lines.insert(insert_line + 4, 'if engine_root not in sys.path:')
            lines.insert(insert_line + 5, '    sys.path.insert(0, engine_root)')
            lines.insert(insert_line + 6, 'if shared_path not in sys.path:')
            lines.insert(insert_line + 7, '    sys.path.insert(0, shared_path)')
            lines.insert(insert_line + 8, '')
            lines.insert(insert_line + 9, '# Import shared modules directly')
            
            for i, imp in enumerate(shared_imports):
                lines.insert(insert_line + 10 + i, imp)
            
            content = '\n'.join(lines)
    
    # Handle CLIENT_TYPES usage if present
    if 'CLIENT_TYPES' in content and 'from config import config, CLIENT_TYPES' not in content:
        content = content.replace('import config', 'from config import config, CLIENT_TYPES')
    
    # Write the updated content
    with open(handler_file, 'w') as f:
        f.write(content)
    
    print(f"  ✅ Fixed imports in {handler_file.name}")


def main():
    """Fix imports in all Lambda handlers."""
    print("🔧 Fixing Lambda handler imports for production deployment...")
    
    handlers_dir = Path(__file__).parent.parent / 'engine' / 'handlers'
    
    # Find all handler files
    handler_files = list(handlers_dir.glob('handler_*.py'))
    
    print(f"Found {len(handler_files)} handler files to process:")
    
    for handler_file in handler_files:
        fix_handler_imports(handler_file)
    
    print(f"\n✅ Fixed imports in {len(handler_files)} Lambda handlers!")
    print("🚀 Ready for deployment and testing!")


if __name__ == '__main__':
    main()