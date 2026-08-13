from persistence.database import AsyncSessionLocal

class UnitOfWork:
    def __init__(self):
        self.session_factory = AsyncSessionLocal
        self.session = None

    async def __aenter__(self):
        self.session = self.session_factory()
        # Initialize repositories here, injecting self.session
        # self.users = UserRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc_val, traceback):
        if exc_type is not None:
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()