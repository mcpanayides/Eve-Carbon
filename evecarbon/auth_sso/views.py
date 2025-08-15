import base64
import json
import time
import urllib.parse

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.models import User
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from .models import Alliance
from jwt import PyJWKClient, decode as jwt_decode, InvalidTokenError

# Pull secrets + allowlists from your secrets.py
from evecarbon.secrets import (
    client_id,
    client_secret,
    callback_url,
    EVE_ALLOWED_ALLIANCE_IDS,
    EVE_ALLOWED_CORPORATION_IDS,
    EVE_CHARACTER_ACL,
)

SSO_AUTHORIZE = "https://login.eveonline.com/v2/oauth/authorize"
SSO_TOKEN = "https://login.eveonline.com/v2/oauth/token"
SSO_JWKS = "https://login.eveonline.com/.well-known/jwks.json"
ESI_BASE = "https://esi.evetech.net"

#landing page view
def landing(request):
    # Render your landing page template
    return render(request, "auth_sso/landing.html")


# Minimal scope: "publicData" is enough to get an access token + character identity.
# If you later need corp director things, add scopes accordingly.
EVE_SCOPES = ["publicData"]  # space-separated below

def eve_login(request):
    # CSRF-style state we can validate on callback
    state = base64.urlsafe_b64encode(os.urandom(24)).decode("utf-8").rstrip("=")
    request.session["eve_oauth_state"] = state

    params = {
        "response_type": "code",
        "redirect_uri": callback_url,
        "client_id": client_id,
        "scope": " ".join(EVE_SCOPES),
        "state": state,
    }
    return redirect(f"{SSO_AUTHORIZE}?{urllib.parse.urlencode(params)}")

def _exchange_code_for_token(code: str) -> dict:
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "login.eveonline.com",
    }
    data = {"grant_type": "authorization_code", "code": code}
    resp = requests.post(SSO_TOKEN, data=data, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json()  # includes access_token (JWT), token_type, expires_in, refresh_token
    # See CCP note to use v2 endpoints + JWT. :contentReference[oaicite:3]{index=3}

def _validate_jwt(access_token: str) -> dict:
    # Validate signature and claims with CCP JWKS
    # CCP recommends verifying issuer, audience, expiration. :contentReference[oaicite:4]{index=4}
    jwk_client = PyJWKClient(SSO_JWKS)
    signing_key = jwk_client.get_signing_key_from_jwt(access_token)
    claims = jwt_decode(
        access_token,
        signing_key.key,
        algorithms=["RS256"],
        audience=client_id,
        options={"require": ["exp", "iss", "sub"]},
    )
    # Typical 'sub' looks like "CHARACTER:EVE:123456789"
    return claims

def _extract_character_id(claims: dict) -> int:
    sub = claims.get("sub", "")
    # Format: CHARACTER:EVE:<id>
    try:
        return int(sub.split(":")[-1])
    except Exception:
        raise InvalidTokenError("Invalid subject format in access token")

def _fetch_affiliation(character_id: int) -> tuple[int | None, int | None]:
    # Public ESI; no auth required
    # POST /v2/characters/affiliation/ returns corp/alliance IDs for a list of chars. :contentReference[oaicite:5]{index=5}
    url = f"{ESI_BASE}/v2/characters/affiliation/"
    resp = requests.post(url, json=[character_id], timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if not data:
        return None, None
    entry = data[0]
    return entry.get("corporation_id"), entry.get("alliance_id")

def _is_authorized(character_id: int, corporation_id: int | None, alliance_id: int | None) -> bool:
    if character_id in EVE_CHARACTER_ACL:
        return True
    if alliance_id:
        try:
            alliance = Alliance.objects.get(alliance_id=alliance_id)
            if alliance.blue:
                return True
        except Alliance.DoesNotExist:
            pass
    if corporation_id and corporation_id in EVE_ALLOWED_CORPORATION_IDS:
        return True
    return False

def _get_or_create_user(character_id: int, character_name: str, corporation_id, alliance_id):
    User = get_user_model()
    username = f"eve_{character_id}"
    user, created = User.objects.get_or_create(username=username, defaults={"first_name": character_name})
    if created:
        user.set_unusable_password()
        user.save()
    # ensure profile
    from .models import UserProfile
    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            "character_id": character_id,
            "character_name": character_name,
            "corporation_id": corporation_id,
            "alliance_id": alliance_id,
        },
    )
    # update on each login
    profile.character_name = character_name
    profile.corporation_id = corporation_id
    profile.alliance_id = alliance_id
    profile.save()
    return user

import os
def eve_callback(request):
    # Validate anti-forgery 'state'
    state = request.GET.get("state")
    code = request.GET.get("code")
    if not code or not state or state != request.session.get("eve_oauth_state"):
        return HttpResponseBadRequest("Invalid OAuth state")

    try:
        token_payload = _exchange_code_for_token(code)
        access_token = token_payload["access_token"]
        claims = _validate_jwt(access_token)
    except Exception as e:
        messages.error(request, f"SSO Error: {e}")
        return redirect("/")

    character_id = _extract_character_id(claims)
    character_name = claims.get("name") or claims.get("preferred_username") or "Unknown Capsuleer"

    # Determine corp/alliance now
    corp_id, alliance_id = _fetch_affiliation(character_id)

    if not _is_authorized(character_id, corp_id, alliance_id):
        # show a nice "unauthorized" page
        ctx = {
            "character_name": character_name,
            "character_id": character_id,
            "corp_id": corp_id,
            "alliance_id": alliance_id,
        }
        return render(request, "auth_sso/unauthorized.html", ctx, status=403)

    # Create/login the Django user
    user = _get_or_create_user(character_id, character_name, corp_id, alliance_id)
    login(request, user)
    # Send to dashboard or wherever makes sense
    return redirect("/")

def logout_view(request):
    logout(request)
    return redirect("/")
