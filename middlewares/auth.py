from fastapi import Body, Request, Response
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware, DispatchFunction
from starlette.types import ASGIApp
from starlette import status
from jose import JWTError, jwt, ExpiredSignatureError
import os

swagger = [
    '/order/docs',
    '/order/openapi.json',
]

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        if request.url.path  in swagger:
            response = await call_next(request)
            return response
        
        body = await request.json()
        access_token = body['access_token']

        if access_token:
            userInfo: dict
            try:
                userInfo = jwt.decode(access_token, os.getenv('SECRET_KEY'))
            except ExpiredSignatureError:
                return Response(
                    content='Access token has expired, please log in again',
                    status_code=status.HTTP_403_FORBIDDEN
                )
            except JWTError:
                return Response(
                    content='Incorrect jwt token',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            response = await call_next(request)
            return response
        else:
            return Response(
                    content='No token - no bitches',
                    status_code=status.HTTP_403_FORBIDDEN
                )