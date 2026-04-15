from app.__init__ import create_app
from app.extensions import db
from app.models import Company, CompanyPost, User
from sqlalchemy import text

def seed_companies():
    app = create_app()
    with app.app_context():
        print("Clearing old company data (if any)...")
        # Ensure we drop old company metadata safely
        try:
            db.session.execute(text('DROP TABLE IF EXISTS company_profile'))
            db.session.execute(text('DROP TABLE IF EXISTS bookmarked_company'))
            db.session.execute(text('DROP TABLE IF EXISTS company_follow'))
            db.session.execute(text('DROP TABLE IF EXISTS saved_company'))
            db.session.execute(text('DROP TABLE IF EXISTS post_like'))
            db.session.execute(text('DROP TABLE IF EXISTS post_comment'))
            db.session.execute(text('DROP TABLE IF EXISTS company_post'))
            db.session.execute(text('DROP TABLE IF EXISTS company'))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Cleanup skip: {e}")
            
        print("Creating tables...")
        db.create_all()
        
        # Get a dummy user to author posts
        admin_user = User.query.filter_by(role='admin').first()
        if not admin_user:
            admin_user = User.query.first()
            if not admin_user:
                print("No users found. Please create a user first.")
                return

        companies_data = [
            {
                "name": "TCS",
                "description": "Tata Consultancy Services is an Indian multinational information technology services and consulting company.",
                "industry": "IT Services",
                "hiring_roles": "Software Engineer, Business Analyst",
                "required_skills": "Java, SQL, Aptitude",
                "package_range": "3.5\u20137",
                "logo_url": "https://upload.wikimedia.org/wikipedia/commons/b/b1/Tata_Consultancy_Services_Logo.svg",
                "website": "https://www.tcs.com",
                "headquarters": "Mumbai, India",
                "hiring_process": "Online Test|Technical Round|HR Round",
                "prep_topics": "Quantitative Aptitude|Logical Reasoning|Basic Programming"
            },
            {
                "name": "Infosys",
                "description": "Infosys is a global leader in next-generation digital services and consulting.",
                "industry": "IT Services",
                "hiring_roles": "Systems Engineer, DTE",
                "required_skills": "Python, DBMS, Reasoning",
                "package_range": "3.6\u20138",
                "logo_url": "https://upload.wikimedia.org/wikipedia/commons/9/95/Infosys_logo.svg",
                "website": "https://www.infosys.com",
                "headquarters": "Bengaluru, India",
                "hiring_process": "Online Test|Technical Interview|HR Interview",
                "prep_topics": "Pseudo Code|Database Queries|Puzzles"
            },
            {
                "name": "Wipro",
                "description": "Wipro is a leading technology services and consulting company focused on building innovative solutions.",
                "industry": "IT Services",
                "hiring_roles": "Project Engineer, WILP",
                "required_skills": "C++, Networking, Aptitude",
                "package_range": "3.5\u20136.5",
                "logo_url": "https://upload.wikimedia.org/wikipedia/commons/a/a0/Wipro_Primary_Logo_Color_RGB.svg",
                "website": "https://www.wipro.com",
                "headquarters": "Bengaluru, India",
                "hiring_process": "Online Assessment|Technical Round|HR Session",
                "prep_topics": "Verbal Ability|Computer Networks|C/C++"
            },
            {
                "name": "Amazon",
                "description": "Amazon is a multinational technology company focusing on e-commerce, cloud computing, and AI.",
                "industry": "E-Commerce",
                "hiring_roles": "SDE-1, Data Engineer",
                "required_skills": "DSA, System Design, LeetCode",
                "package_range": "18\u201345",
                "logo_url": "https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg",
                "website": "https://www.amazon.jobs",
                "headquarters": "Seattle, USA",
                "hiring_process": "Online Assessment (OA)|Technical 1|Technical 2|Bar Raiser|HR",
                "prep_topics": "Advanced DSA|Graphs & Trees|System Design"
            },
            {
                "name": "Google",
                "description": "Google is a technology company specializing in internet-related services and products.",
                "industry": "Technology",
                "hiring_roles": "SWE, STEP Intern",
                "required_skills": "Algorithms, System Design, CP",
                "package_range": "30\u201360",
                "logo_url": "https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg",
                "website": "https://careers.google.com",
                "headquarters": "Mountain View, USA",
                "hiring_process": "Online Coding Challenge|Phone Screen|Onsite Technical (3-4)|Googlyness",
                "prep_topics": "Competitive Programming|Dynamic Programming|System Architecture"
            }
        ]

        print("Adding companies...")
        for data in companies_data:
            c = Company(**data)
            db.session.add(c)
        db.session.commit()

        # Add posts
        print("Adding sample posts...")
        posts_data = [
            # TCS
            {"c_name": "TCS", "title": "My TCS NQT Experience", "content": "The aptitude section was tougher than expected. Focus heavily on time, speed, distance problems! The coding rounds were standard array/string manipulations.", "type": "experience"},
            {"c_name": "TCS", "title": "Tip for Technical HR", "content": "Be very well-versed with your resume projects. They asked me to explain my database schema in depth.", "type": "tip"},
            
            # Infosys
            {"c_name": "Infosys", "title": "Infosys System Engineer Interview", "content": "Questions were mostly around OOPS concepts in Python and a few basic SQL queries like JOINS.", "type": "experience"},
            {"c_name": "Infosys", "title": "What comes in Pseudo code round?", "content": "Does anyone know the difficulty level of the pseudocode section?", "type": "question"},
            
            # Wipro
            {"c_name": "Wipro", "title": "Wipro WILP Assessment", "content": "The essay writing section requires good grammar and a decent typing speed. Practiced typing every day!", "type": "tip"},
            
            # Amazon
            {"c_name": "Amazon", "title": "SDE1 Interview Experience", "content": "The Bar Raiser round was intense. It focused entirely on Leadership Principles. Do NOT ignore the Amazon LPs!", "type": "experience"},
            {"c_name": "Amazon", "title": "Tips for Amazon OA", "content": "Practice sliding window and greedy algorithms. LeetCode medium questions are very similar to what gets asked.", "type": "tip"},
            {"c_name": "Amazon", "title": "System design for SDE1?", "content": "Do they ask low-level or high-level design for freshers?", "type": "question"},
            
            # Google
            {"c_name": "Google", "title": "Google SWE Interview", "content": "4 rounds of technical onsite. Expect heavy graph traversal and dynamic programming. Communication is graded! Always explain your thought process.", "type": "experience"},
            {"c_name": "Google", "title": "Graph algorithms to focus on?", "content": "Which graph algos are most frequently asked? Is max flow necessary?", "type": "question"}
        ]
        
        for p in posts_data:
            company = Company.query.filter_by(name=p['c_name']).first()
            if company:
                post = CompanyPost(
                    company_id=company.id,
                    user_id=admin_user.id,
                    title=p['title'],
                    content=p['content'],
                    post_type=p['type']
                )
                db.session.add(post)
                
        db.session.commit()
        print("Seeding completed successfully!")

if __name__ == '__main__':
    seed_companies()
