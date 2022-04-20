import uuid

from models import Code


def generate_user_codes(user):
    codes = []
    for _ in range(10):
        code_str = str(uuid.uuid4()).upper().replace("-", "")[:10]
        code = Code(
            {
                "code": code_str,
            }
        )
        codes.append(code_str)
        user.code.append(code)
    return user, codes
