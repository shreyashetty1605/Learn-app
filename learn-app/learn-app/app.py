from flask import Flask
from flask_login import LoginManager
from models import db, User, Domain, Topic, Application
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'learn-secret-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)

    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from routes.auth_routes import auth_bp
    from routes.main_routes import main_bp
    from routes.application_routes import app_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(app_bp)

    return app


def seed_data(app):
    with app.app_context():
        if Domain.query.first():
            return  # Already seeded

        # Create admin user
        admin = User(name='Admin', email='admin@learn.com', role='admin', is_verified=True, reputation=999)
        admin.set_password('admin123')
        db.session.add(admin)

        # Create sample contributor
        prof = User(name='Dr. Sarah Chen', email='sarah@learn.com', role='user', is_verified=True, reputation=450)
        prof.set_password('password123')
        db.session.add(prof)

        # Domains
        domains_data = [
            ('Physics', '⚛️', 'Explore the fundamental laws governing matter, energy, space and time.'),
            ('Chemistry', '🧪', 'Discover chemical reactions, molecular structures and material properties.'),
            ('Biology', '🧬', 'Understand life, organisms, ecosystems and biological processes.'),
            ('Mathematics', '📐', 'The universal language of patterns, logic and quantitative reasoning.'),
            ('Computer Science', '💻', 'Algorithms, data structures, software engineering and computation.'),
            ('AI & Machine Learning', '🤖', 'Intelligent systems, neural networks and data-driven learning.'),
            ('Mechanical Engineering', '⚙️', 'Design and analysis of mechanical systems and devices.'),
            ('Electrical Engineering', '⚡', 'Circuits, electromagnetism, electronics and power systems.'),
            ('Medical & Healthcare', '🏥', 'Medicine, physiology, diagnostics and therapeutic techniques.'),
            ('Economics & Finance', '📈', 'Markets, decision-making, resource allocation and financial systems.'),
            ('Psychology', '🧠', 'Human behavior, cognition, emotion and mental processes.'),
            ('Environmental Science', '🌿', 'Earth systems, ecology, climate and sustainability.'),
            ('Architecture & Design', '🏛️', 'Built environments, spatial design and aesthetic principles.'),
            ('Civil Engineering', '🌉', 'Infrastructure, structures, transportation and urban systems.'),
            ('Business & Management', '💼', 'Strategy, operations, leadership and organizational behavior.'),
        ]

        domain_objs = {}
        for name, icon, desc in domains_data:
            d = Domain(name=name, icon=icon, description=desc)
            db.session.add(d)
            domain_objs[name] = d

        db.session.flush()

        # Physics Topics
        physics = domain_objs['Physics']
        bernoulli = Topic(
            name="Bernoulli's Principle",
            domain_id=physics.id,
            explanation="Bernoulli's Principle states that as the speed of a fluid increases, its pressure decreases. "
                        "In simpler terms: fast-moving fluid has lower pressure than slow-moving fluid. "
                        "This elegant relationship between velocity and pressure is one of the most powerful ideas in fluid dynamics, "
                        "explaining phenomena from airplane lift to the curve of a football."
        )
        newton_laws = Topic(
            name="Newton's Laws of Motion",
            domain_id=physics.id,
            explanation="Newton's three laws describe how objects move. First: an object stays at rest or in motion unless acted upon by a force. "
                        "Second: Force equals mass times acceleration (F=ma). Third: Every action has an equal and opposite reaction. "
                        "These laws form the foundation of classical mechanics."
        )
        thermodynamics = Topic(
            name="Laws of Thermodynamics",
            domain_id=physics.id,
            explanation="Thermodynamics studies heat, energy, and their transformations. The four laws govern how energy flows in systems, "
                        "why engines have efficiency limits, and why time moves in one direction. Entropy, the measure of disorder, always increases."
        )
        db.session.add_all([bernoulli, newton_laws, thermodynamics])

        # CS Topics
        cs = domain_objs['Computer Science']
        binary_search = Topic(
            name="Binary Search",
            domain_id=cs.id,
            explanation="Binary search is an efficient algorithm for finding an item in a sorted list. "
                        "It works by repeatedly halving the search space — comparing the target to the middle element "
                        "and eliminating the half where the target cannot be. This gives O(log n) time complexity, "
                        "making it dramatically faster than linear search for large datasets."
        )
        encryption = Topic(
            name="Encryption & Cryptography",
            domain_id=cs.id,
            explanation="Cryptography is the science of secure communication. Modern encryption converts readable data into scrambled ciphertext "
                        "using mathematical algorithms and keys. Only the intended recipient with the right key can decrypt it. "
                        "It underpins everything from online banking to private messaging."
        )
        db.session.add_all([binary_search, encryption])

        # Biology Topics
        bio = domain_objs['Biology']
        dna_replication = Topic(
            name="DNA Replication",
            domain_id=bio.id,
            explanation="DNA replication is the process by which a cell copies its DNA before cell division. "
                        "The double helix unwinds, and each strand serves as a template for a new complementary strand. "
                        "This semi-conservative process ensures genetic information is faithfully passed to daughter cells."
        )
        db.session.add(dna_replication)

        # Math Topics
        math = domain_objs['Mathematics']
        calculus = Topic(
            name="Calculus — Derivatives & Integrals",
            domain_id=math.id,
            explanation="Calculus is the mathematics of continuous change. Derivatives measure instantaneous rates of change (how fast something is changing). "
                        "Integrals measure accumulation (how much has changed over time). Together, they describe everything from planetary orbits to the spread of disease."
        )
        db.session.add(calculus)

        db.session.flush()

        # Applications for Bernoulli's Principle
        apps_data = [
            {
                'topic_id': bernoulli.id,
                'user_id': prof.id,
                'title': 'Airplane Wing Lift Generation',
                'description': 'Aircraft wings (airfoils) are shaped so air travels faster over the curved top surface than the flat bottom. '
                               'Per Bernoulli\'s Principle, this faster airflow creates lower pressure above the wing than below, '
                               'generating the upward lift force that keeps planes airborne. Without this pressure differential, '
                               'commercial aviation would be impossible. Engineers carefully design wing curvature and angle of attack '
                               'to maximize lift while minimizing drag.',
                'application_domain': 'Aerospace Engineering',
                'image_path': 'airplane_wing.svg',
                'tags': 'aviation, aerodynamics, lift, airfoil, pressure',
                'vote_count': 142,
            },
            {
                'topic_id': bernoulli.id,
                'user_id': prof.id,
                'title': 'Carburetor in Internal Combustion Engines',
                'description': 'A carburetor uses Bernoulli\'s Principle to mix air and fuel in the correct ratio for combustion. '
                               'Air is forced through a narrow venturi section, causing its velocity to increase and pressure to drop. '
                               'This low pressure region draws fuel up through a small nozzle and atomizes it into the airstream. '
                               'The resulting air-fuel mixture enters the engine cylinders for combustion. Though modern engines use fuel injection, '
                               'carburetors powered automobiles for nearly a century.',
                'application_domain': 'Mechanical Engineering',
                'image_path': 'carburetor.svg',
                'tags': 'automotive, engine, fuel, venturi, combustion',
                'vote_count': 98,
            },
            {
                'topic_id': bernoulli.id,
                'user_id': admin.id,
                'title': 'Blood Flow & Arterial Stenosis Detection',
                'description': 'Bernoulli\'s Principle governs blood flow in our circulatory system. When arteries narrow due to plaque buildup (stenosis), '
                               'blood must flow faster through the constricted section — just like water through a pinched hose. '
                               'This creates a pressure drop across the narrowing, which cardiologists can measure using Doppler ultrasound. '
                               'The pressure gradient indicates the severity of the blockage and helps diagnose coronary artery disease without invasive surgery.',
                'application_domain': 'Medical & Healthcare',
                'image_path': 'blood_flow.svg',
                'tags': 'cardiology, blood flow, stenosis, medical, diagnosis',
                'vote_count': 115,
            },
        ]

        for app_data in apps_data:
            application = Application(**app_data)
            db.session.add(application)

        # Applications for Newton's Laws
        rocket = Application(
            topic_id=newton_laws.id,
            user_id=prof.id,
            title='Rocket Propulsion — Newton\'s Third Law',
            description='Rockets work entirely on Newton\'s Third Law: for every action there is an equal and opposite reaction. '
                        'Burning fuel expels hot gases downward at extremely high velocities (action). '
                        'The rocket is pushed upward with equal force (reaction). In the vacuum of space where there\'s no air to push against, '
                        'this reaction principle is the only means of propulsion. The Saturn V rocket that carried Apollo astronauts to the moon '
                        'produced 7.5 million pounds of thrust through this principle alone.',
            application_domain='Aerospace Engineering',
            image_path='rocket.svg',
            tags='rocket, space, propulsion, NASA, reaction force',
            vote_count=201,
        )
        db.session.add(rocket)

        # Binary search application
        db_index = Application(
            topic_id=binary_search.id,
            user_id=admin.id,
            title='Database Index Lookups',
            description='Modern databases use B-trees (a generalization of binary search) to index millions of records. '
                        'When you search for a user by email or a product by ID, the database performs a binary-search-like traversal '
                        'of its index tree rather than scanning every row. A table with 1 billion records requires at most 30 comparisons '
                        'using binary search (log₂ of 1 billion ≈ 30), versus 500 million comparisons on average for a linear scan. '
                        'This is what makes SQL queries return in milliseconds instead of minutes.',
            application_domain='Computer Science',
            image_path='database_index.svg',
            tags='database, indexing, B-tree, SQL, performance',
            vote_count=178,
        )
        db.session.add(db_index)

        db.session.commit()
        print("✅ Database seeded successfully!")


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
        seed_data(app)
    app.run(debug=True, port=5000)
