"""
Credit management functionality for Mockly application
Handles credit checking, deduction, and transaction tracking
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional
import uuid

from app.database import get_async_session
from app.models import User, UserCreditTransaction
from app.user_schemas import (
    CreditBalanceResponse, CreditTransactionResponse, 
    CreditTransactionsResponse, PurchaseCreditsRequest
)
from app.auth import current_active_user

router = APIRouter(prefix="/credits", tags=["credits"])

async def check_user_credits(user_id: str, session: AsyncSession, required_credits: int = 1) -> bool:
    """
    Check if user has sufficient credits for an operation
    Returns True if user has enough credits, False otherwise
    """
    query = select(User.credits).where(User.id == user_id)
    result = await session.execute(query)
    user_credits = result.scalar_one_or_none()
    
    if user_credits is None:
        return False
    
    return user_credits >= required_credits

async def deduct_credits(
    user_id: str, 
    session: AsyncSession, 
    amount: int = 1, 
    transaction_type: str = "session_start",
    description: str = "Interview session started",
    session_id: Optional[str] = None
) -> bool:
    """
    Deduct credits from user account and create transaction record
    Returns True if successful, False if insufficient credits
    """
    # Check if user has enough credits
    if not await check_user_credits(user_id, session, amount):
        return False
    
    # Get current user
    user_query = select(User).where(User.id == user_id)
    user_result = await session.execute(user_query)
    user = user_result.scalar_one_or_none()
    
    if not user:
        return False
    
    # Deduct credits
    user.credits -= amount
    
    # Create transaction record
    transaction = UserCreditTransaction(
        user_id=user_id,
        transaction_type=transaction_type,
        credits_change=-amount,  # Negative for deduction
        credits_balance_after=user.credits,
        description=description,
        session_id=session_id
    )
    
    session.add(transaction)
    session.add(user)
    await session.commit()
    
    return True

async def add_credits(
    user_id: str,
    session: AsyncSession,
    amount: int,
    transaction_type: str = "purchase",
    description: str = "Credits purchased",
    session_id: Optional[str] = None
) -> bool:
    """
    Add credits to user account and create transaction record
    Returns True if successful
    """
    # Get current user
    user_query = select(User).where(User.id == user_id)
    user_result = await session.execute(user_query)
    user = user_result.scalar_one_or_none()
    
    if not user:
        return False
    
    # Add credits
    user.credits += amount
    
    # Create transaction record
    transaction = UserCreditTransaction(
        user_id=user_id,
        transaction_type=transaction_type,
        credits_change=amount,  # Positive for addition
        credits_balance_after=user.credits,
        description=description,
        session_id=session_id
    )
    
    session.add(transaction)
    session.add(user)
    await session.commit()
    
    return True

@router.get("/balance", response_model=CreditBalanceResponse)
async def get_credit_balance(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get current user's credit balance"""
    return CreditBalanceResponse(
        credits=user.credits,
        message=f"You have {user.credits} credits remaining"
    )

@router.get("/transactions", response_model=CreditTransactionsResponse)
async def get_credit_transactions(
    limit: int = 20,
    offset: int = 0,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get user's credit transaction history"""
    
    # Get total count
    count_query = select(func.count(UserCreditTransaction.id)).where(
        UserCreditTransaction.user_id == user.id
    )
    count_result = await session.execute(count_query)
    total_transactions = count_result.scalar()
    
    # Get transactions
    query = select(UserCreditTransaction).where(
        UserCreditTransaction.user_id == user.id
    ).order_by(desc(UserCreditTransaction.created_at)).offset(offset).limit(limit)
    
    result = await session.execute(query)
    transactions = result.scalars().all()
    
    return CreditTransactionsResponse(
        transactions=transactions,
        total_transactions=total_transactions
    )

@router.post("/purchase", response_model=CreditBalanceResponse)
async def purchase_credits(
    purchase_data: PurchaseCreditsRequest,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Purchase additional credits
    Note: This is a placeholder - actual payment processing would be implemented here
    """
    if purchase_data.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be positive"
        )
    
    # In a real implementation, you would:
    # 1. Process payment through Stripe/PayPal
    # 2. Verify payment success
    # 3. Add credits only after successful payment
    
    # For now, we'll simulate a successful purchase
    success = await add_credits(
        user_id=user.id,
        session=session,
        amount=purchase_data.amount,
        transaction_type="purchase",
        description=f"Purchased {purchase_data.amount} credits via {purchase_data.payment_method}"
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add credits"
        )
    
    # Refresh user data
    await session.refresh(user)
    
    return CreditBalanceResponse(
        credits=user.credits,
        message=f"Successfully purchased {purchase_data.amount} credits. New balance: {user.credits} credits"
    )

@router.post("/refund", response_model=CreditBalanceResponse)
async def refund_credits(
    amount: int,
    reason: str,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Refund credits to user account (admin function)
    Note: This would typically be an admin-only endpoint
    """
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be positive"
        )
    
    success = await add_credits(
        user_id=user.id,
        session=session,
        amount=amount,
        transaction_type="refund",
        description=f"Refund: {reason}"
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refund credits"
        )
    
    # Refresh user data
    await session.refresh(user)
    
    return CreditBalanceResponse(
        credits=user.credits,
        message=f"Successfully refunded {amount} credits. New balance: {user.credits} credits"
    )

# Credit validation middleware function
async def validate_credits_for_session(
    user: User,
    session: AsyncSession,
    required_credits: int = 1
) -> bool:
    """
    Validate that user has enough credits to start a session
    Returns True if valid, raises HTTPException if not
    """
    if not await check_user_credits(user.id, session, required_credits):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient credits. You need {required_credits} credit(s) to start a session. Current balance: {user.credits} credits."
        )
    return True
