from app import create_app
from app.extensions import db
from app.models import PlacementEvent
from datetime import datetime

# Initialize the Flask application
app = create_app()

def seed_calendar():
    with app.app_context():
        # Clean existing events
        print("Clearing old calendar events...")
        try:
            db.session.execute(db.text('DROP TABLE IF EXISTS event_applications'))
            db.session.execute(db.text('DROP TABLE IF EXISTS placement_events'))
        except Exception as e:
            print(f"Cleanup skip: {e}")
            
        print("Creating tables...")
        db.create_all()
        
        events = [
            {
                "company_name": "TCS",
                "role": "Software Engineer (Ninja)",
                "event_date": datetime(2025, 4, 20).date(),
                "location": "offline",
                "venue": "College Auditorium",
                "eligibility_cgpa": 6.0,
                "eligibility_skills": "Java, Aptitude, Reasoning"
            },
            {
                "company_name": "Infosys",
                "role": "Systems Engineer",
                "event_date": datetime(2025, 4, 25).date(),
                "location": "online",
                "venue": None,
                "eligibility_cgpa": 6.5,
                "eligibility_skills": "Python, DBMS, Communication"
            },
            {
                "company_name": "Wipro",
                "role": "Project Engineer",
                "event_date": datetime(2025, 4, 28).date(),
                "location": "offline",
                "venue": "Seminar Hall B",
                "eligibility_cgpa": 6.0,
                "eligibility_skills": "C++, Aptitude"
            },
            {
                "company_name": "Amazon",
                "role": "SDE-1",
                "event_date": datetime(2025, 4, 30).date(),
                "location": "online",
                "venue": None,
                "eligibility_cgpa": 7.5,
                "eligibility_skills": "DSA, System Design, LeetCode"
            },
            {
                "company_name": "Cognizant",
                "role": "Programmer Analyst",
                "event_date": datetime(2025, 5, 5).date(),
                "location": "offline",
                "venue": "Main Seminar Hall",
                "eligibility_cgpa": 6.0,
                "eligibility_skills": "Java, SQL"
            },
            {
                "company_name": "Accenture",
                "role": "Associate Software Engineer",
                "event_date": datetime(2025, 5, 8).date(),
                "location": "online",
                "venue": None,
                "eligibility_cgpa": 6.5,
                "eligibility_skills": "Communication, Any Language"
            }
        ]

        print("Adding sample placement events...")
        for data in events:
            ev = PlacementEvent(
                company_name=data["company_name"],
                role=data["role"],
                event_date=data["event_date"],
                location=data["location"],
                venue=data["venue"],
                eligibility_cgpa=data["eligibility_cgpa"],
                eligibility_skills=data["eligibility_skills"],
                description="This is a mock description generated for testing purposes.",
                registration_link="https://example.com/apply"
            )
            db.session.add(ev)

        db.session.commit()
        print("Calendar events seeded successfully!")

if __name__ == '__main__':
    seed_calendar()
