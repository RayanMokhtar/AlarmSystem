import psycopg2

from BaseModels import *

def calculer_Nb_lieu():
    try:

        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            cursor_factory=RealDictCursor
        )

        cur = conn.cursor()

        cur.execute("select count(*) from lieu")

        nb = cur.fetchone()
        return nb
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def calculer_Nb_equipement():
    try:

        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            cursor_factory=RealDictCursor
        )

        cur = conn.cursor()

        cur.execute("select count(*) from equipement")

        nb = cur.fetchone()
        return nb
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



def calculerEquipementEnPanne():
    try:

        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            cursor_factory=RealDictCursor
        )

        cur = conn.cursor()

        cur.execute("select count(*) from equipement where statut <> 'actif' ")

        nb = cur.fetchone()
        return nb
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
