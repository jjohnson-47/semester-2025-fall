#!/usr/bin/env python3
"""
KPC Syllabus Generator System
Generates syllabi in HTML, Markdown, and DOCX formats
August 2025 Version
"""

import os
import sys
import yaml
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
import argparse
import json


class SyllabusGenerator:
    """Modern syllabus generator with multi-format export capabilities."""
    
    def __init__(self, template_dir: str = "templates"):
        """Initialize the generator with template directory."""
        self.template_dir = Path(template_dir)
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
    def load_data(self, data_file: str) -> Dict[str, Any]:
        """Load syllabus data from YAML or JSON file."""
        data_path = Path(data_file)
        
        if data_path.suffix in ['.yaml', '.yml']:
            with open(data_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        elif data_path.suffix == '.json':
            with open(data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            raise ValueError(f"Unsupported data format: {data_path.suffix}")
    
    def generate_html(self, data: Dict[str, Any]) -> str:
        """Generate HTML version of syllabus."""
        template = self.env.get_template('syllabus.html.j2')
        
        # Add generation metadata
        data['generation'] = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M:%S'),
            'year': datetime.now().year
        }
        
        return template.render(**data)
    
    def generate_markdown(self, data: Dict[str, Any]) -> str:
        """Generate Markdown version of syllabus."""
        template = self.env.get_template('syllabus.md.j2')
        
        # Add generation metadata
        data['generation'] = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M:%S'),
            'year': datetime.now().year
        }
        
        return template.render(**data)
    
    def html_to_docx(self, html_content: str, output_file: str) -> bool:
        """Convert HTML to DOCX using Pandoc."""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
                tmp.write(html_content)
                tmp_path = tmp.name
            
            # Pandoc command with modern options
            cmd = [
                'pandoc',
                '-f', 'html',
                '-t', 'docx',
                '--reference-doc', str(self.template_dir / 'reference.docx') if (self.template_dir / 'reference.docx').exists() else '',
                '-o', output_file,
                tmp_path
            ]
            
            # Remove empty reference-doc parameter if file doesn't exist
            cmd = [c for c in cmd if c]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Clean up temp file
            os.unlink(tmp_path)
            
            if result.returncode != 0:
                print(f"Pandoc error: {result.stderr}")
                return False
            
            return True
            
        except FileNotFoundError:
            print("Error: Pandoc not installed. Install with: brew install pandoc (Mac) or apt-get install pandoc (Linux)")
            return False
    
    def generate_all_formats(self, data_file: str, output_dir: str = "output"):
        """Generate syllabus in all supported formats."""
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Load data
        data = self.load_data(data_file)
        
        # Generate base filename from course info
        course_id = data.get('course', {}).get('number', 'syllabus').replace(' ', '_')
        base_name = f"{course_id}_{datetime.now().strftime('%Y%m%d')}"
        
        # Generate HTML
        html_content = self.generate_html(data)
        html_file = output_path / f"{base_name}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✓ Generated HTML: {html_file}")
        
        # Generate Markdown
        md_content = self.generate_markdown(data)
        md_file = output_path / f"{base_name}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"✓ Generated Markdown: {md_file}")
        
        # Generate DOCX
        docx_file = output_path / f"{base_name}.docx"
        if self.html_to_docx(html_content, str(docx_file)):
            print(f"✓ Generated DOCX: {docx_file}")
        else:
            print(f"✗ Failed to generate DOCX")
        
        return {
            'html': str(html_file),
            'markdown': str(md_file),
            'docx': str(docx_file) if docx_file.exists() else None
        }


