from fastapi import APIRouter

router = APIRouter()


@router.post("/uber")
def receive_webhook():
    # TODO: verify signature and dispatch to handlers
    return {"status": "received"}

