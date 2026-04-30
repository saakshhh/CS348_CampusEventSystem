import os
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_sessions'

# database configuration
database_url = os.environ.get("DATABASE_URL")

if database_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace("mysql://", "mysql+pymysql://")
else:
    db_user = os.environ.get("DB_USER", "root")
    db_password = os.environ.get("DB_PASSWORD", "")
    db_host = os.environ.get("DB_HOST", "localhost")
    db_name = os.environ.get("DB_NAME", "campus_event_db")
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# flask login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# to find a specific user
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# database models
class Club(db.Model):
    __tablename__ = 'clubs'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    users = db.relationship('User', backref='club', lazy=True)
    events = db.relationship('Event', backref='host_club', lazy=True)


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('clubs.id'), nullable=True)
    rsvps = db.relationship('RSVP', backref='student', lazy=True)
    feedbacks = db.relationship('Feedback', backref='author', lazy=True)


class Location(db.Model):
    __tablename__ = 'locations'

    id = db.Column(db.Integer, primary_key=True)
    building_name = db.Column(db.String(100), nullable=False)
    room_number = db.Column(db.String(20), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    events = db.relationship('Event', backref='location', lazy=True)


class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    event_date = db.Column(db.Date, default=date.today)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('clubs.id'), nullable=False)

    feedbacks = db.relationship('Feedback', backref='event', cascade="all, delete-orphan", lazy=True)
    rsvps = db.relationship('RSVP', backref='event', cascade="all, delete-orphan", lazy=True)


class RSVP(db.Model):
    __tablename__ = 'rsvps'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)


class Feedback(db.Model):
    __tablename__ = 'feedback'

    id = db.Column(db.Integer, primary_key=True)
    venue_rating = db.Column(db.Integer, nullable=False)
    content_rating = db.Column(db.Integer, nullable=False)
    recommend = db.Column(db.String(10), nullable=False)
    comments = db.Column(db.Text)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


# database initialization
with app.app_context():
    db.create_all()


# --- AUTHENTICATION ROUTES ---

@app.route("/signup", methods=["GET", "POST"])
def signup():
    all_clubs = Club.query.all()

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "").strip()

        allowed_roles = {"student", "club_admin"}
        if not email or not name or not password or role not in allowed_roles:
            flash("Invalid signup input.")
            return redirect(url_for("signup"))

        club_id = None

        if role == "club_admin":
            club_selection = request.form.get("club_id", "").strip()

            if not club_selection:
                flash("Please select a club.")
                return redirect(url_for("signup"))

            if club_selection == "new":
                new_club_name = request.form.get("new_club_name", "").strip()
                new_club_desc = request.form.get("new_club_description", "").strip()

                if not new_club_name:
                    flash("New club name cannot be empty.")
                    return redirect(url_for("signup"))

                new_club = Club(name=new_club_name, description=new_club_desc)
                db.session.add(new_club)
                db.session.commit()

                club_id = new_club.id
            else:
                try:
                    club_id = int(club_selection)
                except ValueError:
                    flash("Invalid club selection.")
                    return redirect(url_for("signup"))

        if User.query.filter_by(email=email).first():
            flash("Email already exists. Please log in.")
            return redirect(url_for("signup"))

        new_user = User(
            email=email,
            name=name,
            password_hash=generate_password_hash(password),
            role=role,
            club_id=club_id
        )
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("signup.html", clubs=all_clubs)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Invalid email or password.")
            return redirect(url_for("login"))

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("home"))

        flash("Invalid email or password.")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


#main app routes
@app.route("/")
def home():
    all_events = Event.query.all()
    all_locations = Location.query.all()
    user_rsvps = {}
    user_feedbacks = []

    if current_user.is_authenticated:
        user_rsvps = {rsvp.event_id: rsvp.status for rsvp in current_user.rsvps}
        user_feedbacks = [feedback.event_id for feedback in current_user.feedbacks]

    return render_template(
        "index.html",
        events=all_events,
        locations=all_locations,
        today=date.today(),
        user_rsvps=user_rsvps,
        user_feedbacks=user_feedbacks
    )


@app.route("/add_event", methods=["POST"])
@login_required
def add_event():
    if current_user.role != "club_admin":
        return "Unauthorized", 403

    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    loc_id_raw = request.form.get("location_id", "").strip()
    event_date_raw = request.form.get("event_date", "").strip()
    start_time_raw = request.form.get("start_time", "").strip()
    end_time_raw = request.form.get("end_time", "").strip()

    if not title or not description or not loc_id_raw or not event_date_raw or not start_time_raw or not end_time_raw:
        flash("All event fields are required.")
        return redirect("/")

    try:
        loc_id = int(loc_id_raw)
        event_date = datetime.strptime(event_date_raw, "%Y-%m-%d").date()
        start_time = datetime.strptime(start_time_raw, "%H:%M").time()
        end_time = datetime.strptime(end_time_raw, "%H:%M").time()
    except ValueError:
        flash("Invalid event input.")
        return redirect("/")

    if end_time <= start_time:
        flash("Error: Event end time must be after the start time.")
        return redirect("/")

    overlap = Event.query.filter(
        Event.location_id == loc_id,
        Event.event_date == event_date,
        Event.start_time < end_time,
        Event.end_time > start_time
    ).first()

    if overlap:
        flash(
            f"Double Booking Error: {overlap.location.building_name} is already booked by "
            f"{overlap.host_club.name} from {overlap.start_time.strftime('%I:%M %p')} "
            f"to {overlap.end_time.strftime('%I:%M %p')}!"
        )
        return redirect("/")

    new_event = Event(
        title=title,
        description=description,
        location_id=loc_id,
        event_date=event_date,
        start_time=start_time,
        end_time=end_time,
        club_id=current_user.club_id
    )
    db.session.add(new_event)
    db.session.commit()

    return redirect("/")


