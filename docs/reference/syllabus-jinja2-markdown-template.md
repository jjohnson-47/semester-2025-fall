# Syllabus

**{{ course.department }} {{ course.number }} Section {{ course.section }}: {{ course.title }}**  
{{ course.semester }} {{ course.year }} - CRN {{ course.crn }}  
{{ course.location }}

---

## Instructor

**Name:** {{ instructor.name }}  
**Office Hours:** {{ instructor.office_hours }}  
**Contact Information:**
- Email: {{ instructor.email }}
- Office: {{ instructor.office }}
{% if instructor.zoom_link -%}
- Zoom: {{ instructor.zoom_link }}
{% endif -%}
- Phone: {{ instructor.phone }}

---

## Course Information

### Course Description
{{ course_info.description }}

### Course Prerequisites
{{ course_info.prerequisites }}

{% if course_info.fees -%}
### Course Fees
{{ course_info.fees }}
{% endif %}

### Instructional Goals
{% for goal in course_info.goals -%}
- {{ goal }}
{% endfor %}

### Student Outcomes
Upon successful completion of this course, students will be able to:
{% for outcome in course_info.outcomes -%}
- {{ outcome }}
{% endfor %}

### Required Text(s) and Technology

**Required Texts:**
{% for text in course_info.required_texts -%}
- {{ text.title }} by {{ text.author }}, {{ text.edition }} Edition (ISBN: {{ text.isbn }})
{% endfor %}

**Required Technology:**
{% for tech in course_info.required_technology -%}
- {{ tech }}
{% endfor %}

---

## Course Policies

### Instructor Response Time

**Feedback:** {{ policies.response_time.feedback }}

**Communication:** {{ policies.response_time.communication }}

{% if policies.async_statement -%}
### Asynchronous Course Information
{{ policies.async_statement }}
{% endif %}

### Class Participation and Attendance
{{ policies.attendance }}

### Class Atmosphere and Safety
{{ policies.atmosphere }}

### Audit Policy
{{ policies.audit }}

---

## Grading

### Grading Scale
{% for grade, range in grading.scale.items() -%}
- **{{ grade }}:** {{ range }}
{% endfor %}

### Evaluation Components

| Assignment | Percentage |
|------------|------------|
{% for component in grading.components -%}
| {{ component.name }} | {{ component.weight }}% |
{% endfor %}

---

## Course Schedule

| Week | Dates | Topic | Assignments |
|------|-------|-------|-------------|
{% for week in schedule -%}
| {{ week.week }} | {{ week.dates }} | {{ week.topic }} | {{ week.assignments }} |
{% endfor %}

{% if final_exam -%}
### Final Exam
- **Date:** {{ final_exam.date }}
- **Time:** {{ final_exam.time }}
- **Location:** {{ final_exam.location }}
{% endif %}

---

## KPC Support & Policy Guide

It is important for all KPC students to review the [KPC Support & Policy Guide](https://drive.google.com/file/d/1lEn0osdkkN9BakEa8QjMpNd_o3RrQeww/view?usp=sharing) which contains important information about Academic Services available to you as a KPC student, KPC Policies and Processes, and Campus Safety.

---

*Generated on {{ generation.date }} at {{ generation.time }}*
