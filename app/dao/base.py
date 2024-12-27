from app.database import async_session_maker
from sqlalchemy import select, insert

class BaseDAO:
    model = None


    @classmethod
    async def find_by_id(cls, model_id: int):
        async with async_session_maker() as session: # type: ignore
            query = select(cls.model).filter_by(id=model_id) # type: ignore
            result = await session.execute(query) 
            return result.scalar_one_or_none()
        

    @classmethod
    async def find_by_one_or_none(cls, **filter_by):
        async with async_session_maker() as session: # type: ignore
            query = select(cls.model).filter_by(**filter_by) # type: ignore
            result = await session.execute(query)
            return result.scalar_one_or_none()


    @classmethod
    async def find_all(cls, **filter_by):
        async with async_session_maker() as session: # type: ignore
            query = select(cls.model).filter_by(**filter_by) # type: ignore
            result = await session.execute(query)
            return result.scalars().all()



    @classmethod
    async def add(cls, **data):
        async with async_session_maker() as session: # type: ignore
            query = insert(cls.model).values(**data) # type: ignore
            await session.execute(query)
            await session.commit()