@app.route("/delete_event/<int:id>")
@login_required
def delete_event(id):
    event = Event.query.get_or_404(id)

    if event.club_id == current_user.club_id:
        if event.event_date < date.today():
            flash("You cannot delete an event that has already ended.")
            return redirect("/")

        db.session.delete(event)
        db.session.commit()

    return redirect("/")


@app.route("/edit_event/<int:id>", methods=["GET", "POST"])
@login_required
def edit_event(id):
    event_to_edit = Event.query.get_or_404(id)

    if event_to_edit.club_id != current_user.club_id:
        return "Unauthorized", 403

    if event_to_edit.event_date < date.today():
        flash("You cannot edit an event that has already ended.")
        return redirect("/")

    all_locations = Location.query.all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        new_loc_id_raw = request.form.get("location_id", "").strip()
        new_date_raw = request.form.get("event_date", "").strip()
        new_start_raw = request.form.get("start_time", "").strip()
        new_end_raw = request.form.get("end_time", "").strip()

        if not title or not description or not new_loc_id_raw or not new_date_raw or not new_start_raw or not new_end_raw:
            flash("All event fields are required.")
            return redirect(f"/edit_event/{id}")

        try:
            new_loc_id = int(new_loc_id_raw)
            new_date = datetime.strptime(new_date_raw, "%Y-%m-%d").date()
            new_start = datetime.strptime(new_start_raw, "%H:%M").time()
            new_end = datetime.strptime(new_end_raw, "%H:%M").time()
        except ValueError:
            flash("Invalid event input.")
            return redirect(f"/edit_event/{id}")

        if new_end <= new_start:
            flash("Error: Event end time must be after the start time.")
            return redirect(f"/edit_event/{id}")

        overlap = Event.query.filter(
            Event.id != id,
            Event.location_id == new_loc_id,
            Event.event_date == new_date,
            Event.start_time < new_end,
            Event.end_time > new_start
        ).first()

        if overlap:
            flash(
                f"Double Booking Error: {overlap.location.building_name} is already booked from "
                f"{overlap.start_time.strftime('%I:%M %p')} to {overlap.end_time.strftime('%I:%M %p')}!"
            )
            return redirect(f"/edit_event/{id}")

        event_to_edit.title = title
        event_to_edit.description = description
        event_to_edit.location_id = new_loc_id
        event_to_edit.event_date = new_date
        event_to_edit.start_time = new_start
        event_to_edit.end_time = new_end

        db.session.commit()
        return redirect("/")

    return render_template("edit_event.html", event=event_to_edit, locations=all_locations)

@app.route("/rsvp/<int:event_id>", methods=["POST"])
@login_required
def rsvp(event_id):
    if current_user.role != "student":
        return "Unauthorized", 403

    status = request.form.get("status", "").strip()
    allowed_statuses = {"going", "maybe"}

    if status not in allowed_statuses:
        flash("Invalid RSVP status.")
        return redirect("/")

    # REQUIREMENT 1C (TRANSACTIONS & ISOLATION):
    # flask automatically starts a transaction here. If anything fails, the except block catches it and rolls the whole thing back
    try:
        # PESSIMISTIC LOCKING: We execute a 'SELECT ... FOR UPDATE'
        # if two students click RSVP at the exact same millisecond, this lock forces the
        # second student's transaction to pause and wait until the first student is finished.
        db.session.execute(
            text("SELECT id FROM events WHERE id = :event_id FOR UPDATE"),
            {"event_id": event_id}
        )

        event = db.session.get(Event, event_id)
        if not event:
            flash("Event not found.")
            return redirect("/")

        # check if this student already RSVP'd before
        existing_rsvp = RSVP.query.filter_by(
            user_id=current_user.id,
            event_id=event_id
        ).first()

        # capacity check
        if status == "going" and (not existing_rsvp or existing_rsvp.status != "going"):
            current_going = RSVP.query.filter_by(
                event_id=event_id,
                status="going"
            ).count()

            if current_going >= event.location.capacity:
                flash(f"Sorry! The room capacity of {event.location.capacity} has been reached.")
                return redirect("/")

        # update their status or create a new RSVP record
        if existing_rsvp:
            existing_rsvp.status = status
        else:
            db.session.add(
                RSVP(
                    user_id=current_user.id,
                    event_id=event_id,
                    status=status
                )
            )

        # manually commit the automatic transaction now that everything succeeded
        db.session.commit()

        flash("RSVP updated successfully.")
        return redirect("/")

    except Exception as e:
        print(f"CRITICAL RSVP ERROR: {str(e)}")
        db.session.rollback()
        flash("Something went wrong while processing your RSVP. Please try again.")
        return redirect("/")