def create_sample_data_file():
    """Create a sample YAML data file for the syllabus."""
    sample_data = """
# KPC Syllabus Data File
# Edit this file with your course information

course:
  department: "Computer Science"
  number: "CS 201"
  section: "001"
  title: "Introduction to Programming"
  semester: "Fall"
  year: 2025
  crn: "12345"
  location: "BLDG 101 / Room 205"
  
instructor:
  name: "Dr. Jane Smith"
  email: "jsmith@alaska.edu"
  office: "Science Building 312"
  phone: "(907) 555-0100"
  office_hours: "MW 2:00-4:00 PM"
  zoom_link: "https://zoom.us/j/123456789"

course_info:
  description: |
    This course provides an introduction to computer programming using Python.
    Students will learn fundamental programming concepts including variables,
    control structures, functions, and basic data structures.
  
  prerequisites: "MATH 105 or placement"
  
  fees: "A $25 lab fee is required for this course to cover software licensing."
  
  goals:
    - Understand fundamental programming concepts
    - Develop problem-solving skills
    - Write clean, maintainable code
    
  outcomes:
    - Design and implement basic algorithms
    - Debug and test programs effectively
    - Apply programming concepts to solve real-world problems
    
  required_texts:
    - title: "Python Programming: An Introduction"
      author: "John Doe"
      isbn: "978-0-123456-78-9"
      edition: "3rd"
    
  required_technology:
    - "Python 3.11 or later"
    - "Visual Studio Code or similar IDE"
    - "GitHub account for version control"

policies:
  response_time:
    feedback: "Assignment feedback will be provided within one week of submission."
    communication: "Email responses within 24 hours on weekdays."
  
  attendance: |
    Regular attendance is expected. More than 3 absences may result in
    grade reduction. Attendance alone does not determine grades.
  
  atmosphere: |
    Respectful behavior is expected at all times. Cell phones should be
    silenced during class. Discrimination or harassment will not be tolerated.
  
  audit: "Audit students must complete all assignments but are not required to take exams."
  
  async_statement: |
    This course includes asynchronous components. Regular participation in
    discussion boards and timely submission of assignments is required.

grading:
  scale:
    A: "90-100%"
    B: "80-89%"
    C: "70-79%"
    D: "60-69%"
    F: "Below 60%"
  
  components:
    - name: "Homework Assignments"
      weight: 30
    - name: "Programming Projects"
      weight: 25
    - name: "Midterm Exam"
      weight: 20
    - name: "Final Exam"
      weight: 20
    - name: "Participation"
      weight: 5

schedule:
  - week: 1
    dates: "Aug 26-30"
    topic: "Introduction to Programming"
    assignments: "Read Chapter 1"
  - week: 2
    dates: "Sep 2-6"
    topic: "Variables and Data Types"
    assignments: "HW1 due, Read Chapter 2"
  - week: 3
    dates: "Sep 9-13"
    topic: "Control Structures"
    assignments: "HW2 due, Read Chapter 3"
  # Add more weeks as needed

final_exam:
  date: "December 12, 2025"
  time: "10:00 AM - 12:00 PM"
  location: "BLDG 101 / Room 205"
"""
    
    with open('syllabus_data.yaml', 'w') as f:
        f.write(sample_data.strip())
    
    print("Created sample data file: syllabus_data.yaml")
    print("Edit this file with your course information, then run the generator.")


def main():
    """CLI interface for the syllabus generator."""
    parser = argparse.ArgumentParser(
        description='Generate course syllabi in multiple formats',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --init              # Create sample data file and templates
  %(prog)s data.yaml           # Generate syllabus from data file
  %(prog)s data.json -o dist/  # Generate with custom output directory
        """
    )
    
    parser.add_argument('data_file', nargs='?', 
                       help='YAML or JSON file with syllabus data')
    parser.add_argument('-o', '--output', default='output',
                       help='Output directory (default: output)')
    parser.add_argument('--init', action='store_true',
                       help='Initialize with sample files and templates')
    parser.add_argument('--template-dir', default='templates',
                       help='Template directory (default: templates)')
    
    args = parser.parse_args()
    
    if args.init:
        # Create sample files and template directory
        create_sample_data_file()
        
        # Create templates directory
        template_path = Path(args.template_dir)
        template_path.mkdir(exist_ok=True)
        
        print(f"Created template directory: {template_path}")
        print("\nNext steps:")
        print("1. Add syllabus.html.j2 and syllabus.md.j2 templates to templates/")
        print("2. Edit syllabus_data.yaml with your course information")
        print("3. Run: python syllabus_generator.py syllabus_data.yaml")
        
        return
    
    if not args.data_file:
        parser.print_help()
        sys.exit(1)
    
    # Check if data file exists
    if not Path(args.data_file).exists():
        print(f"Error: Data file not found: {args.data_file}")
        print("Run with --init to create a sample data file")
        sys.exit(1)
    
    # Generate syllabi
    generator = SyllabusGenerator(args.template_dir)
    
    try:
        results = generator.generate_all_formats(args.data_file, args.output)
        print(f"\n✓ Successfully generated syllabi in {args.output}/")
        
    except Exception as e:
        print(f"Error generating syllabus: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
