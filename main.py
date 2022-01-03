import asyncio

from aiogram import Bot, Dispatcher, executor, types
from config import TOKEN
from database import Database
from site import StopGame

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

db = Database('db.db')
sg = StopGame('site.py')


# Подписаться
@dp.message_handlers(commands=['subscribe'])
async def subscribe(message: types.Message):
    if not db.subscriber_exists(message.from_user.id):
        db.add_subscriber(message.from_user.id)
    else:
        db.update_subscription(message.from_user.id, True)
    await message.answer('Вы подписались на рассылку!')


@dp.message_handlers(commands=['unsubscribe'])
async def unsubscribe(message: types.Message):
    if not db.subscriber_exists(message.from_user.id):
        db.add_subscriber(message.from_user.id, False)
        await message.answer('Отмена подписки, которой и так у вас не было :)')
    else:
        db.update_subscription(message.from_user.id, False)
        await message.answer('Вы отменили подписку :(')


# проверяем наличие новых игр и делаем рассылки
async def scheduled(wait_for):
    while True:
        await asyncio.sleep(wait_for)

        # проверяем наличие новых игр
        new_games = sg.new_games()

        if (new_games):
            # если игры есть, переворачиваем список и итерируем
            new_games.reverse()
            for ng in new_games:
                # парсим инфу о новой игре
                nfo = sg.game_info(ng)

                # получаем список подписчиков бота
                subscriptions = db.get_subscriptions()

                # отправляем всем новость
                with open(sg.download_image(nfo['image']), 'rb') as photo:
                    for s in subscriptions:
                        await bot.send_photo(
                            s[1],
                            photo,
                            caption=nfo['title'] + "\n" + "Оценка: " + nfo['score'] + "\n" + nfo['excerpt'] + "\n\n" +
                                    nfo['link'],
                            disable_notification=True
                        )

                # обновляем ключ
                sg.update_lastkey(nfo['id'])


if __name__ == '__main__':
    dp.loop.create_task(scheduled(10))  # оставим 10 секунд (в качестве теста)
    executor.start_polling(dp, skip_updates=True)
