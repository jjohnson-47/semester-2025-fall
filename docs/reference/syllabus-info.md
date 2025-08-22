# Fall 2025 Course Files Structure

## Shared Files

### profiles/instructor.json
```json
{
  "name": "Jeffrey Johnson",
  "title": "Professor",
  "email": "jjohnson47@alaska.edu",
  "office": "KPC Kachemak Bay Campus, Bayview Hall, Office #126",
  "phone": "(907) 235-1603",
  "office_hours": "Anytime by appointment",
  "zoom_link": "Available in Blackboard"
}
```

### .env additions
```
SEMESTER_NAME=Fall 2025
MATH221_FULL=Applied Calculus for Managerial and Social Sciences
MATH221_SHORT=Applied Calculus
MATH251_FULL=Calculus 1
MATH251_SHORT=Calc 1
STAT253_FULL=Applied Statistics for the Sciences
STAT253_SHORT=Applied Stats
```

## MATH221 Files

### content/courses/MATH221/course_meta.json
```json
{
  "course_crn": "XXXXX",
  "course_credits": 3
}
```

### content/courses/MATH221/course_description.json
```json
{
  "text": "Covers functions and graphs, differentiation, exponential and logarithmic functions, antidifferentiation and integration, and functions of several variables. Applies these mathematical concepts."
}
```

### content/courses/MATH221/course_prerequisites.json
```json
{
  "text": "MATH A121 with a minimum grade of C or MATH A151 with a minimum grade of C or appropriate ALEKS test scores"
}
```

### content/courses/MATH221/instructional_goals.json
```json
{
  "goals": [
    "Introduce techniques and rules of differentiation and integration",
    "Present applications of differentiation and integration",
    "Introduce partial derivatives and appropriate applications"
  ]
}
```

### content/courses/MATH221/student_outcomes.json
```json
{
  "outcomes": [
    "Differentiate functions involving rational, exponential, and logarithmic functions and combinations of these functions",
    "Integrate functions using the power rule (substitution method) and integration by parts techniques",
    "Use differentiation and integration techniques to solve applied problems"
  ]
}
```

### content/courses/MATH221/required_textbook.json
```json
{
  "title": "Business Calculus",
  "author": "Shana Calaway, Dale Hoffman, and David Lippman",
  "edition": "1st",
  "isbn": "",
  "notes": "Free copy available as website and PDF at opentextbookstore.com/buscalc1/"
}
```

### content/courses/MATH221/calculators_and_technology.json
```json
{
  "requirements": "- MyOpenMath online homework system (free, required)\n- Access to standard graphing calculator\n- Desmos online calculator (www.desmos.com/calculator)\n- Blackboard for course hub\n- Zoom for optional study sessions\n- Stable internet connection required"
}
```

### content/courses/MATH221/evaluation_tools.json
```json
{
  "categories": [
    {
      "name": "Participation",
      "weight": 4
    },
    {
      "name": "MyOpenMath Homework",
      "weight": 20
    },
    {
      "name": "MyOpenMath Class Activities",
      "weight": 8
    },
    {
      "name": "Exams",
      "weight": 68
    }
  ]
}
```

### content/courses/MATH221/grading_policy.json
```json
{
  "scale": [
    {
      "letter": "A",
      "range": "90-100%",
      "points": 900
    },
    {
      "letter": "B",
      "range": "80-89%",
      "points": 800
    },
    {
      "letter": "C",
      "range": "70-79%",
      "points": 700
    },
    {
      "letter": "D",
      "range": "60-69%",
      "points": 600
    },
    {
      "letter": "F",
      "range": "< 60%",
      "points": 0
    }
  ]
}
```

### content/courses/MATH221/class_policies.json
```json
{
  "late_work": "Academic honesty required. First offense: Zero for assignment. Second offense or exam cheating: Grade of F for course."
}
```

### content/courses/MATH221/rsi.json
```json
{
  "text": "Regular and substantive interaction through: (1) Optional Monday and Wednesday Zoom study sessions (12-1 PM), (2) Personalized feedback on MyOpenMath assignments, (3) Weekly content-focused announcements and email responses within one business day, (4) Active participation in weekly Blackboard discussions."
}
```

