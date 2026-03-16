"""Stripe billing routes — Checkout session creation and webhook handling.

Endpoints:
  POST /api/stripe/create-checkout-session  — create a Stripe Checkout session
  POST /api/stripe/webhook                  — handle Stripe webhook events

Environment variables required:
  STRIPE_SECRET_KEY       — Stripe secret key (sk_live_... or sk_test_...)
  STRIPE_PRICE_ID         — recurring price ID (price_...)
  STRIPE_WEBHOOK_SECRET   — webhook signing secret (whsec_...)
"""

from __future__ import annotations

import os

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from backend.auth import get_admin_client, get_current_user

router = APIRouter()

# Stripe is configured once at import time from environment variables.
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "")
_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# URLs Stripe redirects the user to after checkout.
_SUCCESS_URL = os.getenv("APP_URL", "https://soloact.app") + "/dashboard?upgraded=1"
_CANCEL_URL  = os.getenv("APP_URL", "https://soloact.app") + "/dashboard"


@router.post("/api/stripe/create-checkout-session")
async def create_checkout_session(user=Depends(get_current_user)) -> dict:
    """Create a Stripe Checkout session for the authenticated user.

    Looks up or creates a Stripe customer tied to the user's Supabase ID,
    then returns a hosted Checkout URL for the monthly subscription.
    """
    client = get_admin_client()

    # Fetch or create the Stripe customer ID stored in the user's profile.
    profile_res = client.table("profiles").select("stripe_customer_id").eq("id", str(user.id)).single().execute()
    profile = profile_res.data or {}
    customer_id: str | None = profile.get("stripe_customer_id")

    if not customer_id:
        customer = stripe.Customer.create(
            email=user.email,
            metadata={"supabase_user_id": str(user.id)},
        )
        customer_id = customer.id
        client.table("profiles").update({"stripe_customer_id": customer_id}).eq("id", str(user.id)).execute()

    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{"price": _PRICE_ID, "quantity": 1}],
        mode="subscription",
        subscription_data={"trial_period_days": 7},
        success_url=_SUCCESS_URL,
        cancel_url=_CANCEL_URL,
    )

    return {"url": session.url}


@router.post("/api/stripe/webhook")
async def stripe_webhook(request: Request) -> JSONResponse:
    """Handle incoming Stripe webhook events.

    Verifies the Stripe signature, then processes:
      - checkout.session.completed        → mark user as paid
      - customer.subscription.deleted     → revert user to free
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, _WEBHOOK_SECRET)
    except stripe.errors.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature.")

    client = get_admin_client()

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        customer_id = session.get("customer")
        subscription_id = session.get("subscription")
        if customer_id:
            client.table("profiles").update({
                "plan": "paid",
                "stripe_subscription_id": subscription_id,
            }).eq("stripe_customer_id", customer_id).execute()

    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        customer_id = subscription.get("customer")
        if customer_id:
            client.table("profiles").update({
                "plan": "free",
                "stripe_subscription_id": None,
            }).eq("stripe_customer_id", customer_id).execute()

    return JSONResponse(content={"received": True})
