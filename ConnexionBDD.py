from datetime import date, datetime
from fastapi import FastAPI, HTTPException
import psycopg2
from pydantic import BaseModel, EmailStr
from psycopg2.extras import RealDictCursor
from uuid import UUID

DB_HOST = "postgresql-hammal.alwaysdata.net"
DB_NAME = "hammal_atelierrt"
DB_USER = "hammal"
DB_PASS = "Zahrdin.99"
