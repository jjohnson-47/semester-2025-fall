# Local Development Server Information

## 🌐 Server Details

**Status**: ✅ **RUNNING**  
**URL**: http://localhost:8001  
**Directory**: `/home/verlyn13/Projects/jjohnson-47/semester-2025-fall/build/`

## 📚 Available Course Materials

### Direct Links (click to open in browser):

#### MATH 221 - Applied Calculus
- **Syllabus**: http://localhost:8001/syllabi/MATH221.html
- **Syllabus with Calendar**: http://localhost:8001/syllabi/MATH221_with_calendar.html
- **Schedule**: http://localhost:8001/schedules/MATH221_schedule.html
- **Calendar (ICS)**: http://localhost:8001/MATH221_calendar.ics

#### MATH 251 - Calculus I
- **Syllabus**: http://localhost:8001/syllabi/MATH251.html
- **Syllabus with Calendar**: http://localhost:8001/syllabi/MATH251_with_calendar.html
- **Schedule**: http://localhost:8001/schedules/MATH251_schedule.html
- **Calendar (ICS)**: http://localhost:8001/MATH251_calendar.ics

#### STAT 253 - Applied Statistics
- **Syllabus**: http://localhost:8001/syllabi/STAT253.html
- **Syllabus with Calendar**: http://localhost:8001/syllabi/STAT253_with_calendar.html
- **Schedule**: http://localhost:8001/schedules/STAT253_schedule.html
- **Calendar (ICS)**: http://localhost:8001/STAT253_calendar.ics

## 🏠 Homepage

**Index Page**: http://localhost:8001/index.html

A nicely formatted homepage with links to all course materials.

## 🛠️ Server Management

### Stop the server:
```bash
# Find the process
lsof -i :8001

# Kill the process (replace PID with actual process ID)
kill <PID>
```

### Restart the server:
```bash
cd build && python -m http.server 8001
```

### Use a different port:
```bash
cd build && python -m http.server 8002
```

## 📋 Generated Content Summary

All syllabi have been generated with:
- ✅ V2 architecture features
- ✅ No weekend due dates enforcement
- ✅ Schema v1.1.0 compliance
- ✅ Full calendar integration
- ✅ Custom due dates from course platforms (MyOpenMath, Edfinity, Pearson)

## 🚀 Quick Test

Open your browser and navigate to:
**http://localhost:8001/index.html**

You should see a nicely formatted page with links to all course materials.