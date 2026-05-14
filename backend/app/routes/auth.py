from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException

from app.config import get_settings
from app.routes.common import auth_status_out, get_app_settings_store, _extract_bearer_token, _resolve_token_subject
from app.schemas import AuthStatusOut, AuthUserOut, LoginRequest, LoginResponse
from app.security import create_token


router = APIRouter(prefix='/api')


@router.post('/auth/login', response_model=LoginResponse)
def login(payload: LoginRequest, store=Depends(get_app_settings_store)) -> LoginResponse:
    stored = store.authenticate(payload.username, payload.password)
    if stored is None:
        raise HTTPException(status_code=401, detail='用户名或密码错误')
    token = create_token(stored.admin_username, stored.auth_secret, expires_in_hours=get_settings().auth_token_ttl_hours)
    return LoginResponse(token=token, user=AuthUserOut(username=stored.admin_username), status=auth_status_out(stored, store, authenticated=True))


@router.get('/auth/status', response_model=AuthStatusOut)
def auth_status(
    authorization: Annotated[str | None, Header()] = None,
    store=Depends(get_app_settings_store),
) -> AuthStatusOut:
    stored = store.load()
    subject = _resolve_token_subject(_extract_bearer_token(authorization), store)
    return auth_status_out(stored, store, authenticated=subject == stored.admin_username)