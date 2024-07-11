import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.dispatcher import filters
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time


API_TOKEN = ''

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


def get_player_data(steam_id):
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 4)
    data = {}
    

    try:
        base_url_matches = f"https://csstats.gg/ru-RU/player/{steam_id}#/matches"
        driver.get(base_url_matches)
        time.sleep(1)

        avatar_element = driver.find_element(By.XPATH, "//div[@id='player-avatar']/img")
        avatar_url = avatar_element.get_attribute("src")
        data["avatar_url"] = avatar_url

        match_rows = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//tbody/tr[contains(@class, 'p-row js-link')]")))

        if match_rows:
            last_game_row = match_rows[0]
            date = last_game_row.find_element(By.XPATH, "./td[1]").text.strip()
            map_name = last_game_row.find_element(By.XPATH, "./td[3]").text.strip()
            result = last_game_row.find_element(By.XPATH, "./td[4]/span").text.strip()

            data["last_game"] = {
                "date": date,
                "map_name": map_name,
                "result": result
            }
        else:
            data["error"] = "На странице нет строк с матчами или элементы не были найдены."

        base_url_players = f"https://csstats.gg/ru-RU/player/{steam_id}?modes=Premier#/players"
        driver.get(base_url_players)
        time.sleep(4)
        rating = driver.find_element(By.XPATH, "//tr[@class='total-row']/td[last()]").text.strip()
        time.sleep(2)
        data["rating"] = rating

    except TimeoutException:
        data["error"] = "Не удалось найти строки с матчами. Возможно, данные не загрузились полностью или данные отсутствуют."

    except Exception as e:
        data["error"] = str(e)

    finally:
        driver.quit()
    
    return data


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Отправь мне Steam ID и я покажу тебе информацию о последнем матче и рейтинге игрока")


@dp.message_handler(filters.Regexp(r'^\d{17}$'))
async def handle_steam_id(message: types.Message):
    steam_id = message.text.strip()
    await message.reply(f"Ищу информацию для Steam ID: {steam_id}...")

    data = get_player_data(steam_id)
    
    if "error" in data:
        await message.reply(f"Произошла ошибка: {data['error']}")
    else:
        avatar_url = data.get("avatar_url", "N/A")
        last_game = data.get("last_game", {})
        rating = data.get("rating", "N/A")
        
        response = f"<b>Avatar URL:</b> <a href='{avatar_url}'>{avatar_url}</a>\n\n"
        response += "<b>Последняя сыгранная игра:</b>\n"
        response += f"Дата: {last_game.get('date', 'N/A')}\n"
        response += f"Карта: {last_game.get('map_name', 'N/A')}\n"
        response += f"Результат: {last_game.get('result', 'N/A')}\n\n"
        response += f"<b>Рейтинг в премьер режиме (актуальный):</b> {rating}"

        await message.reply(response, parse_mode=ParseMode.HTML)


@dp.message_handler()
async def invalid_steam_id(message: types.Message):
    await message.reply("Пожалуйста, отправьте правильный Steam ID, состоящий из 17 цифр")

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)