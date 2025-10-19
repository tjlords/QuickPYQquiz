import asyncpg

class Database:
    def __init__(self, url):
        self.url = url

    async def connect(self):
        self.conn = await asyncpg.connect(self.url)
        await self.conn.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id BIGINT PRIMARY KEY,
            title TEXT
        );
        CREATE TABLE IF NOT EXISTS folders (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE
        );
        CREATE TABLE IF NOT EXISTS questions (
            id SERIAL PRIMARY KEY,
            folder_id INTEGER REFERENCES folders(id),
            question TEXT,
            options TEXT[],
            correct TEXT,
            explanation TEXT
        );
        """)

    async def add_group(self, group_id, title):
        await self.conn.execute(
            "INSERT INTO groups (id, title) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            group_id, title
        )

    async def add_folder(self, name):
        await self.conn.execute(
            "INSERT INTO folders (name) VALUES ($1) ON CONFLICT DO NOTHING",
            name
        )

    async def add_question(self, folder_name, question, options, correct, explanation=None):
        folder = await self.conn.fetchrow("SELECT id FROM folders WHERE name=$1", folder_name)
        if not folder:
            await self.add_folder(folder_name)
            folder = await self.conn.fetchrow("SELECT id FROM folders WHERE name=$1", folder_name)
        await self.conn.execute(
            "INSERT INTO questions (folder_id, question, options, correct, explanation) VALUES ($1,$2,$3,$4,$5)",
            folder['id'], question, options, correct, explanation
        )

    async def get_random_question(self, folder_name):
        folder = await self.conn.fetchrow("SELECT id FROM folders WHERE name=$1", folder_name)
        if not folder:
            return None
        return await self.conn.fetchrow(
            "SELECT * FROM questions WHERE folder_id=$1 ORDER BY RANDOM() LIMIT 1",
            folder['id']
        )
