from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.application.dtos import CreateOrderRequest, OrderResponse, PaymentStatusUpdateRequest
from src.application.use_cases import CreateOrderUseCase, GetUserOrdersUseCase, GetOrderStatusUseCase, UpdateOrderPaymentStatusUseCase
from src.domain.value_objects import OrderStatus
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.repositories_impl import OrderRepository, OutboxMessageRepository, PaymentStatusInboxRepository

router = APIRouter()

def get_create_order_use_case(
    db: Session = Depends(get_db)
) -> CreateOrderUseCase:
    return CreateOrderUseCase(
        OrderRepository(db),
        OutboxMessageRepository(db)
    )

def get_get_user_orders_use_case(
    db: Session = Depends(get_db)
) -> GetUserOrdersUseCase:
    return GetUserOrdersUseCase(OrderRepository(db))

def get_get_order_status_use_case(
    db: Session = Depends(get_db)
) -> GetOrderStatusUseCase:
    return GetOrderStatusUseCase(OrderRepository(db))

def get_update_order_payment_status_use_case(
    db: Session = Depends(get_db)
) -> UpdateOrderPaymentStatusUseCase:
    return UpdateOrderPaymentStatusUseCase(
        OrderRepository(db),
        PaymentStatusInboxRepository(db)
    )

@router.post(
    "/orders", 
    response_model=OrderResponse, 
    status_code=status.HTTP_201_CREATED, 
    summary="Создать новый заказ"
)
def create_order_endpoint(
    request: CreateOrderRequest,
    use_case: CreateOrderUseCase = Depends(get_create_order_use_case),
    db: Session = Depends(get_db)
):
    try:
        response = use_case.execute(request)
        db.commit()
        return response
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Неожиданная ошибка: {e}")

@router.get(
    "/orders", 
    response_model=List[OrderResponse], 
    summary="Получить список заказов пользователя"
)
def get_user_orders_endpoint(
    user_id: int,
    use_case: GetUserOrdersUseCase = Depends(get_get_user_orders_use_case)
):
    try:
        return use_case.execute(user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Неожиданная ошибка: {e}")

@router.get(
    "/orders/{order_id}", 
    response_model=OrderResponse, 
    summary="Получить статус отдельного заказа"
)
def get_order_status_endpoint(
    order_id: str,
    use_case: GetOrderStatusUseCase = Depends(get_get_order_status_use_case)
):
    try:
        return use_case.execute(order_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Неожиданная ошибка: {e}")

@router.post(
    "/orders/payment-status", 
    status_code=status.HTTP_200_OK, 
    summary="Обновить статус заказа по результату оплаты (Transactional Inbox)"
)
def update_order_payment_status_endpoint(
    request: PaymentStatusUpdateRequest,
    use_case: UpdateOrderPaymentStatusUseCase = Depends(get_update_order_payment_status_use_case),
    db: Session = Depends(get_db)
):
    try:
        response = use_case.execute(request)
        db.commit()
        return response
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) 