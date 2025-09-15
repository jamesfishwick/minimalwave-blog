#!/bin/bash
# Enhanced migration dependency validation

set -e

echo "🔍 Validating migration dependency graph..."

# Check for broken dependency references
echo "📋 Checking for broken dependency references..."
find . -name "migrations/*.py" -not -name "__init__.py" -exec grep -l "dependencies.*=" {} \; | while read migration_file; do
    # Extract dependencies from the migration file
    dependencies=$(python3 -c "
import re
with open('$migration_file', 'r') as f:
    content = f.read()
    
# Find dependencies array
deps_match = re.search(r'dependencies\s*=\s*\[(.*?)\]', content, re.DOTALL)
if deps_match:
    deps_content = deps_match.group(1)
    # Find all tuples like ('app', 'migration_name')
    dep_tuples = re.findall(r'\([\'\"](.*?)[\'\"],\s*[\'\"](.*?)[\'\"]\)', deps_content)
    for app, migration in dep_tuples:
        print(f'{app}:{migration}')
")
    
    # Check if each dependency file exists
    for dep in $dependencies; do
        app=$(echo $dep | cut -d: -f1)
        migration=$(echo $dep | cut -d: -f2)
        dep_file="${app}/migrations/${migration}.py"
        
        if [ ! -f "$dep_file" ]; then
            echo "❌ BROKEN DEPENDENCY: $migration_file references non-existent $dep_file"
            exit 1
        fi
    done
done

# Check for duplicate field additions
echo "📋 Checking for duplicate field additions..."
python3 -c "
import os
import re
from collections import defaultdict

# Track all field additions by app and model
field_additions = defaultdict(lambda: defaultdict(list))

for root, dirs, files in os.walk('.'):
    if 'migrations' in root and not '.git' in root:
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                filepath = os.path.join(root, file)
                app = root.split('/')[1] if '/' in root else root.split('\\\\')[1]
                
                with open(filepath, 'r') as f:
                    content = f.read()
                    
                # Find AddField operations
                add_field_matches = re.findall(
                    r'migrations\.AddField\(\s*model_name=[\'\"](.*?)[\'\"],\s*name=[\'\"](.*?)[\'\"]',
                    content,
                    re.DOTALL
                )
                
                for model, field in add_field_matches:
                    field_additions[app][f'{model}.{field}'].append(filepath)

# Check for duplicates
for app, models in field_additions.items():
    for field_key, files in models.items():
        if len(files) > 1:
            print(f'❌ DUPLICATE FIELD: {field_key} added in multiple migrations:')
            for f in files:
                print(f'   - {f}')
            exit(1)
"

echo "✅ Migration dependency validation completed successfully"