@app.route("/add_feedback/<int:event_id>", methods=["POST"])
@login_required
def add_feedback(event_id):
    if Feedback.query.filter_by(user_id=current_user.id, event_id=event_id).first():
        flash("You have already submitted feedback for this event.")
        return redirect("/")

    venue_rating = request.form.get("venue_rating", "").strip()
    content_rating = request.form.get("content_rating", "").strip()
    recommend = request.form.get("recommend", "").strip()
    comments = request.form.get("comments", "").strip()

    allowed_ratings = {"1", "2", "3", "4", "5"}
    allowed_recommend = {"Yes", "No"}

    if venue_rating not in allowed_ratings or content_rating not in allowed_ratings:
        flash("Invalid rating submitted.")
        return redirect("/")

    if recommend not in allowed_recommend:
        flash("Invalid recommendation submitted.")
        return redirect("/")

    new_feedback = Feedback(
        venue_rating=int(venue_rating),
        content_rating=int(content_rating),
        recommend=recommend,
        comments=comments,
        event_id=event_id,
        user_id=current_user.id
    )
    db.session.add(new_feedback)
    db.session.commit()

    return redirect("/")


@app.route("/report", methods=["GET", "POST"])
@login_required
def report():
    all_locations = Location.query.all()
    student_events = []
    club_events = []
    total_rsvps = 0
    avg_venue = 0
    avg_content = 0

    loc_id = request.form.get("location_id", "").strip()
    start_date = request.form.get("start_date", "").strip()
    end_date = request.form.get("end_date", "").strip()
    sort_order = request.form.get("sort_order", "asc").strip()

    if sort_order not in {"asc", "desc"}:
        sort_order = "asc"

    # student report logic
    if current_user.role == "student":
        query = RSVP.query.filter_by(user_id=current_user.id).join(Event)

        if start_date:
            query = query.filter(Event.event_date >= start_date)
        if end_date:
            query = query.filter(Event.event_date <= end_date)

        if sort_order == "desc":
            query = query.order_by(Event.event_date.desc())
        else:
            query = query.order_by(Event.event_date.asc())

        # execute the query and map the RSVPs to their actual event objects
        student_rsvps = query.all()
        student_events = [rsvp.event for rsvp in student_rsvps]

        if sort_order == "desc":
            student_events.sort(key=lambda x: x.event_date, reverse=True)
        else:
            student_events.sort(key=lambda x: x.event_date)

    # club admin report
    elif current_user.role == "club_admin":
        query = Event.query.filter_by(club_id=current_user.club_id)

        # Location filter
        if loc_id:
            try:
                loc_id_int = int(loc_id)
                query = query.filter(Event.location_id == loc_id_int)
            except ValueError:
                flash("Invalid location filter.")
                return redirect(url_for("report"))

        # date filters
        if start_date:
            query = query.filter(Event.event_date >= start_date)
        if end_date:
            query = query.filter(Event.event_date <= end_date)

        if sort_order == "desc":
            query = query.order_by(Event.event_date.desc())
        else:
            query = query.order_by(Event.event_date.asc())

        club_events = query.all()

        # python sorting logic
        if sort_order == "desc":
            club_events.sort(key=lambda x: x.event_date, reverse=True)
        else:
            club_events.sort(key=lambda x: x.event_date)

        if club_events:
            event_ids = [event.id for event in club_events]

            # count all RSVPs marked 'going' for this list of events
            total_rsvps = RSVP.query.filter(
                RSVP.event_id.in_(event_ids),
                RSVP.status == "going"
            ).count()

            # ask the database to calculate the mathematical average of the star ratings
            venue_avg = db.session.query(func.avg(Feedback.venue_rating)).filter(
                Feedback.event_id.in_(event_ids)
            ).scalar()

            content_avg = db.session.query(func.avg(Feedback.content_rating)).filter(
                Feedback.event_id.in_(event_ids)
            ).scalar()

            avg_venue = round(venue_avg, 2) if venue_avg else "N/A"
            avg_content = round(content_avg, 2) if content_avg else "N/A"

            for event in club_events:
                event.going_count = sum(1 for rsvp in event.rsvps if rsvp.status == "going")
                event.maybe_count = sum(1 for rsvp in event.rsvps if rsvp.status == "maybe")
                event.total_responses = len(event.rsvps)

    # pass all the processed data over to the report.html template
    return render_template(
        "report.html",
        locations=all_locations,
        student_events=student_events,
        club_events=club_events,
        total_rsvps=total_rsvps,
        avg_venue=avg_venue,
        avg_content=avg_content,
        request=request
    )


if __name__ == "__main__":
    app.run(debug=True)