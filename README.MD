Husky Ambassador Work Log & Summary Dashboard

**Project Overview**

This project is an interactive dashboard built using Python, Dash, and Plotly, designed for Husky Ambassadors to log their work shifts and view summary statistics across semesters.

**Key Features:**

Work Log Tab:
- Enter shifts with fields for date, time, work type, and hours worked.
- Automatic formatting of time inputs (e.g., entering "12" auto-fills to "12:00").
- Invalid row detection and auto-removal with a warning message.
- Semester-based filtering of displayed shifts.
- Chronologically sorted work log (newest first), with times displayed in a 12-hour format without leading zeros.
- Deletion of rows via an interactive table.

Summary Tab:
- Displays total hours worked, estimated earnings, and a breakdown of shift types.
- Semester-based filtering with a dynamic title that updates to reflect the selected semester.

Local Data Storage:
- All user-entered data is stored in localStorage so users can leave and return without losing information.

**Future Improvements (if revisited):**

1) Add CSV export functionality for the work log
2) Enable user authentication for personalized work log history
3) Color coding for the work log 

**How to Use This Husky Ambassador Work Log Dashboard**

1️⃣ Clone this repository
- git clone https://github.com/shreyathal/husky-ambassador-dashboard.git
- cd husky-ambassador-dashboard

2️⃣ Set up your Python environment
- (Optional but recommended) Create and activate a virtual environment:
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
- Install the required dependencies:
pip install -r requirements.txt

3️⃣ Run the program
- In the terminal, from your project directory, run:
python HA_dash.py
- Once the page opens, add your own work shift data
