from sqlalchemy import  Column, ForeignKey, Integer, String, DateTime, Boolean, Double
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# Базовая модель
class Base(DeclarativeBase): pass

# Модель пользователя
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key = True, index = True)
    login = Column(String)
    role = Column(String, default='driver')
    password = Column(String)
    created_at = Column(DateTime, default=func.now())
    orders = relationship("Order", back_populates="driver")

# Модель заказа
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key = True, index = True)
    title = Column(String)
    addresFrom = Column(String)
    addresTo = Column(String)
    description = Column(String)
    requiredLoaders = Column(Integer)
    rigging = Column(Boolean)
    disassembly = Column(Boolean)
    latitude = Column(Double)
    longitude = Column(Double)
    driver_id = Column(Integer, ForeignKey("users.id"), nullable=True, default=None)
    created_at = Column(DateTime, default=func.now())
    driver = relationship("User", back_populates="orders")