# KPC Syllabus Generator

A modern, template-based syllabus generation system for academic courses. Generate consistent, accessible syllabi in HTML, Markdown, and DOCX formats from a single data file.

## Features

- **Multi-format Export**: Generate HTML, Markdown, and DOCX from a single source
- **Modern Web Standards**: Responsive, accessible HTML5 with CSS Grid/Flexbox
- **Template-based**: Jinja2 templates for easy customization
- **Data-driven**: YAML or JSON data files for course information
- **Docker Support**: Containerized environment for consistent generation
- **CI/CD Ready**: GitHub Actions workflow included
- **Accessibility**: WCAG 2.1 compliant output

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/syllabus-generator.git
cd syllabus-generator

# Run setup script
chmod +x setup.sh
./setup.sh

# Activate virtual environment
source venv/bin/activate

# Initialize with sample files
python syllabus_generator.py --init
```

### Basic Usage

1. Edit `syllabus_data.yaml` with your course information
2. Generate syllabi:

```bash
python syllabus_generator.py syllabus_data.yaml
```

Output files will be in the `output/` directory.

## System Requirements

- Python 3.9+
- Pandoc 3.0+ (for DOCX generation)
- 100MB free disk space

### Platform-specific Installation

#### macOS

```bash
brew install python@3.11 pandoc
```

#### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install python3.11 python3-pip pandoc
```

#### Windows

- Install Python from [python.org](https://python.org)
- Install Pandoc from [pandoc.org](https://pandoc.org/installing.html)

## Data File Format

The syllabus data is defined in YAML format:

```yaml
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
    Comprehensive course description here...
  prerequisites: "MATH 105 or placement"
  fees: "Lab fee information"
  goals:
    - "Goal 1"
    - "Goal 2"
  outcomes:
    - "Outcome 1"
    - "Outcome 2"

# ... additional sections
```

## Template Customization

Templates are stored in the `templates/` directory:

- `syllabus.html.j2` - HTML template
- `syllabus.md.j2` - Markdown template
- `reference.docx` - Word template (optional)

### Customizing Templates

1. Edit the Jinja2 templates directly
2. Use Jinja2 syntax for variables: `{{ variable_name }}`
3. Use conditionals: `{% if condition %} ... {% endif %}`
4. Use loops: `{% for item in list %} ... {% endfor %}`

## Docker Usage

Build and run in Docker for consistent environment:

```bash
# Build image
docker-compose build

# Generate syllabus
docker-compose run syllabus-generator data/syllabus_data.yaml

# Or use Make commands
make docker-build
make docker-run ARGS=syllabus_data.yaml
```

## API Usage

Use the generator programmatically:

```python
from syllabus_generator import SyllabusGenerator

# Initialize generator
gen = SyllabusGenerator(template_dir="templates")

# Load data
data = gen.load_data("syllabus_data.yaml")

# Generate HTML
html = gen.generate_html(data)

# Generate all formats
results = gen.generate_all_formats("syllabus_data.yaml", "output")
```

## File Structure

```
syllabus-generator/
├── syllabus_generator.py    # Main generator script
├── templates/               # Jinja2 templates
│   ├── syllabus.html.j2
│   └── syllabus.md.j2
├── data/                    # Data files
│   └── syllabus_data.yaml
├── output/                  # Generated files
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose config
├── Makefile               # Build automation
└── setup.sh               # Setup script
```

## Command Line Options

```bash
python syllabus_generator.py [OPTIONS] DATA_FILE

Options:
  --init                Initialize with sample files
  -o, --output DIR     Output directory (default: output)
  --template-dir DIR   Template directory (default: templates)
  -h, --help           Show help message
```

## Advanced Features

### Multiple Courses

Generate multiple syllabi:

```bash
for file in data/*.yaml; do
    python syllabus_generator.py "$file"
done
```

### Custom Templates

```bash
python syllabus_generator.py data.yaml --template-dir custom_templates/
```

### CI/CD Integration

GitHub Actions workflow included for automated testing:

```yaml
on:
  push:
    paths:
      - 'data/*.yaml'

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python syllabus_generator.py data/*.yaml
      - uses: actions/upload-artifact@v4
```

## Troubleshooting

### Common Issues

1. **Pandoc not found**: Install Pandoc or use Docker
2. **Template not found**: Check templates directory exists
3. **YAML parse error**: Validate YAML syntax at [yamllint.com](http://yamllint.com)
4. **Unicode errors**: Ensure files are UTF-8 encoded

### Debug Mode

```bash
# Enable verbose output
PYTHONVERBOSE=1 python syllabus_generator.py data.yaml

# Check template rendering
python -c "from syllabus_generator import SyllabusGenerator;
gen = SyllabusGenerator();
print(gen.env.get_template('syllabus.html.j2').module)"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and add tests
4. Submit a pull request

### Development Setup

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Format code
black syllabus_generator.py

# Type checking
mypy syllabus_generator.py
```

## License

MIT License - See LICENSE file for details

## Support

- Issues: [GitHub Issues](https://github.com/your-org/syllabus-generator/issues)
- Documentation: [Wiki](https://github.com/your-org/syllabus-generator/wiki)
- Contact: <academic-tech@alaska.edu>

## Acknowledgments

- KPC Faculty Forum for requirements and feedback
- UAA Academic Affairs for policy guidance
- Pandoc developers for document conversion

## Version History

- v2.0.0 (August 2025) - Complete rewrite with modern stack
- v1.5.0 (January 2025) - Added Docker support
- v1.0.0 (August 2024) - Initial release

---

*Last updated: August 21, 2025*
