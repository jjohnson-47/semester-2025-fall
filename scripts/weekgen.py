#!/usr/bin/env python3
"""
Generate weekly module folders and overview pages.
Creates structured weekly content for the semester.
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.utils.calendar import SemesterCalendar


class WeeklyGenerator:
    """Generate weekly content structure."""
    
    def __init__(self, output_dir: str = "build/weekly"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.calendar = SemesterCalendar()
    
    def generate_weeks(self):
        """Generate all weekly folders."""
        weeks = self.calendar.get_weeks()
        
        for i, week in enumerate(weeks[:16], 1):
            if week.get('is_finals'):
                week_name = "Finals_Week"
            else:
                week_name = f"Week_{i:02d}"
            
            week_dir = self.output_dir / week_name
            week_dir.mkdir(exist_ok=True)
            
            # Create overview file
            overview = [
                f"# {week_name.replace('_', ' ')}",
                f"**Dates:** {week['start']} to {week['end']}",
                "",
            ]
            
            if week['holidays']:
                overview.append(f"**Note:** {', '.join(week['holidays'])}")
                overview.append("")
            
            if week.get('is_finals'):
                overview.extend([
                    "## Finals Week",
                    "",
                    "This week is dedicated to final examinations.",
                    "",
                    "### Important:",
                    "- Check Blackboard for your final exam schedule",
                    "- Review all course materials",
                    "- Complete any remaining assignments",
                ])
            else:
                overview.extend([
                    "## Learning Objectives",
                    f"- Week {i} objectives to be added",
                    "",
                    "## Required Reading",
                    f"- Chapter {i} in textbook",
                    "",
                    "## Assignments",
                    f"- Homework {i} due Sunday 11:59 PM",
                    "",
                    "## Resources",
                    "- Lecture notes",
                    "- Practice problems",
                    "- Discussion board",
                ])
            
            overview_file = week_dir / "README.md"
            overview_file.write_text("\n".join(overview))
            
            print(f"✓ Generated {week_name}")
        
        # Create index file
        index = [
            "# Weekly Modules - Fall 2025",
            "",
            "## Course Schedule",
            "",
        ]
        
        for i, week in enumerate(weeks[:16], 1):
            if week.get('is_finals'):
                index.append(f"- [Finals Week]({self.output_dir}/Finals_Week/) - {week['start']} to {week['end']}")
            else:
                week_name = f"Week_{i:02d}"
                holidays = f" - {', '.join(week['holidays'])}" if week['holidays'] else ""
                index.append(f"- [Week {i}]({self.output_dir}/{week_name}/) - {week['start']} to {week['end']}{holidays}")
        
        index_file = self.output_dir / "index.md"
        index_file.write_text("\n".join(index))
        
        print(f"✓ Generated weekly index")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Generate weekly modules')
    parser.add_argument('--output', default='build/weekly', help='Output directory')
    
    args = parser.parse_args()
    
    generator = WeeklyGenerator(output_dir=args.output)
    generator.generate_weeks()
    
    print(f"\nWeekly modules generated in: {args.output}/")


if __name__ == '__main__':
    main()