### content/courses/MATH221/schedule.json
```json
{
  "weeks": [
    {
      "week": 1,
      "topic": "Functions, Operations on Functions, Linear Functions",
      "readings": ["1.1", "1.2", "1.3"],
      "assignments": ["MyOpenMath: Sections 1.1-1.3"],
      "assessments": [],
      "notes": ""
    },
    {
      "week": 2,
      "topic": "Exponents, Quadratics, Polynomials & Rational Functions",
      "readings": ["1.4", "1.5", "1.6"],
      "assignments": ["MyOpenMath: Sections 1.4-1.6"],
      "assessments": [],
      "notes": ""
    },
    {
      "week": 3,
      "topic": "Exponential & Logarithmic Functions, Rate of Change",
      "readings": ["1.7", "1.8", "2.1"],
      "assignments": ["MyOpenMath: Sections 1.7-2.1"],
      "assessments": [],
      "notes": ""
    },
    {
      "week": 4,
      "topic": "Limits, Continuity, The Derivative",
      "readings": ["2.2", "2.3", "2.4"],
      "assignments": ["MyOpenMath: Sections 2.2-2.4"],
      "assessments": [],
      "notes": ""
    },
    {
      "week": 5,
      "topic": "Derivative Formulas and Rules",
      "readings": ["2.5"],
      "assignments": ["MyOpenMath: Section 2.5"],
      "assessments": [],
      "notes": ""
    },
    {
      "week": 6,
      "topic": "Second Derivative & Concavity",
      "readings": ["2.6"],
      "assignments": ["MyOpenMath: Section 2.6"],
      "assessments": ["Exam 1"],
      "notes": ""
    },
    {
      "week": 7,
      "topic": "Optimization and Curve Sketching",
      "readings": ["2.7", "2.8", "2.9"],
      "assignments": ["MyOpenMath: Sections 2.7-2.9"],
      "assessments": [],
      "notes": ""
    },
    {
      "week": 8,
      "topic": "Implicit Differentiation & Related Rates",
      "readings": ["2.10", "2.11"],
      "assignments": ["MyOpenMath: Sections 2.10-2.11"],
      "assessments": [],
      "notes": ""
    },
    {
      "week": 9,
      "topic": "Definite Integral & Fundamental Theorem",
      "readings": ["3.1", "3.2", "3.3"],
      "assignments": ["MyOpenMath: Sections 3.1-3.3"],
      "assessments": ["Exam 2"],
      "notes": ""
    },
    {
      "week": 10,
      "topic": "Integration Techniques",
      "readings": ["3.4", "3.5"],
      "assignments": ["MyOpenMath: Sections 3.4-3.5"],
      "assessments": [],
      "notes": ""
    },
    {
      "week": 11,
      "topic": "Applications of Integration",
      "readings": ["3.6", "3.7"],
      "assignments": ["MyOpenMath: Sections 3.6-3.7"],
      "assessments": [],
      "notes": ""
    },
    {
      "week": 12,
      "topic": "Differential Equations",
      "readings": ["3.8"],
      "assignments": ["MyOpenMath: Section 3.8"],
      "assessments": [],
      "notes": ""
    },
    {
      "week": 13,
      "topic": "Functions of Two Variables",
      "readings": ["4.1"],
      "assignments": ["MyOpenMath: Section 4.1"],
      "assessments": ["Exam 3"],
      "notes": ""
    },
    {
      "week": 14,
      "topic": "Partial Derivatives and Optimization",
      "readings": ["4.2", "4.3"],
      "assignments": ["MyOpenMath: Sections 4.2-4.3"],
      "assessments": [],
      "notes": ""
    },
    {
      "week": 15,
      "topic": "Review and Final Preparation",
      "readings": [],
      "assignments": [],
      "assessments": [],
      "notes": ""
    }
  ],
  "finals": {
    "topic": "Final Exam",
    "assessments": ["Final Exam"],
    "notes": "Comprehensive"
  }
}
```

## MATH251 Files

### content/courses/MATH251/course_meta.json
```json
{
  "course_crn": "XXXXX",
  "course_credits": 4
}
```

