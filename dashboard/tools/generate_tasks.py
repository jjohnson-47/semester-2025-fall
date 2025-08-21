#!/usr/bin/env python3
"""
Generate tasks from templates and course configuration.
"""

import json
import yaml
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import re
import sys


class TaskGenerator:
    """Generate tasks from YAML templates."""
    
    def __init__(self, courses_file: str, templates_dir: str):
        self.courses = self._load_json(courses_file)
        self.templates_dir = Path(templates_dir)
        self.tasks = []
        self.task_counter = 0
    
    def _load_json(self, filepath: str) -> Dict[str, Any]:
        """Load JSON file."""
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def _load_yaml(self, filepath: str) -> Dict[str, Any]:
        """Load YAML file."""
        with open(filepath, 'r') as f:
            return yaml.safe_load(f)
    
    def generate(self) -> Dict[str, Any]:
        """Generate all tasks from templates."""
        # Process each template file
        template_files = sorted(self.templates_dir.glob('*.yaml'))
        
        for template_file in template_files:
            print(f"Processing template: {template_file.name}")
            self._process_template(template_file)
        
        # Sort tasks by due date and priority
        self.tasks.sort(key=lambda t: (
            t.get('due', '9999-12-31'),
            -t.get('weight', 1)
        ))
        
        return {
            'tasks': self.tasks,
            'metadata': {
                'version': '1.0',
                'generated': datetime.now().isoformat(),
                'semester': self.courses.get('semester', '2025-fall'),
                'task_count': len(self.tasks)
            }
        }
    
    def _process_template(self, template_file: Path) -> None:
        """Process a single template file."""
        template = self._load_yaml(template_file)
        
        # Get applicable courses
        applies_to = template.get('applies_to', [])
        if 'ALL' in applies_to:
            applies_to = [c['code'] for c in self.courses.get('courses', [])]
        
        # Generate tasks for each applicable course
        for course_code in applies_to:
            course = self._get_course(course_code)
            if not course:
                print(f"  Warning: Course {course_code} not found")
                continue
            
            for task_template in template.get('tasks', []):
                task = self._create_task(task_template, template, course)
                self.tasks.append(task)
                print(f"  Created task: {task['id']}")
    
    def _get_course(self, course_code: str) -> Optional[Dict[str, Any]]:
        """Get course by code."""
        for course in self.courses.get('courses', []):
            if course['code'] == course_code:
                return course
        return None
    
    def _create_task(self, task_template: Dict[str, Any], 
                     template: Dict[str, Any], 
                     course: Dict[str, Any]) -> Dict[str, Any]:
        """Create a task from template."""
        self.task_counter += 1
        
        # Prepare context for variable substitution
        context = {
            'course': course,
            'semester': self.courses.get('important_dates', {}),
        }
        
        # Generate task ID
        task_key = task_template.get('key', f'TASK-{self.task_counter:04d}')
        task_id = f"{course['code']}-{task_key}"
        
        # Calculate due date
        due_date = self._calculate_due_date(task_template.get('due_offset', {}))
        
        # Create task
        task = {
            'id': task_id,
            'course': course['code'],
            'title': self._substitute_vars(task_template['title'], context),
            'description': self._substitute_vars(task_template.get('description', ''), context),
            'category': template.get('defaults', {}).get('category', 'General'),
            'status': 'blocked' if task_template.get('blocked_by') else 'todo',
            'weight': task_template.get('weight', template.get('defaults', {}).get('weight', 1)),
            'tags': task_template.get('tags', template.get('defaults', {}).get('tags', [])),
            'created': datetime.now().isoformat(),
            'history': []
        }
        
        # Add optional fields
        if due_date:
            task['due'] = due_date.isoformat()
        
        if 'checklist' in task_template:
            task['checklist'] = [
                self._substitute_vars(item, context) 
                for item in task_template['checklist']
            ]
        
        if 'blocked_by' in task_template:
            blocked_by = task_template['blocked_by']
            task['blocked_by'] = [
                self._substitute_vars(dep, context) 
                for dep in (blocked_by if isinstance(blocked_by, list) else [blocked_by])
            ]
        
        if 'links' in task_template:
            task['links'] = task_template['links']
        
        return task
    
    def _calculate_due_date(self, offset: Dict[str, Any]) -> Optional[datetime]:
        """Calculate due date from offset specification."""
        if not offset:
            return None
        
        days = offset.get('days', 0)
        from_date = offset.get('from', 'semester.first_day')
        
        # Get base date
        if from_date == 'semester.first_day':
            base = self.courses.get('important_dates', {}).get('first_day', '2025-08-25')
        elif from_date == 'semester.last_day':
            base = self.courses.get('important_dates', {}).get('last_day', '2025-12-13')
        elif from_date == 'today':
            base = datetime.now().strftime('%Y-%m-%d')
        else:
            base = from_date
        
        # Parse and offset
        try:
            base_date = datetime.strptime(base, '%Y-%m-%d')
            return base_date + timedelta(days=days)
        except:
            return None
    
    def _substitute_vars(self, text: str, context: Dict[str, Any]) -> str:
        """Substitute template variables."""
        if not text:
            return text
        
        def replacer(match):
            path = match.group(1).split('.')
            value = context
            for key in path:
                if isinstance(value, dict):
                    value = value.get(key, match.group(0))
                else:
                    return match.group(0)
            return str(value)
        
        return re.sub(r'{{([\w.]+)}}', replacer, text)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Generate tasks from templates')
    parser.add_argument('--courses', required=True, help='Courses JSON file')
    parser.add_argument('--templates', required=True, help='Templates directory')
    parser.add_argument('--out', required=True, help='Output tasks JSON file')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not Path(args.courses).exists():
        print(f"Error: Courses file not found: {args.courses}")
        sys.exit(1)
    
    if not Path(args.templates).exists():
        print(f"Error: Templates directory not found: {args.templates}")
        sys.exit(1)
    
    # Generate tasks
    generator = TaskGenerator(args.courses, args.templates)
    result = generator.generate()
    
    # Write output
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n✓ Generated {len(result['tasks'])} tasks")
    print(f"✓ Written to {args.out}")


if __name__ == '__main__':
    main()