import requests
from bs4 import BeautifulSoup
import telebot
from telebot import types

TOKEN = '7039287159:AAHGA_F7irUaMPIvlGTiQyCPX47a5NhjeOU'
URL_BASE = 'https://animefire.plus/pesquisar/'
WEBHOOK_URL = 'https://mybottelegram.vercel.app/'  # Substitua pela sua URL pública
selected_anime = {}
bot = telebot.TeleBot(TOKEN)

# Configuração do Webhook
def set_webhook():
    webhook_url = WEBHOOK_URL + TOKEN  # A URL completa para o webhook inclui o token
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)

# Função para enviar botões de animes
def send_anime_buttons(chat_id, anime_list, start_index, show_back_button=False, show_next_button=False, message_id=None):
    markup = types.InlineKeyboardMarkup(row_width=1)
    if message_id:
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)

    for anime in anime_list[start_index:start_index+10]:
        button_data = anime['title'][:30]
        button = types.InlineKeyboardButton(anime['title'], callback_data=button_data)
        markup.add(button)

    if show_back_button:
        back_button = types.InlineKeyboardButton("Voltar à Lista", callback_data="back")
        markup.add(back_button)

    if show_next_button:
        next_button = types.InlineKeyboardButton("Próxima Lista", callback_data="next")
        markup.add(next_button)

    if message_id:
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Escolha um anime:", reply_markup=markup)
    else:
        bot.send_message(chat_id, "Escolha um anime:", reply_markup=markup)

# Função para adicionar botões de episódios
def add_episode_buttons(markup, episode_links):
    row = []
    for i, episode_link in enumerate(episode_links):
        button = types.InlineKeyboardButton(text=f"Episódio {i+1}", callback_data=f"episodio_{i}")
        row.append(button)
        if len(row) == 4:
            markup.add(*row)
            row = []
    if row:
        markup.add(*row)

@bot.message_handler(commands=['pes'])
def search_anime(message):
    anime_name = message.text[5:].lower()
    search_url = URL_BASE + anime_name
    response = requests.get(search_url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        item_elements = soup.select('.minWDanime')
        anime_list = []

        for item_element in item_elements:
            link = item_element.select("a")[0]['href']
            capa = item_element.select("img")[0]['data-src']
            titulo = item_element.select(".animeTitle")[0].text
            anime_list.append({'title': titulo, 'link': link, 'capa': capa})

        if anime_list:
            send_anime_buttons(message.chat.id, anime_list, 0, show_next_button=len(anime_list) > 10)
            selected_anime[message.chat.id] = {'list': anime_list, 'index': 0}
        else:
            bot.reply_to(message, "Nenhum anime encontrado com esse nome")
    else:
        bot.reply_to(message, "Erro ao realizar a pesquisa")

# Função de callback para manipular as interações de botões
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_chat_id = call.message.chat.id
    anime_data = selected_anime.get(user_chat_id)
    message_id = call.message.message_id

    if call.data == "mostrar_eps":
        if anime_data and 'anime_url' in anime_data:
            episode_links = extract_episode_links(anime_data['anime_url'])
            markup = types.InlineKeyboardMarkup()
            add_episode_buttons(markup, episode_links)
            bot.send_message(user_chat_id, "Escolha um episódio:", reply_markup=markup, reply_to_message_id=message_id)

    elif call.data.startswith("episodio_"):
        episode_index = int(call.data.split("_")[1])
        episode_links = extract_episode_links(anime_data['anime_url'])

        if episode_index < len(episode_links):
            episode_link = episode_links[episode_index]
            video_source = get_video_source(episode_link)
            if video_source:
                bot.send_message(user_chat_id, f"Link do Vídeo: {video_source}")
            else:
                bot.send_message(user_chat_id, f"Não foi possível encontrar o link do vídeo para o episódio: {episode_link}")

            bot.delete_message(chat_id=user_chat_id, message_id=message_id)
    else:
        if anime_data and 'list' in anime_data:
            for anime in anime_data['list']:
                if anime['title'][:30] == call.data:
                    send_anime_details(user_chat_id, anime['link'])
                    bot.delete_message(chat_id=user_chat_id, message_id=message_id)
                    break

# Função para extrair links de episódios
def extract_episode_links(anime_url):
    response = requests.get(anime_url)
    episode_links = []

    if response.status_code == 200:
        anime_soup = BeautifulSoup(response.content, 'html.parser')
        item_elements = anime_soup.select("div.div_video_list a.lEp")

        for item_element in item_elements:
            link = item_element['href']
            episode_links.append(link)

    return episode_links

# Função para obter a fonte de vídeo de um episódio
def get_video_source(episode_link):
    video_source = None
    episode_page_response = requests.get(episode_link)

    if episode_page_response.status_code == 200:
        episode_page_soup = BeautifulSoup(episode_page_response.content, 'html.parser')
        video_element = episode_page_soup.select_one("video#my-video")

        if video_element:
            video_source = video_element.get('data-video-src')

    return video_source

# Função para iniciar o Webhook
if __name__ == '__main__':
    set_webhook()  # Configura o webhook
