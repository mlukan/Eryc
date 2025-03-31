from sqlalchemy import (
    Column, Integer, String, Boolean, Text,Float, LargeBinary,  ForeignKey, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set up the engine and session

engine = create_engine("sqlite:///../data/calendar.db")
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(String)
    sex = Column(String, CheckConstraint("sex in ('M', 'F', 'O')"))
    phone = Column(String)
    address = Column(String)
    dob = Column(Integer)

    bookings = relationship("Booking", back_populates="user")
    forms = relationship("Form", back_populates="user")
    session = relationship("Session", back_populates="user", uselist=False)

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}')>"

class Location(Base):
    __tablename__ = 'locations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)

    bookings = relationship("Booking", back_populates="location_rel")
    slots = relationship("Slot", back_populates="location_rel")

    def __repr__(self):
        return f"<Location(id={self.id}, name='{self.name}')>"

class Booking(Base):
    __tablename__ = 'booking'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, ForeignKey("users.email"), nullable=False)
    timestamp = Column(Integer, nullable=False)
    donation_type = Column(String, nullable=False)
    location = Column(String, ForeignKey("locations.name"), nullable=False)
    success = Column(Boolean, nullable=False)
    status = Column(String, nullable=False)
    note = Column(Text)

    user = relationship("User", back_populates="bookings")
    location_rel = relationship("Location", back_populates="bookings")

    def __repr__(self):
        return (f"<Booking(id={self.id}, email='{self.email}', "
                f"location='{self.location}', timestamp={self.timestamp}, "
                f"success={self.success})>")

class Slot(Base):
    __tablename__ = 'slots'

    id = Column(Integer, primary_key=True, autoincrement=True)
    location = Column(String, ForeignKey("locations.name"), nullable=False)
    timestamp = Column(Integer, nullable=False)
    slots_total = Column(Integer, nullable=False)
    slots_remaining = Column(Integer, nullable=False)

    location_rel = relationship("Location", back_populates="slots")

    def __repr__(self):
        return (f"<Slot(id={self.id}, location='{self.location}', "
                f"timestamp={self.timestamp}, remaining={self.slots_remaining})>")

class Session(Base):
    __tablename__ = 'sessions'

    email = Column(String, ForeignKey("users.email"), primary_key=True)
    session = Column(String)
    code = Column(Integer)
    expires = Column(Integer)

    user = relationship("User", back_populates="session")

    def __repr__(self):
        return f"<Session(email='{self.email}', code={self.code}, expires={self.expires})>"

class Form(Base):
    __tablename__ = 'forms'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, ForeignKey("users.email"), nullable=False)
    data = Column(Text)
    timestamp = Column(String)
    expires = Column(String)
    form_id = Column(String)

    user = relationship("User", back_populates="forms")

    def __repr__(self):
        return f"<Form(id={self.id}, email='{self.email}', form_id='{self.form_id}')>"

### FAQ and Feedback tables

class FAQ(Base):
    __tablename__ = 'faq'

    id = Column(Integer, primary_key=True, autoincrement=True)
    section_name = Column(String)
    section_id = Column(String)
    faq_subsection_name = Column(String)
    questions = Column(Text)        # Assumed to be a stringified list
    response = Column(Text)
    embeddings = Column(LargeBinary)  # Vector data, e.g., from OpenAI

    def __repr__(self):
        return (f"<FAQ(id={self.id}, section='{self.section_name}', "
                f"subsection='{self.faq_subsection_name}')>")

class Feedback(Base):
    __tablename__ = 'feedbacks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sender = Column(String)
    feedback = Column(Text)
    response = Column(Text)
    question = Column(Text)
    timestamp = Column(Float)  # assuming UNIX timestamp or float

    def __repr__(self):
        return (f"<Feedback(id={self.id}, sender='{self.sender}', "
                f"question='{self.question[:30]}...', timestamp={self.timestamp})>")
