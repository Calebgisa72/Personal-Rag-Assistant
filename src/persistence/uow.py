from persistence.database import AsyncSessionLocal
from persistence.repositories import UserRepository, ConversationRepository, DocumentRepository

class UnitOfWork:
    def __init__(self):
        self.session_factory = AsyncSessionLocal
        self.session = None

    async def __aenter__(self):
        self.session = self.session_factory()
        self.users = UserRepository(self.session)
        self.conversations = ConversationRepository(self.session)
        self.documents = DocumentRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc_val, traceback):
        if exc_type is not None:
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()