### content/courses/MATH251/course_description.json
```json
{
  "text": "A first course in single-variable calculus. Topics include limits; continuity and differentiation of functions; applications of the derivative to graphing, optimization, and rates of change; definite and indefinite integration; and the fundamental theorem of calculus."
}
```

### content/courses/MATH251/course_prerequisites.json
```json
{
  "text": "(MATH A151 with a minimum grade of C and MATH A152 with a minimum grade of C) or MATH A155 with a minimum grade of C or MATH A211 with a minimum grade of C or MATH A212 with a minimum grade of C or MATH A221 with a minimum grade of C or ALEKS Overall Test with a score of 078"
}
```

### content/courses/MATH251/instructional_goals.json
```json
{
  "goals": [
    "Introduce students to the concept of limit, its notation, and computation",
    "Present to students the concept of differentiation, its notation, calculation, and application",
    "Introduce students to the concept of integration, its notation, and calculation",
    "Present proper terminology and notation"
  ]
}
```

### content/courses/MATH251/student_outcomes.json
```json
{
  "outcomes": [
    "Understand and apply the concept of a limit",
    "Understand and apply the concepts of differentiation and integration, and their relationship as expressed by the Fundamental Theorem of Calculus",
    "Proficiently calculate derivatives and definite and indefinite integrals by means of substitution",
    "Apply the derivative in modeling settings, such as for graphing, optimization, and related rates problems"
  ]
}
```

### content/courses/MATH251/required_textbook.json
```json
{
  "title": "Active Calculus",
  "author": "Boelkins, Austin, and Schlicker",
  "edition": "",
  "isbn": "",
  "notes": "Free HTML and PDF version available at activecalculus.org"
}
```

### content/courses/MATH251/calculators_and_technology.json
```json
{
  "requirements": "- Access to standard graphing calculator required\n- Desmos online calculators (www.desmos.com)\n- Edfinity online homework system\n- Blackboard for course hub\n- Stable internet connection required"
}
```

### content/courses/MATH251/evaluation_tools.json
```json
{
  "categories": [
    {
      "name": "Discussion and Participation",
      "weight": 5
    },
    {
      "name": "Weekly Quizzes",
      "weight": 10
    },
    {
      "name": "Edfinity Homework",
      "weight": 20
    },
    {
      "name": "Written Homework",
      "weight": 15
    },
    {
      "name": "Blackboard Assignments",
      "weight": 10
    },
    {
      "name": "Midterm Exam",
      "weight": 15
    },
    {
      "name": "Final Exam",
      "weight": 25
    }
  ]
}
```

### content/courses/MATH251/grading_policy.json
```json
{
  "scale": [
    {
      "letter": "A",
      "range": "90-100%",
      "points": 450
    },
    {
      "letter": "B",
      "range": "80-89%",
      "points": 400
    },
    {
      "letter": "C",
      "range": "70-79%",
      "points": 350
    },
    {
      "letter": "D",
      "range": "60-69%",
      "points": 300
    },
    {
      "letter": "F",
      "range": "< 60%",
      "points": 0
    }
  ]
}
```

### content/courses/MATH251/class_policies.json
```json
{
  "late_work": "Edfinity homework: Can earn up to 80% of total points if submitted within 2 days after due date. Early submission receives 10% bonus if submitted 1+ days early. Final exam must be proctored."
}
```

### content/courses/MATH251/rsi.json
```json
{
  "text": "Fully asynchronous course with regular and substantive interaction through: (1) Detailed, personalized feedback on assignments within two weeks, (2) Weekly announcements and Zoom office hours, (3) Active participation in weekly discussion board, (4) Personal check-ins throughout semester."
}
```

