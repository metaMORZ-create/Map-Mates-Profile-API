from fastapi import FastAPI
from db import engine
import models as tables
from routers import users  # <--- importiere deine Router

app = FastAPI()

tables.Base.metadata.create_all(bind=engine)

# Routen registrieren
app.include_router(users.router, prefix="/users", tags=["users"])
#app.include_router(locations.router, prefix="/locations", tags=["locations"])
