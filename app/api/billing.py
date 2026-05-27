import logging
from datetime import datetime, timezone

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user_hybrid
from app.orm_models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/billing", tags=["billing"])

TIER_LIMITS = {"free": 5, "pro": 100, "enterprise": 999999}

_price_to_tier: dict[str, str] = {}


def _get_price_to_tier() -> dict[str, str]:
    global _price_to_tier
    if not _price_to_tier and settings.stripe_price_pro_monthly:
        _price_to_tier = {
            settings.stripe_price_pro_monthly: "pro",
            settings.stripe_price_enterprise_monthly: "enterprise",
        }
    return _price_to_tier


def _stripe_configured() -> bool:
    return bool(settings.stripe_secret_key and settings.stripe_webhook_secret)


class BillingStatus(BaseModel):
    tier: str
    query_count_this_period: int
    limit: int
    billing_period_start: str | None
    usage_percentage: float
    has_subscription: bool


class CheckoutRequest(BaseModel):
    tier: str


@router.get("/status", response_model=BillingStatus)
async def get_billing_status(
    current_user: dict = Depends(get_current_user_hybrid),
):
    tier = current_user.get("subscription_tier", "free")
    query_count = current_user.get("query_count_this_period", 0)
    limit = TIER_LIMITS.get(tier, 5)
    billing_period_start = current_user.get("billing_period_start")
    if not billing_period_start:
        billing_period_start = datetime.now(timezone.utc).isoformat()
    usage_pct = (query_count / limit) * 100 if limit < 999999 else 0
    return BillingStatus(
        tier=tier,
        query_count_this_period=query_count,
        limit=limit,
        billing_period_start=billing_period_start,
        usage_percentage=round(usage_pct, 1),
        has_subscription=bool(current_user.get("stripe_subscription_id")),
    )


@router.post("/checkout")
async def create_checkout_session(
    request: CheckoutRequest,
    current_user: dict = Depends(get_current_user_hybrid),
    db: Session = Depends(get_db),
):
    if not _stripe_configured():
        raise HTTPException(status_code=503, detail="Billing not configured")

    if request.tier not in ("pro", "enterprise"):
        raise HTTPException(status_code=422, detail="Invalid tier")

    price_id = (
        settings.stripe_price_pro_monthly
        if request.tier == "pro"
        else settings.stripe_price_enterprise_monthly
    )
    if not price_id:
        raise HTTPException(status_code=503, detail="Price not configured")

    try:
        customer_id = current_user.get("stripe_customer_id")
        if not customer_id:
            customer = stripe.Customer.create(email=current_user["email"])
            customer_id = customer.id
            user_row = (
                db.query(User)
                .filter(User.username == current_user["username"])
                .first()
            )
            if user_row:
                user_row.stripe_customer_id = customer_id
                db.commit()

        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=f"{settings.frontend_url}/app/settings?tab=billing&checkout=success",
            cancel_url=f"{settings.frontend_url}/app/settings?tab=billing&checkout=cancel",
        )
        return {"checkout_url": session.url}
    except stripe.StripeError as e:
        logger.error("Stripe checkout error: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.post("/portal")
async def create_portal_session(
    current_user: dict = Depends(get_current_user_hybrid),
):
    if not _stripe_configured():
        raise HTTPException(status_code=503, detail="Billing not configured")

    customer_id = current_user.get("stripe_customer_id")
    if not customer_id:
        raise HTTPException(status_code=400, detail="No active subscription")

    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{settings.frontend_url}/app/settings?tab=billing",
        )
        return {"portal_url": session.url}
    except stripe.StripeError as e:
        logger.error("Stripe portal error: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create portal session")


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    if not _stripe_configured():
        raise HTTPException(status_code=503, detail="Billing not configured")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Redis-based idempotency — skip already-processed events
    from app.main import redis_client
    event_key = f"stripe:event:{event.id}"
    if redis_client:
        already = await redis_client.set(event_key, "1", ex=86400, nx=True)
        if not already:
            logger.info("Skipping duplicate webhook event: %s", event.id)
            return {"status": "already_processed"}

    logger.info("Processing Stripe webhook: type=%s id=%s", event.type, event.id)

    if event.type == "checkout.session.completed":
        session_obj = event.data.object
        customer_id = session_obj.customer
        subscription_id = session_obj.subscription

        user_row = (
            db.query(User).filter(User.stripe_customer_id == customer_id).first()
        )
        if not user_row:
            logger.error(
                "Stripe checkout completed but no user found for customer %s",
                customer_id,
            )
            return {"status": "ok"}

        # Determine tier by price_id (not amount — future-proof)
        tier = "pro"
        if subscription_id:
            try:
                sub = stripe.Subscription.retrieve(subscription_id)
                price_id = sub["items"]["data"][0]["price"]["id"]
                tier = _get_price_to_tier().get(price_id, "pro")
            except Exception as e:
                logger.warning("Could not resolve tier from subscription: %s", e)

        user_row.subscription_tier = tier
        user_row.stripe_subscription_id = subscription_id
        user_row.query_count_this_period = 0
        db.commit()
        logger.info("User %s upgraded to %s", user_row.username, tier)

    elif event.type == "customer.subscription.updated":
        sub = event.data.object
        customer_id = sub.customer
        user_row = (
            db.query(User).filter(User.stripe_customer_id == customer_id).first()
        )
        if user_row:
            price_id = sub["items"]["data"][0]["price"]["id"]
            new_tier = _get_price_to_tier().get(price_id, user_row.subscription_tier)
            if new_tier != user_row.subscription_tier:
                logger.info(
                    "User %s tier changed: %s -> %s",
                    user_row.username, user_row.subscription_tier, new_tier,
                )
                user_row.subscription_tier = new_tier
                db.commit()

    elif event.type == "invoice.payment_succeeded":
        invoice = event.data.object
        customer_id = invoice.customer
        user_row = (
            db.query(User).filter(User.stripe_customer_id == customer_id).first()
        )
        if user_row:
            user_row.query_count_this_period = 0
            user_row.billing_period_start = datetime.now(timezone.utc)
            db.commit()

    elif event.type == "customer.subscription.deleted":
        sub = event.data.object
        customer_id = sub.customer
        user_row = (
            db.query(User).filter(User.stripe_customer_id == customer_id).first()
        )
        if user_row:
            user_row.subscription_tier = "free"
            user_row.stripe_subscription_id = None
            db.commit()
            logger.info("User %s downgraded to free (subscription cancelled)", user_row.username)

    elif event.type == "invoice.payment_failed":
        invoice = event.data.object
        customer_id = invoice.customer
        logger.warning(
            "Payment failed for customer %s, attempt %s",
            customer_id, invoice.get("attempt_count", "?"),
        )

    else:
        logger.debug("Unhandled Stripe event type: %s", event.type)

    return {"status": "ok"}