### content/courses/MATH251/schedule.json
```json
{
  "weeks": [
    {
      "week": 1,
      "topic": "Measuring velocity and the notion of a limit",
      "readings": ["1.1", "1.2"],
      "assignments": ["Prerequisites Review", "Edfinity 1.1-1.2"],
      "assessments": ["Week 1 Quiz"],
      "notes": ""
    },
    {
      "week": 2,
      "topic": "Finding limits and continuity",
      "readings": ["1.7"],
      "assignments": ["BB1 Evaluating Limits", "Edfinity 1.7"],
      "assessments": ["Week 2 Quiz"],
      "notes": "Labor Day week"
    },
    {
      "week": 3,
      "topic": "The derivative of a function",
      "readings": ["1.3", "1.4"],
      "assignments": ["BB2 Derivative function", "Edfinity 1.3-1.4"],
      "assessments": ["Week 3 Quiz"],
      "notes": ""
    },
    {
      "week": 4,
      "topic": "Interpreting derivatives and second derivatives",
      "readings": ["1.5", "1.6"],
      "assignments": ["BB3 Second derivatives", "Written Problems 1"],
      "assessments": ["Week 4 Quiz"],
      "notes": ""
    },
    {
      "week": 5,
      "topic": "Tangent lines and derivative rules",
      "readings": ["1.8", "2.1"],
      "assignments": ["BB4 Linear approximations", "Edfinity 1.8-2.1"],
      "assessments": ["Week 5 Quiz"],
      "notes": ""
    },
    {
      "week": 6,
      "topic": "Trig derivatives, product and quotient rules",
      "readings": ["2.2", "2.3"],
      "assignments": ["BB5 Trig derivatives", "Edfinity 2.2-2.3"],
      "assessments": ["Week 6 Quiz"],
      "notes": ""
    },
    {
      "week": 7,
      "topic": "Chain rule and advanced derivatives",
      "readings": ["2.4", "2.5"],
      "assignments": ["BB6 Chain rule", "Written Problems 2"],
      "assessments": ["Week 7 Quiz"],
      "notes": ""
    },
    {
      "week": 8,
      "topic": "Inverse and implicit functions",
      "readings": ["2.6", "2.7"],
      "assignments": ["BB7 Inverse Functions", "Edfinity 2.6-2.7"],
      "assessments": ["Week 8 Quiz", "Midterm Exam"],
      "notes": ""
    },
    {
      "week": 9,
      "topic": "L'Hopital's Rule and extreme values",
      "readings": ["2.8", "3.1"],
      "assignments": ["BB8 L'Hopital's Rule", "Written Problems 3"],
      "assessments": [],
      "notes": ""
    },
    {
      "week": 10,
      "topic": "Global optimization",
      "readings": ["3.2", "3.3"],
      "assignments": ["BB9 Optimization", "Edfinity 3.2-3.3"],
      "assessments": ["Week 10 Quiz"],
      "notes": ""
    },
    {
      "week": 11,
      "topic": "Applied optimization and related rates",
      "readings": ["3.4", "3.5", "4.1"],
      "assignments": ["BB10 Related Rates", "Written Problems 4"],
      "assessments": ["Week 11 Quiz"],
      "notes": ""
    },
    {
      "week": 12,
      "topic": "Riemann sums and definite integral",
      "readings": ["4.2", "4.3"],
      "assignments": ["BB11 Summation Notation", "Edfinity 4.1-4.3"],
      "assessments": ["Week 12 Quiz"],
      "notes": ""
    },
    {
      "week": 13,
      "topic": "Fundamental Theorem of Calculus",
      "readings": ["4.4", "5.1", "5.2"],
      "assignments": ["BB12 Antiderivatives", "Written Problems 5"],
      "assessments": ["Week 13 Quiz"],
      "notes": ""
    },
    {
      "week": 14,
      "topic": "Integration techniques",
      "readings": ["5.3", "5.4"],
      "assignments": ["BB13 Integration", "Edfinity 5.3-5.4"],
      "assessments": ["Week 14 Quiz"],
      "notes": "Thanksgiving week"
    },
    {
      "week": 15,
      "topic": "Review week",
      "readings": [],
      "assignments": ["BB14 Looking Ahead"],
      "assessments": [],
      "notes": ""
    }
  ],
  "finals": {
    "topic": "Final Exam",
    "assessments": ["Final Exam (Proctored)"],
    "notes": "Comprehensive final exam"
  }
}
```

## STAT253 Files

### content/courses/STAT253/course_meta.json
```json
{
  "course_crn": "XXXXX",
  "course_credits": 3
}
```

### content/courses/STAT253/course_description.json
```json
{
  "text": "Intensive survey course with applications for the sciences. Topics include descriptive statistics, probability, random variables, binomial, Poisson and normal distributions, estimation and hypothesis testing of common parameters, analysis of variance for single factor and two factors, correlation, and simple linear regression. A major statistical software package will be utilized."
}
```

