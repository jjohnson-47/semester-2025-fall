#!/usr/bin/env python3
"""
Semester calendar builder for Fall 2025.
Generates course calendars from academic calendar data.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import pytz
from dateutil import parser as date_parser


class SemesterCalendar:
    """Manages semester calendar and course schedules."""
    
    def __init__(self, calendar_file: str = "academic-calendar.json"):
        self.calendar_file = Path(calendar_file)
        self.calendar_data = self._load_calendar()
        self.timezone = pytz.timezone('America/Anchorage')
        self.semester = 'fall_2025'
        
    def _load_calendar(self) -> Dict[str, Any]:
        """Load academic calendar JSON."""
        # Try project root first
        if self.calendar_file.exists():
            with open(self.calendar_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Try parent directory (where the original files are)
        parent_calendar = Path("..") / self.calendar_file
        if parent_calendar.exists():
            with open(parent_calendar, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Return minimal calendar if not found
        return {
            'semesters': {
                'fall_2025': {
                    'start_date': '2025-08-25',
                    'end_date': '2025-12-13',
                    'finals_start': '2025-12-08',
                    'finals_end': '2025-12-13',
                    'holidays': []
                }
            }
        }
    
    def get_semester_dates(self) -> Dict[str, Any]:
        """Get key dates for the semester."""
        semester = self.calendar_data['semesters'][self.semester]
        return {
            'start': self._parse_date(semester['start_date']),
            'end': self._parse_date(semester['end_date']),
            'finals_start': self._parse_date(semester['finals_start']),
            'finals_end': self._parse_date(semester['finals_end']),
            'add_drop': self._parse_date(semester['critical_deadlines']['add_drop']['date']),
            'withdrawal': self._parse_date(semester['critical_deadlines']['withdrawal_deadline']['date'])
        }
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime."""
        if isinstance(date_str, str):
            return datetime.strptime(date_str, '%Y-%m-%d')
        return date_str
    
    def get_holidays(self) -> List[Dict[str, Any]]:
        """Get list of holidays for the semester."""
        semester = self.calendar_data['semesters'][self.semester]
        holidays = []
        
        for holiday in semester.get('holidays', []):
            if 'date' in holiday:
                holidays.append({
                    'name': holiday['name'],
                    'date': self._parse_date(holiday['date']),
                    'campus_closed': holiday.get('campus_closed', False)
                })
            elif 'start' in holiday and 'end' in holiday:
                holidays.append({
                    'name': holiday['name'],
                    'start': self._parse_date(holiday['start']),
                    'end': self._parse_date(holiday['end']),
                    'campus_closed': holiday.get('campus_closed', False)
                })
        
        return holidays
    
    def get_weeks(self) -> List[Dict[str, Any]]:
        """Generate weekly structure for the semester."""
        dates = self.get_semester_dates()
        holidays = self.get_holidays()
        
        weeks = []
        current_date = dates['start']
        week_num = 1
        
        while current_date <= dates['end']:
            # Calculate week end (Friday)
            days_until_friday = (4 - current_date.weekday()) % 7
            if days_until_friday == 0 and current_date.weekday() != 4:
                days_until_friday = 7
            week_end = current_date + timedelta(days=days_until_friday)
            
            # Check for holidays this week
            week_holidays = []
            for holiday in holidays:
                if 'date' in holiday:
                    if current_date <= holiday['date'] <= week_end:
                        week_holidays.append(holiday['name'])
                elif 'start' in holiday:
                    if not (holiday['end'] < current_date or holiday['start'] > week_end):
                        week_holidays.append(holiday['name'])
            
            # Determine if it's finals week
            is_finals = current_date >= dates['finals_start']
            
            weeks.append({
                'number': week_num if not is_finals else 'Finals',
                'start': current_date.strftime('%Y-%m-%d'),
                'end': week_end.strftime('%Y-%m-%d'),
                'holidays': week_holidays,
                'is_finals': is_finals
            })
            
            # Move to next Monday
            current_date = current_date + timedelta(days=(7 - current_date.weekday()))
            if not is_finals:
                week_num += 1
        
        return weeks
    
    def get_course_calendar(self, course_code: str) -> Dict[str, Any]:
        """Get calendar specific to a course."""
        return {
            'semester': self.semester.replace('_', ' ').title(),
            'dates': self.get_semester_dates(),
            'weeks': self.get_weeks(),
            'holidays': self.get_holidays(),
            'course_code': course_code,
            'timezone': 'America/Anchorage'
        }
    
    def generate_ics(self, course_code: str, output_file: Optional[str] = None) -> str:
        """Generate ICS calendar file for a course."""
        from datetime import datetime
        import uuid
        
        dates = self.get_semester_dates()
        
        ics_content = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            f"PRODID:-//KPC//{course_code} Fall 2025//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            f"X-WR-CALNAME:{course_code} Fall 2025",
            "X-WR-TIMEZONE:America/Anchorage",
            "BEGIN:VTIMEZONE",
            "TZID:America/Anchorage",
            "BEGIN:DAYLIGHT",
            "TZOFFSETFROM:-0900",
            "TZOFFSETTO:-0800",
            "DTSTART:20250309T020000",
            "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU",
            "END:DAYLIGHT",
            "BEGIN:STANDARD",
            "TZOFFSETFROM:-0800",
            "TZOFFSETTO:-0900",
            "DTSTART:20251102T020000",
            "RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU",
            "END:STANDARD",
            "END:VTIMEZONE",
        ]
        
        # Add important dates as events
        events = [
            ("First Day of Classes", dates['start'], dates['start']),
            ("Add/Drop Deadline", dates['add_drop'], dates['add_drop']),
            ("Withdrawal Deadline", dates['withdrawal'], dates['withdrawal']),
            ("Finals Week", dates['finals_start'], dates['finals_end']),
            ("Last Day of Classes", dates['end'], dates['end']),
        ]
        
        for title, start, end in events:
            uid = str(uuid.uuid4())
            ics_content.extend([
                "BEGIN:VEVENT",
                f"UID:{uid}@kpc.alaska.edu",
                f"DTSTART;VALUE=DATE:{start.strftime('%Y%m%d')}",
                f"DTEND;VALUE=DATE:{(end + timedelta(days=1)).strftime('%Y%m%d')}",
                f"SUMMARY:{course_code} - {title}",
                f"DESCRIPTION:{title} for {course_code} Fall 2025",
                "END:VEVENT",
            ])
        
        # Add holidays
        for holiday in self.get_holidays():
            uid = str(uuid.uuid4())
            if 'date' in holiday:
                date = holiday['date']
                ics_content.extend([
                    "BEGIN:VEVENT",
                    f"UID:{uid}@kpc.alaska.edu",
                    f"DTSTART;VALUE=DATE:{date.strftime('%Y%m%d')}",
                    f"DTEND;VALUE=DATE:{(date + timedelta(days=1)).strftime('%Y%m%d')}",
                    f"SUMMARY:{holiday['name']} (No Classes)",
                    f"DESCRIPTION:{holiday['name']} - Campus {'Closed' if holiday['campus_closed'] else 'Open'}",
                    "END:VEVENT",
                ])
        
        ics_content.append("END:VCALENDAR")
        
        ics_string = "\r\n".join(ics_content)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(ics_string)
        
        return ics_string


def main():
    """Test calendar generation."""
    calendar = SemesterCalendar()
    
    print("Fall 2025 Semester Calendar")
    print("=" * 40)
    
    dates = calendar.get_semester_dates()
    print(f"Start: {dates['start'].strftime('%B %d, %Y')}")
    print(f"End: {dates['end'].strftime('%B %d, %Y')}")
    print(f"Add/Drop: {dates['add_drop'].strftime('%B %d, %Y')}")
    print(f"Withdrawal: {dates['withdrawal'].strftime('%B %d, %Y')}")
    
    print("\nWeeks:")
    for week in calendar.get_weeks():
        holidays = f" ({', '.join(week['holidays'])})" if week['holidays'] else ""
        print(f"Week {week['number']}: {week['start']} to {week['end']}{holidays}")
    
    # Generate ICS for each course
    for course in ['MATH221', 'MATH251', 'STAT253']:
        calendar.generate_ics(course, f"build/{course}_calendar.ics")
        print(f"Generated calendar for {course}")


if __name__ == '__main__':
    main()