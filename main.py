import asyncio
import datetime
import re

from aiogram import Bot, Dispatcher, executor, types
from loguru import logger
from passlib.hash import pbkdf2_sha256
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import func

from db import init_db
from models import Admin, Code, User, UserType
from settings import load_settings
from utils import generate_user_codes

settings = load_settings()

bot = Bot(token=settings["TOKEN_API"])
dp = Dispatcher(bot)


@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: types.Message):
    user_id = message.from_user["id"]
    logger.info(f"User {user_id}")
    s = select(User).where(User.id == user_id)
    async with db.begin() as session:
        user = (await session.execute(s)).scalar()
        if user:
            if user.user_type == UserType.ADMIN:
                await message.answer(
                    "▲ Бот пирамида ▲\n\n"
                    "Нажми:\n"
                    "/register чтобы получить информации о регистрации\n"
                    "/addcodes чтобы сгенерировать дополнительную пачку кодов (admin only)\n"
                    "/codes для отображения кодов-приглашений\n"
                    "/score чтобы увидеть количество приглашенных Вами участников"
                )
                return
        await message.answer(
            "▲ Бот пирамида ▲\n\n"
            "Нажми:\n"
            "/register чтобы получить информации о регистрации\n"
            "/codes для отображения кодов-приглашений\n"
            "/score чтобы увидеть количество приглашенных Вами участников"
        )


@dp.message_handler(commands=["score"])
async def score(message: types.Message):
    user_id = message.from_user["id"]
    logger.info(f"User {user_id}")
    count_query = select(func.count(User.id)).filter(User.invitor_id == user_id)
    async with db.begin() as session:
        count_result = (await session.execute(count_query)).scalar()
        logger.info(f"{user_id} invited {count_result}")
    await message.answer(f"Вы пригласили {count_result} участника(ов).")


@dp.message_handler(commands=["register"])
async def register_info(message: types.Message):
    user_id = message.from_user["id"]
    logger.info(f"User {user_id}")
    async with db.begin() as session:
        s = select(User.id).filter(User.id == user_id)
        user = (await session.execute(s)).fetchone()
        if not user:
            await message.answer(
                "Введите код-приглашение в формате:\n" "Код: 10-ти значный код"
            )
            return
        await message.answer("Вы уже зарегистрированы.")


@dp.message_handler(lambda message: message.text.startswith("Код: "))
async def register(message: types.Message):
    user_id = message.from_user["id"]
    logger.info(f"User {user_id}")
    try:
        code = re.search(r"\s*Код:\s*([\d\w]+)\s*", message.text).group(1)
    except AttributeError:
        await message.answer(
            "Введите код в корректном формате:\n" "Код: 10-ти значный код"
        )
        return

    async with db.begin() as session:
        hashed_admin_pass_query = select(Admin.admin_code)
        hashed_admin_pass_result = (
            await session.execute(hashed_admin_pass_query)
        ).fetchone()

        if not hasattr(hashed_admin_pass_result, "admin_code"):
            logger.warning(
                "Проверьте, что в таблице admin есть запись с хэшом админ пароля."
            )
        else:
            if pbkdf2_sha256.verify(code, hashed_admin_pass_result.admin_code):
                user_info = {
                    "user_id": user_id,
                    "user_type": UserType.ADMIN,
                    "invitor_id": None,
                }
                user_for_reg = User(user_info)
                user_for_reg, codes = generate_user_codes(user_for_reg)
                session.add(user_for_reg)
                await message.answer(
                    "Вы успешно зарегистрированы, как администратор!\n"
                    "{}\n{}".format(
                        "\n".join([f'{"-" * 21}\n`{code}`' for code in codes]), "-" * 21
                    ),
                    parse_mode="Markdown",
                )
                return
    async with db.begin() as session:
        s = select(User.id).filter(User.id == user_id)
        user = (await session.execute(s)).fetchone()
        if not user:
            if code:
                code_user_select = (
                    select(Code.code, User.id)
                    .select_from(User)
                    .filter(Code.code == code, Code.is_used == False)
                )
                code_result = (await session.execute(code_user_select)).fetchone()
                if code_result:
                    code_update = (
                        update(Code)
                        .filter(Code.code == code, Code.is_used == False)
                        .values(is_used=True, use_time=datetime.datetime.utcnow())
                    )
                    await session.execute(code_update)
            else:
                await message.answer(
                    "Убедитесь, что вы ввели корректный код-приглашение."
                )
                return
            user_info = {
                "user_id": user_id,
                "user_type": UserType.USER,
                "invitor_id": code_result.id,
            }
            user_for_reg = User(user_info)
        else:
            await message.answer("Вы уже зарегистрированы.")
            return
        user_for_reg, codes = generate_user_codes(user_for_reg)
        session.add(user_for_reg)
        logger.info(f"{user_id} registered")
    await message.answer(
        "Вы успешно зарегистрировались!\n\n"
        "Ваши коды для приглашения:\n"
        "{}\n{}".format(
            "\n".join([f'{"-" * 21}\n`{code}`' for code in codes]), "-" * 21
        ),
        parse_mode="markdown",
    )


@dp.message_handler(commands=["codes"])
async def get_codes(message: types.Message):
    user_id = message.from_user["id"]
    logger.info(f"User {user_id}")
    async with db.begin() as session:
        user_codes_select = (
            select(Code.code)
            .join(User)
            .filter(User.id == user_id, Code.is_used == False)
        )
        user_codes = (await session.execute(user_codes_select)).fetchall()
    if user_codes:
        await message.answer(
            "{}\n{}".format(
                "\n".join([f'{"-" * 21}\n`{code.code}`' for code in user_codes]),
                "-" * 21,
            ),
            parse_mode="Markdown",
        )
        return
    await message.answer("Сначала зарегистрируйтесь.\n\n" "/register")


@dp.message_handler(commands=["addcodes"])
async def add_chunk_codes(message: types.Message):
    user_id = message.from_user["id"]
    logger.info(f"User {user_id}")
    async with db.begin() as session:
        user_query = (
            select(User)
            .options(selectinload(User.code))
            .join(Code)
            .where(Code.user_relationship == user_id)
        )
        user = (await session.execute(user_query)).scalar()
        if user.user_type == UserType.ADMIN:
            user, codes = generate_user_codes(user)
            await message.answer(
                "{}\n{}".format(
                    "\n".join([f'{"-" * 21}\n`{code}`' for code in codes]), "-" * 21
                ),
                parse_mode="Markdown",
            )
            return


@dp.message_handler()
async def error_handler(message: types.Message):
    user_id = message.from_user["id"]
    logger.info(f"User {user_id}")
    await message.answer(
        "Введите код в корректном формате, если вы хотите зарегистрироваться\n\n"
        "Подробнее: /register"
    )


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    db = loop.run_until_complete(init_db())
    executor.start_polling(dp, skip_updates=True)
