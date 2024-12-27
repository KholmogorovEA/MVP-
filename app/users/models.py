from app.database import Base
from sqlalchemy import Column, String, Integer



class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    mobile = Column(String, nullable=False)

# после мигрируем модель с бэка в постгрес
# alembic revision --autogenerate -m "Initial migration"
# alembic upgrade head