### content/courses/STAT253/course_prerequisites.json
```json
{
  "text": "MATH A121 with a minimum grade of C or MATH A151 with a minimum grade of C or MATH A155 with a minimum grade of C or ALEKS Overall Test with a score of 065 or higher"
}
```

### content/courses/STAT253/instructional_goals.json
```json
{
  "goals": [
    "Introduce descriptive statistics, probability, and widely used parametric statistical methods",
    "Utilize real-world data sets from the sciences and introduce one major statistical package to aid statistical analyses",
    "Guide writing reports that effectively communicate statistical results"
  ]
}
```

### content/courses/STAT253/student_outcomes.json
```json
{
  "outcomes": [
    "Solve thought-provoking problems and critically evaluate statistical information from real-life scenarios",
    "Collect data either by running an appropriate randomized experiment or from a reliable source",
    "Use a major statistical software package to conduct analysis of data, validating all assumptions relevant to the selected statistical method",
    "Draw conclusions and write a report effectively communicating the results"
  ]
}
```

### content/courses/STAT253/required_textbook.json
```json
{
  "title": "Applied Statistics",
  "author": "James T. McClave and Terry Sincich",
  "edition": "13th",
  "isbn": "",
  "notes": "Digital copy comes with MyMathLab"
}
```

### content/courses/STAT253/calculators_and_technology.json
```json
{
  "requirements": "- MyMathLab subscription (required)\n- R and RStudio (free)\n- Google Sheets (free)\n- Microsoft Excel (optional)\n- Blackboard for course hub\n- Zoom for optional study sessions\n- Stable internet connection required"
}
```

### content/courses/STAT253/evaluation_tools.json
```json
{
  "categories": [
    {
      "name": "Participation",
      "weight": 4.7
    },
    {
      "name": "Homework",
      "weight": 23.4
    },
    {
      "name": "Chapter Tests",
      "weight": 31.25
    },
    {
      "name": "R Assignments",
      "weight": 15.65
    },
    {
      "name": "Final Report",
      "weight": 12.5
    },
    {
      "name": "Final Test",
      "weight": 12.5
    }
  ]
}
```

### content/courses/STAT253/grading_policy.json
```json
{
  "scale": [
    {
      "letter": "A",
      "range": "90-100%",
      "points": 288
    },
    {
      "letter": "B",
      "range": "80-89%",
      "points": 256
    },
    {
      "letter": "C",
      "range": "70-79%",
      "points": 224
    },
    {
      "letter": "D",
      "range": "60-69%",
      "points": 192
    },
    {
      "letter": "F",
      "range": "< 60%",
      "points": 0
    }
  ]
}
```

### content/courses/STAT253/class_policies.json
```json
{
  "late_work": "All assignments due by 11:59 PM unless otherwise specified. Check MyMathLab and Blackboard regularly for updates."
}
```

### content/courses/STAT253/rsi.json
```json
{
  "text": "Regular and substantive interaction through: (1) Optional Monday and Wednesday Zoom study sessions (12-1 PM), (2) Personalized feedback on MyMathLab assignments, (3) Weekly content-focused announcements, (4) Active participation in Blackboard discussions. Interaction through at least two methods weekly."
}
```

