import unittest
from datetime import datetime, timezone, timedelta
import jwt

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES,
    ACCESS_TOKEN_TYPE,
)

# Test-only secret key (strictly isolated from any production or environment secret)
TEST_SECRET_KEY = "test_only_mock_jwt_signing_secret_key_32bytes_len!"


class TestSecurity(unittest.TestCase):

    def test_password_hashing_differs_from_original(self):
        # 1. Password hashing returns a hash different from the original password
        plain = "SuperSecretPassword123!"
        hashed = hash_password(plain)
        self.assertNotEqual(plain, hashed)
        self.assertTrue(hashed.startswith("$argon2id$"))

    def test_correct_password_verification_succeeds(self):
        # 2. Correct password verification succeeds
        plain = "CorrectHorseBatteryStaple"
        hashed = hash_password(plain)
        self.assertTrue(verify_password(plain, hashed))

    def test_incorrect_password_verification_fails(self):
        # 3. Incorrect password verification fails
        plain = "Password123"
        hashed = hash_password(plain)
        self.assertFalse(verify_password("WrongPassword123", hashed))

    def test_two_hashes_of_same_password_are_independently_salted(self):
        # 4. Two hashes of the same password are independently salted
        plain = "SamePasswordAcrossUsers"
        hash1 = hash_password(plain)
        hash2 = hash_password(plain)
        self.assertNotEqual(hash1, hash2)
        self.assertTrue(verify_password(plain, hash1))
        self.assertTrue(verify_password(plain, hash2))

    def test_malformed_hash_verification_fails_safely(self):
        # 5. Malformed hash verification fails safely without unhandled exceptions
        plain = "MyPassword"
        malformed_hashes = [
            "not_an_argon_hash",
            "$argon2id$v=19$m=65536,t=3,p=4$corrupted_base64_salt$corrupted_hash",
            "",
            "12345",
            "$invalid$hash$format",
            None,
        ]
        for bad_hash in malformed_hashes:
            self.assertFalse(verify_password(plain, bad_hash))

    def test_valid_jwt_creation_and_decoding(self):
        # 6. Valid JWT creation and decoding
        user_id = "user_abc_123"
        token = create_access_token(subject=user_id, secret_key=TEST_SECRET_KEY)
        self.assertIsInstance(token, str)

        payload = decode_access_token(token=token, secret_key=TEST_SECRET_KEY)
        self.assertEqual(payload["sub"], user_id)
        self.assertEqual(payload["type"], ACCESS_TOKEN_TYPE)
        self.assertIn("iat", payload)
        self.assertIn("exp", payload)

    def test_jwt_contains_expected_subject_and_type(self):
        # 7. JWT contains the expected subject and access-token type
        subject = "550e8400-e29b-41d4-a716-446655440000"
        token = create_access_token(subject=subject, secret_key=TEST_SECRET_KEY)
        payload = decode_access_token(token=token, secret_key=TEST_SECRET_KEY)
        self.assertEqual(payload["sub"], subject)
        self.assertEqual(payload["type"], "access")

    def test_jwt_expires_after_configured_lifetime(self):
        # 8. JWT expires after its configured lifetime
        subject = "user_lifetime_test"
        # Test default expiration is approximately 60 minutes
        token_default = create_access_token(subject=subject, secret_key=TEST_SECRET_KEY)
        payload_default = decode_access_token(token_default, TEST_SECRET_KEY)
        lifespan_seconds = payload_default["exp"] - payload_default["iat"]
        self.assertEqual(lifespan_seconds, DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES * 60)

        # Test custom explicit expiration (e.g. 15 minutes)
        custom_delta = timedelta(minutes=15)
        token_custom = create_access_token(
            subject=subject, secret_key=TEST_SECRET_KEY, expires_delta=custom_delta
        )
        payload_custom = decode_access_token(token_custom, TEST_SECRET_KEY)
        custom_lifespan = payload_custom["exp"] - payload_custom["iat"]
        self.assertEqual(custom_lifespan, 15 * 60)

    def test_expired_jwt_is_rejected(self):
        # 9. Expired JWT is rejected
        subject = "expired_user"
        expired_token = create_access_token(
            subject=subject,
            secret_key=TEST_SECRET_KEY,
            expires_delta=timedelta(seconds=-10),  # expired 10 seconds ago
        )
        with self.assertRaises(jwt.ExpiredSignatureError):
            decode_access_token(expired_token, TEST_SECRET_KEY)

    def test_tampered_signature_is_rejected(self):
        # 10. Tampered signature is rejected
        token = create_access_token(subject="user_tamper", secret_key=TEST_SECRET_KEY)
        # Modify the last characters of the token
        tampered_token = token[:-5] + ("AAAAA" if token[-5:] != "AAAAA" else "BBBBB")
        with self.assertRaises(jwt.InvalidSignatureError):
            decode_access_token(tampered_token, TEST_SECRET_KEY)

        # Also test signing with different secret fails
        with self.assertRaises(jwt.InvalidSignatureError):
            decode_access_token(token, "wrong_unauthorized_secret_key_1234567")

    def test_missing_subject_is_rejected(self):
        # 11. Missing subject is rejected
        now = datetime.now(timezone.utc)
        payload_without_sub = {
            "iat": now,
            "exp": now + timedelta(minutes=60),
            "type": ACCESS_TOKEN_TYPE,
        }
        token_no_sub = jwt.encode(payload_without_sub, TEST_SECRET_KEY, algorithm="HS256")
        with self.assertRaises(jwt.InvalidTokenError):
            decode_access_token(token_no_sub, TEST_SECRET_KEY)

        # Empty subject string should also be rejected
        payload_empty_sub = {
            "sub": "   ",
            "iat": now,
            "exp": now + timedelta(minutes=60),
            "type": ACCESS_TOKEN_TYPE,
        }
        token_empty_sub = jwt.encode(payload_empty_sub, TEST_SECRET_KEY, algorithm="HS256")
        with self.assertRaises(jwt.InvalidTokenError):
            decode_access_token(token_empty_sub, TEST_SECRET_KEY)

    def test_incorrect_token_type_is_rejected(self):
        # 12. Incorrect token type is rejected
        now = datetime.now(timezone.utc)
        payload_refresh = {
            "sub": "user_id_refresh",
            "iat": now,
            "exp": now + timedelta(minutes=60),
            "type": "refresh_token",  # Incorrect type
        }
        token_refresh = jwt.encode(payload_refresh, TEST_SECRET_KEY, algorithm="HS256")
        with self.assertRaises(jwt.InvalidTokenError):
            decode_access_token(token_refresh, TEST_SECRET_KEY)

    def test_malformed_jwt_is_rejected(self):
        # 13. Malformed JWT is rejected
        malformed_tokens = [
            "this.is.not.a.valid.jwt",
            "gibberish",
            "a.b",
            "",
            None,
        ]
        for bad_token in malformed_tokens:
            with self.assertRaises(jwt.DecodeError):
                decode_access_token(bad_token, TEST_SECRET_KEY)


if __name__ == "__main__":
    unittest.main()

