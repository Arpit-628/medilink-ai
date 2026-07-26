"""
Database setup — SQLite (no install/server needed, perfect for a hackathon demo).
Run this file directly once to create + seed the database: python database.py
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

engine = create_engine("sqlite:///medilink.db", echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Pharmacy(Base):
    __tablename__ = "pharmacies"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    rating = Column(Float)
    open_now = Column(Boolean, default=True)
    inventory = relationship("Inventory", back_populates="pharmacy")


class Medicine(Base):
    __tablename__ = "medicines"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    salt = Column(String)          # active ingredient -> used for alternatives
    dosage = Column(String)
    # comma-separated symptoms this medicine is commonly associated with (educational only)
    symptoms = Column(String)


class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id"))
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id"))
    stock = Column(Integer)
    price = Column(Float)

    medicine = relationship("Medicine")
    pharmacy = relationship("Pharmacy", back_populates="inventory")


def init_db():
    Base.metadata.create_all(engine)


def seed():
    """Insert demo data so the app has something to search/recommend on stage."""
    init_db()
    db = SessionLocal()

    if db.query(Pharmacy).first():
        db.close()
        return  # already seeded

    pharmacies = [
        Pharmacy(name="Apollo Pharmacy", latitude=20.2961, longitude=85.8245, rating=4.6, open_now=True),
        Pharmacy(name="MedPlus", latitude=20.2975, longitude=85.8210, rating=4.3, open_now=True),
        Pharmacy(name="Local Pharmacy", latitude=20.2950, longitude=85.8260, rating=4.1, open_now=False),
    ]
    db.add_all(pharmacies)
    db.commit()

    medicines = [
        Medicine(name="Paracetamol 650", salt="Paracetamol", dosage="650mg", symptoms="fever,headache,body pain"),
        Medicine(name="Dolo 650", salt="Paracetamol", dosage="650mg", symptoms="fever,headache,body pain"),
        Medicine(name="Crocin 650", salt="Paracetamol", dosage="650mg", symptoms="fever,headache"),
        Medicine(name="Calpol 650", salt="Paracetamol", dosage="650mg", symptoms="fever"),
        Medicine(name="Amoxicillin 500", salt="Amoxicillin", dosage="500mg", symptoms="infection,throat pain"),
        Medicine(name="Pantoprazole 40", salt="Pantoprazole", dosage="40mg", symptoms="acidity,stomach pain"),
        Medicine(name="Cetirizine 10", salt="Cetirizine", dosage="10mg", symptoms="cold,allergy,sneezing"),
    ]
    db.add_all(medicines)
    db.commit()

    # inventory: (medicine_name, pharmacy_name, stock, price)
    inv_data = [
        ("Dolo 650", "Apollo Pharmacy", 20, 28),
        ("Dolo 650", "MedPlus", 15, 26),
        ("Crocin 650", "Local Pharmacy", 2, 30),
        ("Paracetamol 650", "MedPlus", 40, 20),
        ("Amoxicillin 500", "Apollo Pharmacy", 10, 55),
        ("Pantoprazole 40", "MedPlus", 25, 45),
        ("Cetirizine 10", "Local Pharmacy", 12, 18),
    ]
    med_map = {m.name: m for m in db.query(Medicine).all()}
    pharm_map = {p.name: p for p in db.query(Pharmacy).all()}

    for med_name, pharm_name, stock, price in inv_data:
        db.add(Inventory(medicine_id=med_map[med_name].id,
                          pharmacy_id=pharm_map[pharm_name].id,
                          stock=stock, price=price))
    db.commit()
    db.close()


if __name__ == "__main__":
    seed()
    print("Database created and seeded: medilink.db")
