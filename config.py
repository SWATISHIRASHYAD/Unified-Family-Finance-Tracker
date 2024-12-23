import os

class Config:
    SQLALCHEMY_DATABASE_URI='mysql+pymysql://root:@localhost:3306/unified_family'
    SQL_ALCHEMY_TRACK_MODIFICATION=False
    SECRET_KEY=os.getenv('SECRET-KEY','your-swecret-key')