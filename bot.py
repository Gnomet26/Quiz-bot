import asyncio
import logging
import sys
import os
import pandas as pd
from datetime import datetime
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.enums import ParseMode
from aiogram.types import Message, PollAnswer, FSInputFile
from aiogram.filters import Command, CommandStart
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.dispatcher.event.bases import SkipHandler
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
from archive_model import Archive, Base as ArchiveBase
from db import SessionLocal, engine
from player_model import Player, Base
from generate import Generate
from secret import token, admin_id
from upload import upload_file, all_errors
from asyncio import create_task, sleep
from bot_global import delayed_stop_task

# --- Asosiy obyektlar ---
bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
router = Router()

random_questions = None
true_list = None
delayed_stop_task = None



@router.message(F.document)
async def upload_word_handler(message: types.Message):
    if str(message.from_user.id) not in str(admin_id):
        await message.answer("⛔ Siz fayl yuklay olmaysiz. Faqat admin!")
        return

    document = message.document
    if not document.file_name.endswith(".docx"):
        await message.answer("❗️Faqat .docx formatdagi faylni yuboring.")
        return

    file = await message.bot.get_file(document.file_id)
    file_path = f"temp/{document.file_name}"
    os.makedirs("temp", exist_ok=True)
    await message.bot.download_file(file.file_path, file_path)

    try:
        status = upload_file(file_path)      # testni yuklash
        error_list = all_errors()                # <-- FUNKSIYA chaqirilmoqda!

        if error_list:
            await message.answer("⚠️ Quyidagi xatoliklar yuz berdi:")
            for err in error_list:
                await message.answer(f"• {err}")
        
        await message.answer(f"✅ Test yuklandi: {status}")

    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {e}")
    finally:
        os.remove(file_path)




@router.message(Command("players"))
async def list_players(message: Message):
    if str(message.from_user.id) not in str(admin_id):
        await message.answer("⛔ Siz admin emassiz.")
        return

    session = SessionLocal()
    players = session.query(Player).all()
    total = len(players)

    if not players:
        await message.answer("👥 Hozircha hech kim ro'yxatdan o'tmagan.")
        session.close()
        return

    text = f"📋 Hozirgi ro'yxatdagi foydalanuvchilar (jami: {total} ta):\n\n"
    for idx, player in enumerate(players, start=1):
        text += f"{idx}. Ism: {player.first_name or '-'} | Familiya: {player.last_name or '-'} | ID: {player.telegram_id}\n"

    await message.answer(text)
    session.close()


@router.message(Command("quit"))
async def quit_command(message: Message):
    session = SessionLocal()
    telegram_id = message.chat.id

    player = session.query(Player).filter_by(telegram_id=telegram_id).first()

    if not player:
        await message.answer("❗️Siz ro'yxatda emassiz.")
        session.close()
        return

    if player.total_questions and player.total_questions > 0:
        await message.answer("❌ Test davomida ro'yxatdan chiqish mumkin emas.")
        session.close()
        return

    try:
        session.delete(player)
        session.commit()
        await message.answer("✅ Siz test ro'yxatidan muvaffaqiyatli chiqdingiz.")
    except Exception as e:
        session.rollback()
        await message.answer("❌ Chiqishda xatolik yuz berdi.")
        print(f"Delete xatolik: {e}")
    finally:
        session.close()


