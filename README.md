# 🎓 Purdue Campus Events

**[https://cs348campuseventsystem-production.up.railway.app/]**

A database-backed web application built with Flask, SQLAlchemy, MySQL, and Bootstrap for managing campus events. The system supports two user roles: students and club administrators. Students can browse events, RSVP, view RSVP history, and submit feedback for events they attended. Club administrators can create, edit, delete, and analyze events hosted by their organization.

---

## 🚀 Features

### Student features
* Sign up and log in
* Browse all upcoming and past events
* RSVP as Going or Maybe
* View personal RSVP history with filters
* Submit feedback for past events only if the student RSVP’d as Going

### Club admin features
* Sign up as a club admin and associate with an existing club or create a new one
* Create, edit, and delete events for their club
* Prevent double booking for the same location and time slot
* Generate analytics reports filtered by location and date range
* View per-event RSVP counts and feedback summaries

---

## 🛠️ Tech Stack
* **Backend:** Flask
* **Database ORM:** Flask-SQLAlchemy / SQLAlchemy
* **Authentication:** Flask-Login
* **Database:** MySQL
* **Frontend:** HTML, Bootstrap, Jinja2
* **WSGI server:** Gunicorn
* **MySQL driver:** PyMySQL
* **Cloud Deployment:** Railway (CI/CD connected to GitHub)

---

## ☁️ Cloud Deployment (Railway)
This application is fully deployed and hosted on the cloud using **Railway**. 
* **Continuous Integration / Continuous Deployment (CI/CD):** The Railway project is linked directly to this GitHub repository. Any pushes to the `main` branch automatically trigger a new cloud build.
* **Production Database:** Railway provisions and manages a live MySQL 8.0 instance. 
* **Environment Variables:** The live production environment securely injects the `DATABASE_URL` to connect the Flask app to the cloud database without hardcoding credentials.
* **Production Server:** The app is served using `gunicorn` as specified in the `Procfile` and `requirements.txt`.

---

## 📂 Project Structure
```text
app.py
seed.py
requirements.txt
templates/
    index.html
    login.html
    signup.html
    edit_event.html
    report.html
```
* `app.py` contains the Flask app, models, routes, authentication logic, validation, reporting logic, and transaction handling.
* `seed.py` resets and repopulates the database with sample clubs, users, events, RSVPs, and feedback for testing and demo purposes.
* `templates/` contains all UI pages rendered with Jinja2.

---

## 💻 Installation and Local Setup

Clone the repository, create and activate a virtual environment, install dependencies, set MySQL environment variables, and run the app:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export DB_USER='root'
export DB_PASSWORD='your_mysql_password'
export DB_HOST='localhost'
export DB_NAME='campus_event_db'

python app.py
```
Then open: `http://127.0.0.1:5000/`

The application also supports a `DATABASE_URL` environment variable. If that is present, the app will use it directly; otherwise, it falls back to `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_NAME`.

---

## 🌱 Sample Seeded Accounts
The seed script creates:
* 15 club admin accounts
* 50 student accounts
* 45 events
* realistic RSVP and feedback data

**Example seeded accounts:**
* **Student:** `saksham@purdue.edu` / `password`
* **Admins:** `admin1@purdue.edu`, `admin2@purdue.edu`, etc. / `password`

To reseed the database:
```bash
python seed.py
```

---

## 🗄️ Database Design
This project uses a relational database with the following main tables:

### 1. clubs
Stores club/organization information.
* **Primary key:** `id`
* **Important attributes:** `name`, `description`

### 2. users
Stores both students and club admins.
* **Primary key:** `id`
* **Foreign key:** `club_id` -> `clubs.id`
* **Important attributes:** `email`, `password_hash`, `name`, `role`

### 3. locations
Stores campus event locations.
* **Primary key:** `id`
* **Important attributes:** `building_name`, `room_number`, `capacity`

### 4. events
Stores hosted events.
* **Primary key:** `id`
* **Foreign keys:** `location_id` -> `locations.id`, `club_id` -> `clubs.id`
* **Important attributes:** `title`, `description`, `event_date`, `start_time`, `end_time`

### 5. rsvps
Stores attendance intent for a student and event.
* **Primary key:** `id`
* **Foreign keys:** `user_id` -> `users.id`, `event_id` -> `events.id`
* **Important attribute:** `status`

### 6. feedback
Stores post-event feedback.
* **Primary key:** `id`
* **Foreign keys:** `event_id` -> `events.id`, `user_id` -> `users.id`
* **Important attributes:** `venue_rating`, `content_rating`, `recommend`, `comments`

This schema supports authentication, event hosting, RSVP tracking, room-capacity logic, reporting, and post-event reviews.

---

## 📊 Stage 2 Requirement Coverage

### Requirement 1: Insert, Update, Delete on a Main Table
The main table used for CRUD is the `events` table.

* **Insert:** Club admins can create a new event from the dashboard form. The `/add_event` route validates all required fields, parses date/time values, checks that end time is after start time, and prevents double booking at the same location and time.
* **Update:** Club admins can edit their own upcoming events through `/edit_event/<id>`. The route re-validates time ranges and checks for location overlap conflicts before saving changes.
* **Delete:** Club admins can delete their own upcoming events through `/delete_event/<id>`. Past events cannot be deleted to preserve attendance and feedback records.

### Requirement 2: Filter Data and Display Reports
The `/report` route supports two role-based report modes.

**Student report**
Students can filter RSVP history by:
* start date
* end date
* sort order

The UI displays matching events in a table.

**Club admin report**
Club admins can filter events by:
* location
* start date
* end date
* sort order

The report then displays:
* total RSVPs marked going
* average venue rating
* average content rating
* per-event RSVP counts
* feedback details for each matching event

### Dynamic UI Components Built from the Database
A key Stage 2 requirement was that dropdowns or selection controls must be built dynamically from the database. This project satisfies that in multiple places:
* The club selection dropdown in `signup.html` is populated from `Club.query.all()` in the `signup()` route.
* The location dropdown in `index.html` for event creation is populated from `Location.query.all()` in the `home()` route.
* The location dropdown in `edit_event.html` is populated dynamically from the database.
* The location filter dropdown in `report.html` is also built from live database data.

---

## 🔐 Stage 3 Requirement Coverage

### A. Protection Against SQL Injection
This application is protected from SQL injection primarily through the use of SQLAlchemy ORM queries instead of raw SQL string concatenation. User input is passed into ORM filters and object creation methods rather than being embedded directly into SQL statements. Examples include:
* `User.query.filter_by(email=email).first()`
* `Event.query.filter(...)`
* `RSVP.query.filter_by(...)`
* `Feedback.query.filter_by(...)`

**How the application protects itself**
* **ORM-based query construction:** The application does not build raw SQL queries from user input for login, signup, reports, RSVP, feedback, or event management. This reduces SQL injection risk because SQLAlchemy handles parameter binding internally.
* **Backend input validation and sanitization:**
  * `signup()` validates allowed roles and checks for empty required fields.
  * `login()` rejects blank credentials.
  * `add_event()` and `edit_event()` validate required fields, parse types safely, and reject invalid date/time inputs.
  * `rsvp()` validates that RSVP status is only going or maybe.
  * `add_feedback()` validates allowed rating values and recommendation values.
  * `report()` validates location filters and sort order.
* **Password security:** * Passwords are stored using `generate_password_hash(...)`
  * Logins are verified using `check_password_hash(...)`
  * Plaintext passwords are not stored in the database.

**Summary:** The project combines ORM-based query safety with backend input validation and secure password hashing, which together provide meaningful protection against common SQL injection and malformed input attacks.

### B. Indexes and What They Support
This project uses a combination of automatic and manually added indexes.

**Automatic indexes from the schema**
Based on the model design, the database includes:
* primary key indexes on all `id` columns
* a unique index on `users.email`
* a unique index on `clubs.name`
* indexes on foreign-key columns such as `club_id`, `location_id`, `event_id`, and `user_id` in their respective tables

**Additional indexes added in MySQL Workbench**
For performance on report and RSVP queries, the following composite indexes were added:
* `idx_events_club_date` (`club_id`, `event_date`)
* `idx_events_club_location_date` (`club_id`, `location_id`, `event_date`)
* `idx_rsvps_event_status` (`event_id`, `status`)

**What each index supports:**
1. **Unique index on `users.email`**: Supports the login query (`user = User.query.filter_by(email=email).first()`). Since login searches by email, indexing `users.email` makes that lookup efficient.
2. **`idx_events_club_date`**: Supports the club admin report when filtering by current admin’s club, date range, and sort by date. This is used in the club admin branch of `/report`.
3. **`idx_events_club_location_date`**: Supports the more selective version of the same report when the admin also filters by location. This is also used in the club admin branch of `/report`.
4. **`idx_rsvps_event_status`**: Supports RSVP counting queries (e.g., checking capacity or generating admin analytics) based on the event and the specific "going" status.

**Why these indexes matter:**
The added indexes were chosen to support the app’s most important real queries: login, admin report filters, RSVP capacity checks, and attendance analytics. Instead of adding unnecessary indexes, this project focuses on indexes that match actual route logic and report use cases.

### C. Transactions and Isolation Levels
The main concurrency-sensitive feature in this application is the RSVP process.

**The concurrency problem**
Without transaction protection, two students could try to RSVP going for the last available spot at nearly the same time. If both requests read the same current RSVP count before either request commits, the event could become overbooked.

**Transaction design used**
The `rsvp()` route treats the capacity check and RSVP update as a single transaction-critical unit. It:
1. validates the role and RSVP status
2. locks the matching event row using:
```python
db.session.execute(
    text("SELECT id FROM events WHERE id = :event_id FOR UPDATE"),
    {"event_id": event_id}
)
```
3. reads the event and current RSVP count
4. checks capacity
5. inserts or updates the RSVP
6. commits if everything succeeds
7. rolls back if any error occurs

**Why FOR UPDATE is used**
The row lock forces concurrent RSVP requests for the same event to wait until the first transaction finishes. That prevents two students from both taking the last seat simultaneously.

**Isolation level choice**
A practical baseline choice for this application is `READ COMMITTED`:
* it prevents dirty reads
* it keeps performance reasonable
* combined with row-level locking, it is sufficient for the RSVP capacity-critical section

In this project, the main protection against overbooking comes from the explicit `FOR UPDATE` lock in the RSVP transaction.

**Summary:** This design supports a concurrent multi-user version of the application where multiple students may RSVP at the same time without violating event capacity constraints.

---

## 🗺️ Important Routes
* `/signup` — create a new student or club admin account
* `/login` — authenticate users
* `/logout` — end session
* `/` — dashboard with events and role-based actions
* `/add_event` — insert new event row
* `/edit_event/<id>` — update event row
* `/delete_event/<id>` — delete event row if allowed
* `/rsvp/<event_id>` — RSVP with transaction-protected capacity logic
* `/add_feedback/<event_id>` — store feedback
* `/report` — generate student or club admin reports

---

## 🎥 Notes on Demo Coverage
This project demonstrates:
* insert, update, and delete on the `events` table
* report filtering before and after data changes
* dynamic dropdowns built directly from database queries
* report analytics based on live RSVP and feedback data
* backend validation and transaction logic relevant to Stage 3 requirements

---

## 📦 Dependencies
Project dependencies are listed in `requirements.txt`, including:
* Flask
* Flask-Login
* Flask-SQLAlchemy
* SQLAlchemy
* PyMySQL
* Gunicorn
```
