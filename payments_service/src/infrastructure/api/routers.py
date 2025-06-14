from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal

from src.application.dtos import CreateAccountRequest, TopUpAccountRequest, AccountBalanceResponse, PaymentProcessRequest, AccountResponse
from src.application.use_cases import CreateAccountUseCase, TopUpAccountUseCase, GetAccountBalanceUseCase, ProcessPaymentUseCase
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.repositories_impl import AccountRepository, InboxMessageRepository, OutboxMessageRepository

router = APIRouter()

def get_account_use_case(db: Session = Depends(get_db)) -> CreateAccountUseCase:
    return CreateAccountUseCase(AccountRepository(db))

def get_top_up_use_case(db: Session = Depends(get_db)) -> TopUpAccountUseCase:
    return TopUpAccountUseCase(AccountRepository(db))

def get_get_balance_use_case(db: Session = Depends(get_db)) -> GetAccountBalanceUseCase:
    return GetAccountBalanceUseCase(AccountRepository(db))

def get_process_payment_use_case(
    db: Session = Depends(get_db)
) -> ProcessPaymentUseCase:
    return ProcessPaymentUseCase(
        AccountRepository(db),
        InboxMessageRepository(db),
        OutboxMessageRepository(db)
    )


@router.post(
    "/accounts", 
    response_model=AccountResponse, 
    status_code=status.HTTP_201_CREATED, 
    summary="Создать счёт для пользователя"
)
def create_account_endpoint(
    request: CreateAccountRequest,
    use_case: CreateAccountUseCase = Depends(get_account_use_case),
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

@router.post(
    "/accounts/top-up", 
    response_model=AccountBalanceResponse, 
    summary="Пополнить счёт пользователя"
)
def top_up_account_endpoint(
    request: TopUpAccountRequest,
    use_case: TopUpAccountUseCase = Depends(get_top_up_use_case),
    db: Session = Depends(get_db)
):
    try:
        response = use_case.execute(request)
        db.commit()
        return response
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get(
    "/accounts/{user_id}/balance", 
    response_model=AccountBalanceResponse, 
    summary="Просмотреть баланс счёта"
)
def get_account_balance_endpoint(
    user_id: int,
    use_case: GetAccountBalanceUseCase = Depends(get_get_balance_use_case)
):
    try:
        return use_case.execute(user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post(
    "/payments/process", 
    status_code=status.HTTP_200_OK, 
    summary="Обработка платежа (Transactional Inbox)"
)
def process_payment_endpoint(
    request: PaymentProcessRequest,
    use_case: ProcessPaymentUseCase = Depends(get_process_payment_use_case),
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