async def stop_test_logic(bot: Bot, admin_chat_id: int):
    # 1. Arxiv jadvali yaratiladi
    try:
        ArchiveBase.metadata.create_all(bind=engine)
    except SQLAlchemyError as e:
        await bot.send_message(admin_chat_id, "❌ Arxiv jadvalini yaratishda xatolik.")
        print(f"Arxiv jadval xatolik: {e}")
        return

    db = SessionLocal()
    players = db.query(Player).all()

    if not players:
        await bot.send_message(admin_chat_id, "❗Faol test mavjud emas.")
        db.close()
        return

    archive_data = []
    for player in players:
        if player.current_question < player.total_questions:
            player.current_question = player.total_questions

        try:
            await bot.send_message(
                chat_id=player.telegram_id,
                text=(
                    f"⏹ Test yakunlandi.\n"
                    f"✅ To‘g‘ri javoblar: {player.true_answers}\n"
                    f"❌ Noto‘g‘ri javoblar: {player.false_answers}\n"
                    f"Jami savollar: {player.total_questions}"
                )
            )
        except Exception as e:
            print(f"Xatolik {player.telegram_id} ga xabar yuborishda: {e}")

        archive = Archive(
            telegram_id=player.telegram_id,
            first_name=player.first_name,
            last_name=player.last_name,
            true_answers=player.true_answers,
            false_answers=player.false_answers,
            current_question=player.current_question,
            total_questions=player.total_questions,
            completed_at=datetime.now()
        )
        db.add(archive)

        archive_data.append({
            "telegram_id": player.telegram_id,
            "first_name": player.first_name,
            "last_name": player.last_name,
            "true_answers": player.true_answers,
            "false_answers": player.false_answers,
            "total_questions": player.total_questions,
            "completed_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    try:
        db.commit()
        db.query(Player).delete()
        db.commit()

        df = pd.DataFrame(archive_data)
        filename = f"test_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = f"./{filename}"
        df.to_excel(filepath, index=False)

        file = FSInputFile(filepath)
        await bot.send_document(
            chat_id=admin_chat_id,
            document=file,
            caption="📊 Test natijalari (Excel)"
        )

        await bot.send_message(admin_chat_id, "✅ Test to‘xtatildi, natijalar arxivga saqlandi va Excel yuborildi.")

        os.remove(filepath)

    except Exception as e:
        db.rollback()
        await bot.send_message(admin_chat_id, "❌ Xatolik: Arxivlash yoki Excel yaratishda xatolik.")
        print(f"Xatolik: {e}")
    finally:
        db.close()


@router.message(Command("stop_test"))
async def stop_test(message: types.Message):
    if str(message.from_user.id) not in str(admin_id):
        await message.answer("⛔ Siz admin emassiz.")
        return

    await stop_test_logic(bot=message.bot, admin_chat_id=message.from_user.id)




@dp.poll_answer()
async def handle_poll_answer(poll_answer: PollAnswer, state: FSMContext):
    user_id = poll_answer.user.id
    selected_option = poll_answer.option_ids[0]  # Foydalanuvchi tanlagan variant indeksi

    db = SessionLocal()
    player = db.query(Player).filter_by(telegram_id=user_id).first()

    if not player:
        db.close()
        raise SkipHandler("Foydalanuvchi topilmadi")

    # Holatdagi savollarni olish
    data = await state.get_data()
    random_questions = data.get("random_questions")
    true_list = data.get("true_list")
    current_q = data.get("current_question")
    total_q = data.get("total_questions")

    # To‘g‘ri variantni tekshirish
    current_question_obj = random_questions[current_q - 1]
    question_number = str(current_question_obj["number"])
    correct_index = int(true_list[question_number])

    if selected_option == correct_index:
        player.true_answers += 1
        player.false_answers -= 1

    else:
        player.true_answers -= 1
        player.false_answers += 1

    db.commit()

    # Keyingi savolga o‘tish yoki testni yakunlash
    if current_q < total_q:
        next_question_obj = random_questions[current_q]
        player.current_question += 1
        db.commit()

        await bot.send_poll(
            chat_id=user_id,
            question=next_question_obj["question"],
            options=next_question_obj["variants"],
            type="quiz",
            correct_option_id=int(true_list[str(next_question_obj["number"])]),
            is_anonymous=False,
            explanation="✅ Javob tekshirildi."
        )

        await state.update_data(current_question=current_q + 1)
    else:
        await bot.send_message(
            chat_id=user_id,
            text=f"✅ Test tugadi!\nTo‘g‘ri javoblar: {player.true_answers}\nNoto‘g‘ri javoblar: {player.false_answers}"
        )

    db.close()



# --- START komandasi ---
@router.message(CommandStart())
async def command_start_handler(message: Message):
    session = SessionLocal()
    telegram_id = message.chat.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    # 🧱 Jadval mavjudligini tekshirish
    inspector = inspect(session.bind)
    if "players" not in inspector.get_table_names():
        # Jadval mavjud bo‘lmasa yaratiladi
        Base.metadata.create_all(bind=session.bind)

    # 🔍 Foydalanuvchi mavjudligini tekshirish
    existing_player = session.query(Player).filter_by(telegram_id=telegram_id).first()

    if existing_player:
        await message.answer("❗️Siz allaqachon ro'yxatdan o'tgansiz.")
    else:
        new_player = Player(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            true_answers=0,
            false_answers=0,
            current_question=1,
            total_questions=0  # test boshlanganda yangilanadi
        )
        session.add(new_player)
        session.commit()
        await message.answer("✅ Ro'yxatdan muvaffaqiyatli o'tdingiz!")

    session.close()

# --- GO_TEST komandasi ---

@router.message(Command("go_test"))
async def go_test(message: Message, state: FSMContext):
    global delayed_stop_task

    if str(message.from_user.id) not in str(admin_id):
        await message.reply("⛔ Siz admin emassiz.")
        return

    try:
        # 📥 Format: /go_test n=5 t=1
        parts = message.text.split()
        n, t = None, 0

        for part in parts[1:]:
            if part.startswith("n="):
                n = int(part[2:])
            elif part.startswith("t="):
                t = int(part[2:])

        if n is None:
            raise ValueError

        # 🧠 Savollarni generatsiya qilamiz
        generator = Generate(n)
        random_questions = generator.new_question()
        true_list = generator.true_list()

        await state.update_data(
            random_questions=random_questions,
            true_list=true_list,
            current_question=1,
            total_questions=n
        )

        db = SessionLocal()
        players = db.query(Player).all()

        if not players:
            await message.reply("❗ Foydalanuvchilar ro'yxati bo'sh.")
            return

        for player in players:
            try:
                player.total_questions = n
                player.false_answers = n
                player.true_answers = 0
                db.commit()

                # 🕰 Tugash vaqti xabari (agar t > 0 bo‘lsa)
                time_note = f"\n⏱ Test {t} daqiqada avtomatik yakunlanadi." if t > 0 else ""

                await bot.send_message(
                    chat_id=player.telegram_id,
                    text=f"🧠 Test boshlandi!\nJami savollar soni: {n}{time_note}"
                )

                q = random_questions[0]
                question = q["question"]
                options = q["variants"]
                correct_option_id = int(true_list[str(q["number"])])

                await bot.send_poll(
                    chat_id=player.telegram_id,
                    question=question,
                    options=options,
                    type="quiz",
                    correct_option_id=correct_option_id,
                    is_anonymous=False,
                    explanation="✅ Javob tekshirildi."
                )

            except Exception as e:
                print(f"Xatolik {player.telegram_id} ga yuborishda: {e}")

        db.close()

        # ⏳ T daqiqa belgilangan bo‘lsa — avtomatik yakun
        if t > 0:
            await message.reply(f"⏳ Test avtomatik ravishda {t} daqiqadan so‘ng tugatiladi.")

            # ⛔ Oldingi sleep ni to‘xtatamiz (agar mavjud bo‘lsa)
            if delayed_stop_task and not delayed_stop_task.done():
                delayed_stop_task.cancel()

            async def delayed_stop():
                try:
                    await sleep(t * 60)
                    await stop_test_logic(bot=bot, admin_chat_id=message.from_user.id)
                except asyncio.CancelledError:
                    print("⏹ Avtomatik test tugatish bekor qilindi.")

            delayed_stop_task = create_task(delayed_stop())

        else:
            await message.reply("⏳ Test davomiyligi cheklanmagan.")

    except ValueError:
        await message.reply("❌ Format noto‘g‘ri. To‘g‘ri format: /go_test n=5 t=1")

# --- ASOSIY MAIN() ---
async def main():
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())