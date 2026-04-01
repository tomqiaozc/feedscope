from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepo:
    def __init__(self, user_id: str, session: AsyncSession):
        self.user_id = user_id
        self.session = session

    def _user_filter(self, model):
        return model.user_id == self.user_id

    async def list(self):
        raise NotImplementedError

    async def get(self, id):
        raise NotImplementedError

    async def create(self, **kwargs):
        raise NotImplementedError

    async def update(self, id, **kwargs):
        raise NotImplementedError

    async def delete(self, id):
        raise NotImplementedError
