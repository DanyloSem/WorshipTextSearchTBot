from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
import app.keyboards as kb

router = Router()

# Відповідь по конкретній команді(/start) 
@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.reply(f'Привіт {message.from_user.first_name}!\nТвій ID: {message.from_user.id}',
                        reply_markup=await kb.inline_cars())

# Відповідь по очікуваній команді(/help)
@router.message(Command('help'))
async def get_help(message:Message):
    await message.answer('Це команда Хелп.')

# Відповідь по очікуваній фразі(str)
@router.message(F.text == 'Слава Ісусу!')
async def glory_to_God(message:Message):
    await message.answer('Навіки Слава!!!')

# Відповідь на отримане зоображення
@router.message(F.photo)
async def get_photo(message:Message):
    await message.answer(f'ID фотографії: {message.photo[-1].file_id}')

# Відправити користувачеві зоображення, яке вже загружене на сервера ТГ. 
# Відправка по ID або по посиланню на онлайн ресурс.
@router.message(Command('give_photo'))
async def give_photo(message:Message):
    await message.answer_photo(photo='AgACAgIAAxkBAAMRZmTQLMQLHn3kqWb_hONk6Niqf9IAAubXMRtEtilLvcAWHxLSzPEBAAMCAAN5AAM1BA', 
                               caption='Це таблиця Варкрафт 3.')