from datetime import date, datetime, timedelta
import json
import os
from typing import Annotated
from fastapi import APIRouter, FastAPI, Query, Request, Depends, Response
from jose import jwt, ExpiredSignatureError
from pydantic import BaseModel
from starlette import status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from database.database import SessionLocal
from database.models import Order, User

from dotenv import load_dotenv

from middlewares.auth import AuthMiddleware

load_dotenv()

# Рут заметок
orderApp = FastAPI()

orderApp.add_middleware(AuthMiddleware)

class AuthRequest(BaseModel):
    access_token: str

class AuthOrderCreateRequest(AuthRequest):
    title: str
    addresFrom: str
    addresTo: str
    description: str
    requiredLoaders: int
    rigging: bool
    disassembly: bool
    latitud: float
    longitude: float

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class BaseResponse(BaseModel):
    status_code: int
    message: str

class OrderResponse(BaseResponse):
    note_title: str
    note_content: str
    created_at: str
    author_id: int

class TakeOrderRequest(AuthRequest):
    order_id: int

# Инъекция бд
db_dependency = Annotated[Session, Depends(get_db)]

# Создание заказа
@orderApp.post('/create')
def CreateOrder(
    db: db_dependency,
    orderRequest: AuthOrderCreateRequest):
    if db.query(Order).filter(
        and_(
            Order.description == orderRequest.description,
            Order.title == orderRequest.title)).first():
        return Response(
            content='Order already exists',
            status_code=status.HTTP_409_CONFLICT
        )
    else:
        newOrder = Order(
            title=orderRequest.title,
            addresFrom=orderRequest.addresFrom,
            addresTo=orderRequest.addresTo,
            description=orderRequest.description,
            requiredLoaders=orderRequest.requiredLoaders,
            rigging=orderRequest.rigging,
            disassembly=orderRequest.disassembly,
            latitude=orderRequest.latitud,
            longitude=orderRequest.longitude,
        )
        db.add(newOrder)
        db.commit()
        return Response(
            content='Ordere created successfuly',
            status_code=status.HTTP_201_CREATED
        )

# Взятие заказа
@orderApp.post('/take')
def TakeOrder(
    db: db_dependency,
    takeOrderRequest: TakeOrderRequest):

    token = takeOrderRequest.access_token
    
    if token:
        userInfo = jwt.decode(token, os.getenv('SECRET_KEY'))
        orderToTake = db.query(Order).filter(Order.id == takeOrderRequest.order_id).first()
        if(not orderToTake):
            return Response(
                content='No order with given ID',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        if(orderToTake.driver_id != None):
            return Response(
                content='Order already taken',
                status_code=status.HTTP_409_CONFLICT
            )
        else:
            orderToTake.driver_id = int(userInfo['user_id'])
            db.add(orderToTake)
            db.commit()
            return Response(
                content='Order has been taken',
                status_code=status.HTTP_202_ACCEPTED
            )

# Получение списка свободных заказов
@orderApp.post('/avaliable')
def AvaliableListOrders(
    db: db_dependency,
    request: AuthRequest):
    
    userOrders = db.query(Order).filter(
        Order.driver_id == None
    ).all()

    avaliableFilteredOrders = []
        
    for order in userOrders:
        avaliableFilteredOrders.append(
            {
                'id': order.id,
                'title': order.title,
                'addresFrom': order.addresFrom,
                'addresTo': order.addresTo,
                'description': order.description,
                'requiredLoaders': order.requiredLoaders,
                'rigging': order.rigging,
                'disassembly': order.disassembly,
                'latitud': order.latitude,
                'longitude': order.longitude
            }
        )
    print(avaliableFilteredOrders)
    return {
            'orders': avaliableFilteredOrders,
            'count': len(avaliableFilteredOrders)
            }

@orderApp.post('/my')
def MyListOrders(
    db: db_dependency,
    request: AuthRequest):
    
    token = request.access_token

    if token:
        userInfo: dict
        userInfo = jwt.decode(token, os.getenv('SECRET_KEY'))

        userOrders = db.query(Order).filter(
            Order.driver_id == int(userInfo['user_id'])
        ).all()

        usersFilteredOrders = []
        
        for order in userOrders:
            usersFilteredOrders.append(
                {
                    'id': order.id,
                    'title': order.title,
                    'addresFrom': order.addresFrom,
                    'addresTo': order.addresTo,
                    'description': order.description,
                    'requiredLoaders': order.requiredLoaders,
                    'rigging': order.rigging,
                    'disassembly': order.disassembly,
                    'latitud': order.latitude,
                    'longitude': order.longitude
                }
            )
        return {
                'orders': usersFilteredOrders,
                'count': len(usersFilteredOrders)
            }

# удаление заметки
@orderApp.delete('/remove')
def remove_note(
    db: db_dependency,
    request: AuthRequest,
    note_id: int = Query(None),):

    token = request.access_token

    if token:
        userInfo: dict
        try:
            userInfo = jwt.decode(token, os.getenv('SECRET_KEY'))
        except ExpiredSignatureError:
            return BaseResponse(
                message='Access token has expired, please log in again',
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        if note_id:
            # ищем заметку с данным id и проверям 
            noteDelete = db.query(Order).filter(
                and_(Order.id == note_id,      
                Order.author_id == userInfo['user_id'])
            ).first()
            # если нашли то удаляем ее, если нет, то уведомляем о том, что заметка не найдена
            if noteDelete:
                db.delete(noteDelete)
                db.commit()
                return BaseResponse(
                    message=f'Note with id {note_id} have been deleted',
                    status_code=status.HTTP_202_ACCEPTED
                )
            else:
                return BaseResponse(
                    message=f'Note with id {note_id} not found',
                    status_code=status.HTTP_404_NOT_FOUND
                )
        else:
            return BaseResponse(
                    message='note id undefined',
                    status_code=status.HTTP_404_NOT_FOUND
                )
    else:
        return BaseResponse(
                message='Unauthorized user request',
                status_code=status.HTTP_401_UNAUTHORIZED
            )