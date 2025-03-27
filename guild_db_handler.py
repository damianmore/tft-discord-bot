import sqlite3 

class GuildNotFoundError(Exception):
    pass

class GuildDataHandler():
    def __init__(self):
        self.guild_conn = sqlite3.connect('tft_guild.db')
        self.guild_cursor = self.guild_conn.cursor()
        self.guild_cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS guilds (
            guild_id INTEGER PRIMARY KEY,
            permission BOOLEAN NOT NULL
        );
        """
        )
        self.guild_conn.commit()

    def add_guild(self,guild_id):
        self.guild_cursor.execute("INSERT OR REPLACE INTO guilds (guild_id, permission) VALUES (?, ?)", (guild_id, False))
        self.guild_conn.commit()
    
    def update_guild(self,guild_id, permission):
        self.guild_cursor.execute("UPDATE guilds SET permission = ? WHERE guild_id = ?", (permission, guild_id))
        self.guild_conn.commit()

    def remove_guild(self,guild_id):
        self.guild_cursor.execute("DELETE FROM guilds WHERE guild_id = ?", (guild_id,))
        self.guild_conn.commit()
    
    def check_guild(self,guild_id) -> bool:
        self.guild_cursor.execute("SELECT permission FROM guilds WHERE guild_id = ?", (guild_id,))
        result = self.guild_cursor.fetchone()

        if result is not None:
            return bool(result[0])  
        raise GuildNotFoundError 

    def get_approved_guilds(self):
        self.guild_cursor.execute("SELECT guild_id, permission FROM guilds WHERE permission = 1")
        return {row[0]: bool(row[1]) for row in self.guild_cursor.fetchall()}



    


    

