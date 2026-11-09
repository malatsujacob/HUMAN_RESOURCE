import os

DATABASE_URL = os.getenv("DATABASE_URL",
    "postgresql://postgres:Jack.02.+ma@localhost:5432/HUMAN_RESOURCE",
)
SECRET_KEY = os.getenv("SECRET_KEY",
    "chapchap_super_secret_key_2026",
)
ALGORITHM = os.getenv("ALGORITHM",
    "HS256",
)
