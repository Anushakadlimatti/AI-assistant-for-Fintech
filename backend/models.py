from sqlalchemy import Column, Integer, String, Numeric, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(Integer, primary_key=True, index=True)
    cif = Column(String, unique=True, index=True, nullable=False)
    customer_name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    branch = Column(String, nullable=False)

    # Relationships
    fd_bookings = relationship("FDBooking", back_populates="customer", cascade="all, delete-orphan")
    rd_bookings = relationship("RDBooking", back_populates="customer", cascade="all, delete-orphan")

class FDBooking(Base):
    __tablename__ = "fd_bookings"

    fd_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    fd_number = Column(String, unique=True, index=True, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    interest_rate = Column(Numeric(5, 2), nullable=False)
    tenure_months = Column(Integer, nullable=False)
    booking_date = Column(Date, nullable=False)
    maturity_date = Column(Date, nullable=False)
    status = Column(String, nullable=False)  # e.g., ACTIVE, CLOSED, MATURED
    branch = Column(String, nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="fd_bookings")

class RDBooking(Base):
    __tablename__ = "rd_bookings"

    rd_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    rd_number = Column(String, unique=True, index=True, nullable=False)
    monthly_amount = Column(Numeric(15, 2), nullable=False)
    tenure_months = Column(Integer, nullable=False)
    booking_date = Column(Date, nullable=False)
    maturity_date = Column(Date, nullable=False)
    status = Column(String, nullable=False)  # e.g., ACTIVE, CLOSED, MATURED
    branch = Column(String, nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="rd_bookings")
