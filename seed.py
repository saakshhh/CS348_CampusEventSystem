import random
from datetime import date, time, timedelta
from app import app, db, Club, User, Location, Event, RSVP, Feedback
from werkzeug.security import generate_password_hash

print("🧹 Wiping the database clean...")

with app.app_context():
    # Automatically drop and recreate all tables
    db.drop_all()
    db.create_all()

    print("🌱 Seeding 15 Campus Clubs...")
    club_names = [
        "The Data Mine", "Purdue Hackers", "Chess Club", "Board Games Club",
        "Purdue Formula SAE", "Artificial Intelligence Society", "Cricket and Social Outreach",
        "Purdue Outing Club", "Women in Business", "Purdue Space Program",
        "Photography Club", "Culinary Club", "Game Development Club",
        "Boiler Gold Rush", "Model United Nations"
    ]
    clubs = []
    for name in club_names:
        club = Club(name=name,
                    description=f"The official {name} community at Purdue. Join us to learn, build, and connect!")
        clubs.append(club)
        db.session.add(club)
    db.session.commit()

    print("🏢 Seeding 10 Purdue Locations...")
    locations_data = [
        ("Lawson (LWSN)", "B158", 50), ("Wilmeth (WALC)", "1055", 300),
        ("Purdue Memorial Union (PMU)", "North Ballroom", 500), ("Stewart Center (STEW)", "Loeb", 1000),
        ("Beering Hall (BRNG)", "2280", 150), ("Krannert Building (KRAN)", "G016", 100),
        ("Co-Rec (CREC)", "Feature Gym", 400), ("Honors College (HCRN)", "1066", 90),
        ("Forney Hall (FRNY)", "G140", 250), ("Physics Building (PHYS)", "112", 300)
    ]
    locations = []
    for b_name, r_num, cap in locations_data:
        loc = Location(building_name=b_name, room_number=r_num, capacity=cap)
        locations.append(loc)
        db.session.add(loc)
    db.session.commit()

    print("👥 Seeding Users (15 Admins & 50 Students)...")
    hashed_pw = generate_password_hash('password')
    users = []

    # 1. Create Admins (One for each club)
    for i, club in enumerate(clubs):
        admin = User(email=f"admin{i + 1}@purdue.edu", name=f"{club.name} President", password_hash=hashed_pw,
                     role="club_admin", club_id=club.id)
        users.append(admin)
        db.session.add(admin)

    # 2. Create the master student account
    saksham = User(email="saksham@purdue.edu", name="Saksham Singh", password_hash=hashed_pw, role="student")
    users.append(saksham)
    db.session.add(saksham)

    # 3. Create 49 random students
    first_names = ["John", "Jane", "Alex", "Emily", "Michael", "Sarah", "David", "Emma", "Chris", "Olivia", "Ethan",
                   "Sophia", "Daniel", "Isabella", "Matthew", "Ava", "Lucas", "Mia", "Henry", "Amelia", "Jack",
                   "Harper", "Owen", "Evelyn", "Gabriel"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez",
                  "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore",
                  "Jackson", "Martin"]

    students = [saksham]  # Keep track of students for RSVPs
    for i in range(49):
        first = random.choice(first_names)
        last = random.choice(last_names)
        student = User(email=f"student{i + 1}@purdue.edu", name=f"{first} {last}", password_hash=hashed_pw,
                       role="student")
        users.append(student)
        students.append(student)
        db.session.add(student)
    db.session.commit()

    print("📅 Seeding 45 Events with realistic RSVPs and Feedback...")
    today = date.today()

    # Generate 3 events per club (1 past, 2 future) to guarantee a highly active dashboard
    for club in clubs:
        for i in range(3):
            # i == 0 means a Past Event. i > 0 means Future Events.
            if i == 0:
                event_date = today - timedelta(days=random.randint(2, 45))
                event_title = f"{club.name} Semester Kickoff"
            elif i == 1:
                event_date = today + timedelta(days=random.randint(1, 14))
                event_title = f"{club.name} Weekly Meeting"
            else:
                event_date = today + timedelta(days=random.randint(15, 60))
                event_title = f"{club.name} Mega Workshop"

            # Randomize times (between 9 AM and 7 PM)
            start_h = random.randint(9, 19)
            duration = random.choice([1, 2])  # 1 or 2 hour events

            e = Event(
                title=event_title,
                description=f"Join {club.name} for an awesome session! Food and drinks might be provided.",
                event_date=event_date,
                start_time=time(start_h, 0),
                end_time=time(start_h + duration, 0),
                location_id=random.choice(locations).id,
                club_id=club.id
            )
            db.session.add(e)
            db.session.commit()

            # --- GENERATE RSVPS ---
            # Randomly select between 10 and 35 students to attend this event
            attendee_count = random.randint(10, 35)
            attendees = random.sample(students, attendee_count)

            # Bias the data: Ensure 'saksham' attends a lot of events so the personal report looks good
            if saksham not in attendees and random.random() > 0.3:
                attendees.append(saksham)

            for student in attendees:
                rsvp = RSVP(user_id=student.id, event_id=e.id, status='going')
                db.session.add(rsvp)

                # --- GENERATE FEEDBACK (Only if the event is in the past) ---
                # About 60% of attendees leave a review
                if event_date < today and random.random() > 0.4:

                    # Generate realistic varied feedback
                    rating_quality = random.choices(["excellent", "good", "okay", "bad"], weights=[50, 30, 15, 5])[0]

                    if rating_quality == "excellent":
                        v_rate, c_rate, rec = random.randint(4, 5), random.randint(4, 5), "Yes"
                        comments = random.choice(["Absolutely fantastic!", "Loved the energy. Will come again.",
                                                  "Great speaker and awesome snacks.", "Best event of the semester.",
                                                  "Super informative and fun."])
                    elif rating_quality == "good":
                        v_rate, c_rate, rec = random.randint(3, 4), random.randint(3, 5), "Yes"
                        comments = random.choice(
                            ["Good event overall.", "Solid presentation.", "I liked it, but the room was a bit small.",
                             "Decent content.", "Enjoyed myself."])
                    elif rating_quality == "okay":
                        v_rate, c_rate, rec = random.randint(2, 4), random.randint(2, 3), random.choice(["Yes", "No"])
                        comments = random.choice(
                            ["It was just okay.", "A bit boring, honestly.", "Room was freezing cold.",
                             "Expected more hands-on activities.", "Not bad, but not great."])
                    else:
                        v_rate, c_rate, rec = random.randint(1, 2), random.randint(1, 2), "No"
                        comments = random.choice(["Could not hear the speaker.", "Waste of time.", "Very unorganized.",
                                                  "The venue was terrible for this."])

                    fb = Feedback(
                        venue_rating=v_rate,
                        content_rating=c_rate,
                        recommend=rec,
                        comments=comments,
                        event_id=e.id,
                        user_id=student.id
                    )
                    db.session.add(fb)

    db.session.commit()
    print("✅ Database seeding complete! Successfully generated massive amounts of realistic data.")