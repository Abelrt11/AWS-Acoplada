from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uvicorn

from .models import Contact, ContactCreate, ContactUpdate
from .repository import IContactRepository
from .dynamo_repository import DynamoContactRepository
from .config import ALLOW_ORIGINS, PORT

app = FastAPI(title="Contacts API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOW_ORIGINS] if ALLOW_ORIGINS != "*" else ["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

def get_repo() -> IContactRepository:
    repo = DynamoContactRepository()
    repo.initialize()
    return repo

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/contacts", response_model=Contact, status_code=201)
def create_contact(payload: ContactCreate, repo: IContactRepository = Depends(get_repo)):
    try:
        return repo.create(payload)
    except ValueError as e:
        if str(e) == "email_already_exists":
            raise HTTPException(status_code=409, detail="Email already exists")
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/contacts/{contact_id}", response_model=Contact)
def get_contact(contact_id: str, repo: IContactRepository = Depends(get_repo)):
    c = repo.get(contact_id)
    if not c:
        raise HTTPException(status_code=404, detail="Not found")
    return c

@app.get("/contacts", response_model=List[Contact])
def list_contacts(tag: Optional[str] = Query(None), repo: IContactRepository = Depends(get_repo)):
    return repo.list(tag=tag)

@app.put("/contacts/{contact_id}", response_model=Contact)
def update_contact(contact_id: str, payload: ContactUpdate, repo: IContactRepository = Depends(get_repo)):
    try:
        c = repo.update(contact_id, payload)
        if not c:
            raise HTTPException(status_code=404, detail="Not found")
        return c
    except ValueError as e:
        if str(e) == "email_already_exists":
            raise HTTPException(status_code=409, detail="Email already exists")
        raise

@app.delete("/contacts/{contact_id}", status_code=204)
def delete_contact(contact_id: str, repo: IContactRepository = Depends(get_repo)):
    ok = repo.delete(contact_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Not found")
    return None

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=PORT, reload=False)
