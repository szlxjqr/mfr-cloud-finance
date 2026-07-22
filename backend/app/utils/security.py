"""安全工具：密码哈希（PBKDF2）与自签名 Token（HMAC-SHA256）。

不依赖任何第三方加密库，全部使用 Python 标准库，保证小系统零额外风险。
Token 采用与 JWT 兼容的 header.payload.signature 三段结构，仅用 HMAC 自签名。
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time

# 签名密钥：生产环境务必通过环境变量 AUTH_SECRET 覆盖。
_AUTH_SECRET = os.getenv("AUTH_SECRET", "mfr-cloud-finance-default-secret-change-me")
_PBKDF2_ITER = 100_000


# ============ 密码哈希 ============
def hash_password(password: str) -> str:
    """返回格式：pbkdf2_sha256$iterations$salt$hash(hex)。"""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), _PBKDF2_ITER)
    return f"pbkdf2_sha256${_PBKDF2_ITER}${salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """恒定时间比较，防止时序侧信道。"""
    try:
        algo, iter_s, salt, expected = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), int(iter_s))
        return secrets.compare_digest(dk.hex(), expected)
    except Exception:
        return False


# ============ Token 生成 / 校验 ============
def _b64url_encode(obj) -> str:
    raw = base64.urlsafe_b64encode(json.dumps(obj, separators=(",", ":")).encode("utf-8"))
    return raw.decode("ascii").rstrip("=")


def _b64url_decode(s: str):
    pad = "=" * (-len(s) % 4)
    return json.loads(base64.urlsafe_b64decode((s + pad).encode("ascii")))


def generate_token(username: str, role: str, employee_no: str, expire_hours: int = 24 * 30) -> str:
    """生成自签名 Token，默认 30 天有效。"""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": username,
        "role": role,
        "emp": employee_no,
        "exp": int(time.time()) + expire_hours * 3600,
    }
    h = _b64url_encode(header)
    p = _b64url_encode(payload)
    sig = hmac.new(_AUTH_SECRET.encode("utf-8"), f"{h}.{p}".encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{h}.{p}.{sig}"


def verify_token(token: str) -> dict | None:
    """校验签名与有效期，成功返回 payload，失败返回 None。"""
    try:
        h, p, sig = token.split(".")
        expected = hmac.new(_AUTH_SECRET.encode("utf-8"), f"{h}.{p}".encode("utf-8"), hashlib.sha256).hexdigest()
        if not secrets.compare_digest(expected, sig):
            return None
        payload = _b64url_decode(p)
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None