### content/courses/STAT253/schedule.json
```json
{
  "weeks": [
    {
      "week": 1,
      "topic": "Statistics, Data, and Statistical Thinking",
      "readings": ["Chapter 1"],
      "assignments": ["Install R/RStudio", "Homework 1"],
      "assessments": [],
      "notes": ""
    },
    {
      "week": 2,
      "topic": "Methods for Describing Sets of Data",
      "readings": ["Chapter 2"],
      "assignments": ["Homework 2", "R Assignment 1"],
      "assessments": ["Chapter 1 Test", "Chapter 2 Test"],
      "notes": ""
    },
    {
      "week": 3,
      "topic": "Probability",
      "readings": ["Chapter 3"],
      "assignments": ["Homework 3"],
      "assessments": ["Chapter 3 Test"],
      "notes": ""
    },
    {
      "week": 4,
      "topic": "Discrete Random Variables",
      "readings": ["Chapter 4"],
      "assignments": ["Homework 4"],
      "assessments": [],
      "notes": ""
    },
    {
      "week": 5,
      "topic": "Discrete Random Variables (continued)",
      "readings": ["Chapter 4"],
      "assignments": ["Homework 5", "Final Report Draft 1"],
      "assessments": ["Chapter 4 Test"],
      "notes": ""
    },
    {
      "week": 6,
      "topic": "Continuous Random Variables",
      "readings": ["Chapter 5"],
      "assignments": ["Homework 6"],
      "assessments": ["Chapter 5 Test"],
      "notes": ""
    },
    {
      "week": 7,
      "topic": "Sampling Distributions",
      "readings": ["Chapter 6"],
      "assignments": ["Homework 7", "R Assignment 2"],
      "assessments": [],
      "notes": ""
    },
    {
      "week": 8,
      "topic": "Sampling Distributions (continued)",
      "readings": ["Chapter 6"],
      "assignments": ["Homework 8"],
      "assessments": ["Chapter 6 Test"],
      "notes": ""
    },
    {
      "week": 9,
      "topic": "Spring Break",
      "readings": [],
      "assignments": [],
      "assessments": [],
      "notes": "No classes"
    },
    {
      "week": 10,
      "topic": "Inferences Based on a Single Sample (CI)",
      "readings": ["Chapter 7"],
      "assignments": ["Homework 9", "R Assignment 3"],
      "assessments": ["Chapter 7 Test"],
      "notes": ""
    },
    {
      "week": 11,
      "topic": "Inferences Based on a Single Sample (HT)",
      "readings": ["Chapter 8"],
      "assignments": ["Homework 10", "Final Report Draft 2"],
      "assessments": ["Chapter 8 Test"],
      "notes": ""
    },
    {
      "week": 12,
      "topic": "Inferences Based on Two Samples",
      "readings": ["Chapter 9"],
      "assignments": ["Homework 11", "R Assignment 4"],
      "assessments": ["Chapter 9 Test"],
      "notes": ""
    },
    {
      "week": 13,
      "topic": "Analysis of Variance (ANOVA)",
      "readings": ["Chapter 10"],
      "assignments": ["Homework 12"],
      "assessments": [],
      "notes": ""
    },
    {
      "week": 14,
      "topic": "ANOVA (continued)",
      "readings": ["Chapter 10"],
      "assignments": ["Homework 13", "R Assignment 5"],
      "assessments": ["Chapter 10 Test"],
      "notes": ""
    },
    {
      "week": 15,
      "topic": "Linear Regression",
      "readings": ["Chapter 11"],
      "assignments": ["Homework 14"],
      "assessments": [],
      "notes": ""
    },
    {
      "week": 16,
      "topic": "Linear Regression and Review",
      "readings": ["Chapter 11"],
      "assignments": ["Homework 15", "Final Report"],
      "assessments": [],
      "notes": "Finals Week"
    }
  ],
  "finals": {
    "topic": "Final Test",
    "assessments": ["Final Test (Comprehensive)"],
    "notes": "All assignments must be submitted"
  }
}
```

## Changelog

### Updates Made:
1. **CRNs**: Need Fall 2025 CRNs (currently showing XXXXX placeholders)
2. **Shared Instructor**: Created single `profiles/instructor.json` file
3. **Environment Variables**: Added course name variables to `.env`
4. **Schedule Format**: Normalized all schedules to week numbers (no dates)
5. **Evaluation Tools**: Adjusted STAT253 R Assignments weight from 15.6% to 15.65% to ensure exact 100% total

### Items Requiring Confirmation:
1. **Fall 2025 CRNs** for all three courses
2. **Textbook editions**: Confirm if any updates needed for Fall 2025
3. **Technology requirements**: Verify if MyMathLab/Edfinity/MyOpenMath subscriptions remain the same
4. **Office hours**: Currently showing "by appointment" - confirm if specific times needed

### Notes:
- All files follow the exact structure specified in requirements
- Schedules maintain original course progression without specific dates
- Labor Day, Thanksgiving, and Spring Break noted in schedule where relevant
- Points in grading_policy.json based on 1000-point scale (can be adjusted)
