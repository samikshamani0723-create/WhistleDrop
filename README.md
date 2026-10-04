WhistleDrop - Anonymous Reporting API

Project Overview

WhistleDrop is a Flask REST API that allows users to submit anonymous reports and track their status using a unique case code without creating an account.

Technologies Used

- Python
- Flask
- SQLite
- Postman

Features

- Anonymous report submission
- Report categories: Security, Harassment, Corruption, Technical, Other
- Random case code generation
- Report status tracking
- Moderator authentication
- Filtering reports by category and status
- Moderator status updates
- Input validation and error handling

Setup Instructions

1. Install Python.
2. Install Flask:
   "pip install flask"
3. Run the application:
   "python app.py"
4. The API runs at "http://127.0.0.1:5000".

API Endpoints

Method| Endpoint| Purpose
POST| "/reports"| Submit an anonymous report
GET| "/reports/<case_code>"| Track report status
GET| "/moderator/reports"| View and filter reports
PATCH| "/reports/<case_code>/status"| Update report status

Moderator endpoints require the "X-Moderator-Key" request header.

Report Workflow

SUBMITTED → UNDER_REVIEW → RESOLVED / DISMISSED

Privacy and Security

Reports do not require user accounts or personal identity fields. Random case codes allow anonymous tracking. Moderator endpoints are protected using API-key authentication.

Testing

The API can be tested using Postman. HTTP responses include 200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, and 404 Not Found.