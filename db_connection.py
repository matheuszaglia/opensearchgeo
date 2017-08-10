import sqlalchemy


class database:
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self._table_.columns}

    def __init__(self, user, pw, host, db):
        self.user = user
        self.pw = pw
        self.host = host
        self.db = db

    def do_query(self, sql):
        engine = sqlalchemy.create_engine('mysql://' + self.user + ':' + self.pw + '@' + self.host + '/' + self.db)
        result = engine.execute(sql)
        result = result.fetchall()
        engine.dispose()
        return result
