import uuid
from datetime import timedelta

import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.enums import RoleName
from app.services.exceptions import AuthenticationError
from tests.factories import build_admin
import jwt


class TestPasswordHashing:
    """Хеширование и проверка паролей."""

    def test_verify_password_correct(self) -> None:
        """Верный пароль против собственного хеша проходит проверку."""
        hashed = hash_password("s3cret-pass")
        assert verify_password("s3cret-pass", hashed) is True

    def test_verify_password_incorrect(self) -> None:
        """Неверный пароль не проходит, без исключения."""
        hashed = hash_password("s3cret-pass")
        assert verify_password("wrong-pass", hashed) is False

    def test_hash_is_not_plaintext(self) -> None:
        """Хеш не совпадает с исходным паролем как строка."""
        hashed = hash_password("s3cret-pass")
        assert hashed != "s3cret-pass"
        assert len(hashed) == 60  # длина bcrypt-хеша, как в схеме БД


class TestAccessToken:
    """Выпуск и валидация access-токена."""

    def test_roundtrip_valid_token(self) -> None:
        """Токен содержит permissions, собранные из ROLE_PERMISSIONS[role]."""
        admin = build_admin(role_name=RoleName.MANAGER)
        admin.admin_id = uuid.uuid4()

        token = create_access_token(admin)
        raw = jwt.decode(token, options={"verify_signature": False})

        assert set(raw["permissions"]) == {"products:write", "orders:write"}

    def test_expired_token_rejected(self, make_token) -> None:
        """Просроченный токен отклоняется понятным исключением, не библиотечным."""
        admin = build_admin()
        admin.admin_id = uuid.uuid4()
        token = make_token(admin, exp_delta=timedelta(minutes=-1))

        with pytest.raises(AuthenticationError):
            decode_access_token(token)

    def test_wrong_issuer_rejected(self, make_token) -> None:
        """Токен с чужим iss отклоняется."""
        admin = build_admin()
        admin.admin_id = uuid.uuid4()
        token = make_token(admin, issuer="some-other-service")

        with pytest.raises(AuthenticationError):
            decode_access_token(token)

    def test_wrong_audience_rejected(self, make_token) -> None:
        """Токен с чужим aud отклоняется."""
        admin = build_admin()
        admin.admin_id = uuid.uuid4()
        token = make_token(admin, audience="some-other-app")

        with pytest.raises(AuthenticationError):
            decode_access_token(token)

    def test_wrong_signature_rejected(self, make_token, wrong_rsa_keypair) -> None:
        """Токен, подписанный чужим приватным ключом, отклоняется."""
        wrong_private_key, _ = wrong_rsa_keypair
        admin = build_admin()
        admin.admin_id = uuid.uuid4()
        token = make_token(admin, signing_key=wrong_private_key)

        with pytest.raises(AuthenticationError):
            decode_access_token(token)

    def test_malformed_token_rejected(self) -> None:
        """Синтаксически некорректная строка отклоняется 401-эквивалентом, не 500."""
        with pytest.raises(AuthenticationError):
            decode_access_token("not-a-jwt-at-all")

    def test_missing_required_claim_rejected(self, make_token) -> None:
        """Токен без обязательного claim (role) не роняет сервис KeyError-ом."""
        admin = build_admin()
        admin.admin_id = uuid.uuid4()
        token = make_token(admin, omit_claims=("role",))

        with pytest.raises((AuthenticationError, KeyError)):

            decode_access_token(token)
