# ~/clientfactory/src/clientfactory/auths/dpop.py
"""
DPoP Authentication
------------------
DPoP (Demonstration of Proof-of-Possession) authentication for ClientFactory.
"""
from __future__ import annotations
import uuid, base64, typing as t
from datetime import datetime, timezone

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa

from clientfactory.core.bases import BaseAuth
from clientfactory.core.models import RequestModel

class DPOPAuth(BaseAuth):
    """
    DPoP (Demonstration of Proof-of-Possession) authentication.

    Generates cryptographic proof tokens for each request using JWK keys.
    """
    __declaredas__: str = 'dpop'
    __declattrs__: set[str] = BaseAuth.__declattrs__ | {'jwk', 'algorithm', 'headerkey'}

    def _resolveattributes(self, attributes: dict) -> None:
        self.jwk: dict = attributes.get('jwk', {}) or {}
        self.algorithm: str = attributes.get('algorithm', 'ES256') or 'ES256'
        self.headerkey: str = attributes.get('headerkey', 'DPoP') or 'DPoP'
        if self.jwk:
            self._validatejwk()

    def _authenticate(self) -> bool:
        """DPoP is authenticated if valid JWK"""
        return bool(self.jwk)

    def _applyauth(self, request: RequestModel) -> RequestModel:
        """Apply DPoP token to request header"""
        token = self._generatetoken(request)
        return request.withheaders({self.headerkey: token})

    def _validatejwk(self) -> None:
        """Validate JWK has required fields"""
        if not self.jwk:
            return
        kty = self.jwk.get('kty')
        if not kty:
            raise ValueError("JWK missing 'kty' field")

        if (kty.upper() == 'EC'):
            required = {'crv', 'x', 'y', 'd'}
            missing = required - set(self.jwk.keys())
            if missing:
                raise ValueError(f"EC JWK missing fields: {missing}")
        elif (kty.upper() == 'RSA'):
            required = {'n', 'e', 'd'}
            missing = required - set(self.jwk.keys())
            if missing:
                raise ValueError(f"RSA JWK missing fields: {missing}")
        else:
            raise ValueError(f"Unsupported JWK type: {kty}")

        self._authenticated = True

    def _getprivatekey(self) -> ec.EllipticCurvePrivateKey:
        """Extract private key from JWK"""
        kty = self.jwk.get('kty', '').upper()

        if (kty == 'EC'):
            dbytes = base64.urlsafe_b64decode(
                self.jwk['d'] + '=' * (4 - len(self.jwk['d']) % 4)
            )
            private = int.from_bytes(dbytes, 'big')
            crv = self.jwk.get('crv', 'P-256')
            match crv:
                case 'P-256':
                    curve = ec.SECP256R1()
                case 'P-384':
                    curve = ec.SECP384R1()
                case 'P-521':
                    curve = ec.SECP521R1()
                case _:
                    raise ValueError(f"Unsupported curve: {crv}")
            return ec.derive_private_key(private, curve)
        else:
            raise NotImplementedError(f"Private key extraction not yet implemented for: {kty}")

    def _getpublicjwk(self) -> dict:
        """Get public portion of JWK for token header."""
        public = {k: self.jwk.get(k) for k in {'kty', 'crv', 'x', 'y'}}
        return {k: v for k,v in public.items() if v is not None}


    def _generatetoken(self, request: RequestModel) -> str:
        """Generate DPoP proof token for the specific request."""
        if not self.jwk:
            raise RuntimeError(f"No JWK configured")

        privatekey = self._getprivatekey()

        payload = {
            'jti': str(uuid.uuid4()),
            'htm': request.method.value,
            'htu': request.url,
            'iat': int(datetime.now(timezone.utc).timestamp())
        }

        header = {
            'typ': 'dpop+jwt',
            'alg': self.algorithm,
            'jwk': self._getpublicjwk()
        }

        return jwt.encode(payload, privatekey, algorithm=self.algorithm, headers=header)

    def setjwk(self, jwk: dict) -> None:
        """Set the JWK."""
        self.jwk = jwk
        self._validatejwk()
        self._authenticated = True
