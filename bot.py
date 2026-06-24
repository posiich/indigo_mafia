import os
import random
import asyncio
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

MAFIA_GROUP_ID = -1003919230062
MAFIA_TOPIC_ID = 237

user_languages = {}
user_roles = {}
user_tasks_sent = set()
pending_photo_tasks = {}

ROLE_KEYS = ["mafia", "detective", "doctor", "maniac", "civilian"]
ROLE_WEIGHTS = [15, 15, 15, 10, 45]

ROLE_EMOJI = {
    "mafia": "🃏",
    "detective": "🔎",
    "doctor": "🚑",
    "maniac": "😈",
    "civilian": "🌻",
}

ROLE_NAMES = {
    "uk": {
        "mafia": "МАФІЯ",
        "detective": "ШЕРИФ",
        "doctor": "ЛІКАР",
        "maniac": "МАНІЯК",
        "civilian": "МИРНИЙ ЖИТЕЛЬ",
    },
    "bg": {
        "mafia": "МАФИЯ",
        "detective": "ШЕРИФ",
        "doctor": "ДОКТОР",
        "maniac": "МАНИАК",
        "civilian": "МИРЕН ЖИТЕЛ",
    },
    "en": {
        "mafia": "MAFIA",
        "detective": "SHERIFF",
        "doctor": "DOCTOR",
        "maniac": "MANIAC",
        "civilian": "CIVILIAN",
    },
}

TEXTS = {
    "uk": {
        "choose_language": "Choose your language / Обери мову / Избери език:",
        "role_button": "Дізнатися свою роль! 🎭",
        "tasks_button": "Отримати таємні завдання 📜",
        "send_photo": "📸 Надіслати",
        "already_tasks": "Ти вже отримав завдання 🕯",
        "need_role": "Спочатку потрібно дізнатися роль 🎭",
        "photo_request": "📸 Надішли фото сюди наступним повідомленням.",
        "task_word": "ЗАВДАННЯ",
        "reset": "Роль і завдання скинуто 🃏\n\nНатисни /start заново.",
        "intro": (
            "<b>🕸️ Вітаємо тебе в містечку INDIGO!</b>\n\n"
            "Це найзвичайніше містечко!\n\n"
            "Жителі працюють, відпочивають, веселяться...\n\n"
            "Але коли настає ніч, виявляється, що в кожного є свої таємниці…\n\n"
            "Плетуться інтриги, усі виглядають підозріло, і кожен приховує набагато більше, ніж здається! 🤫\n\n"
            "Тут є маніяки, мафія, лікарі, шерифи та мирні жителі.\n\n"
            "Настав час дізнатися, хто ти!\n\n"
            "<b>🎭 Місто засинає, прокидається…</b>"
        ),
    },
    "bg": {
        "choose_language": "Choose your language / Обери мову / Избери език:",
        "role_button": "Разбери своята роля! 🎭",
        "tasks_button": "Получи тайните задачи 📜",
        "send_photo": "📸 Изпрати",
        "already_tasks": "Вече получи задачите 🕯",
        "need_role": "Първо трябва да разбереш ролята си 🎭",
        "photo_request": "📸 Изпрати снимката тук със следващото съобщение.",
        "task_word": "ЗАДАЧА",
        "reset": "Ролята и задачите са изчистени 🃏\n\nНатисни /start отново.",
        "intro": (
            "<b>🕸️ Добре дошъл в градчето INDIGO!</b>\n\n"
            "Това е най-обикновено градче!\n\n"
            "Жителите работят, почиват, забавляват се...\n\n"
            "Но когато настъпи нощта, се оказва, че всеки има свои тайни…\n\n"
            "Плетат се интриги, всички изглеждат подозрителни и всеки крие много повече, отколкото изглежда! 🤫\n\n"
            "Тук има маниаци, мафия, доктори, шерифи и мирни жители.\n\n"
            "Време е да разбереш кой си ти!\n\n"
            "<b>🎭 Градът заспива, събужда се…</b>"
        ),
    },
    "en": {
        "choose_language": "Choose your language / Обери мову / Избери език:",
        "role_button": "Reveal your role! 🎭",
        "tasks_button": "Get secret tasks 📜",
        "send_photo": "📸 Send",
        "already_tasks": "You have already received the tasks 🕯",
        "need_role": "First, reveal your role 🎭",
        "photo_request": "📸 Send the photo here in your next message.",
        "task_word": "TASK",
        "reset": "Role and tasks have been reset 🃏\n\nPress /start again.",
        "intro": (
            "<b>🕸️ Welcome to the town of INDIGO!</b>\n\n"
            "It looks like a completely ordinary town!\n\n"
            "People work, rest, have fun...\n\n"
            "But when night falls, everyone turns out to have secrets…\n\n"
            "Intrigues are being woven, everyone looks suspicious, and everyone hides much more than it seems! 🤫\n\n"
            "There are maniacs, mafia, doctors, sheriffs, and civilians here.\n\n"
            "It is time to find out who you are!\n\n"
            "<b>🎭 The town falls asleep, wakes up…</b>"
        ),
    },
}

ROLE_MESSAGES = {
    "uk": {
        "mafia": "<b>МАФІЯ</b>\n\nТвоя роль на сьогодні!\n\n🃏 Тобі потрібно виконувати відповідні завдання, і наприкінці дня на вечірньому засіданні загального суду ми дізнаємося, чи змогли тебе розкусити!\n\n<b>Але нікому не кажи, що ти в грі!</b>",
        "detective": "<b>ШЕРИФ</b>\n\nТвоя роль на сьогодні!\n\n🔎 Тобі потрібно виконувати відповідні завдання, і наприкінці дня на вечірньому засіданні загального суду ми дізнаємося, чи зміг ти вгадати мафію та маніяків!\n\n<b>Але нікому не кажи, що ти в грі!</b>",
        "doctor": "<b>ЛІКАР</b>\n\nТвоя роль на сьогодні!\n\n🚑 Тобі потрібно виконувати відповідні завдання, і наприкінці дня на вечірньому засіданні загального суду ми дізнаємося, чи зміг ти когось врятувати!\n\n<b>Але нікому не кажи, що ти в грі!</b>",
        "maniac": "<b>МАНІЯК</b>\n\nТвоя роль на сьогодні!\n\n😈 Тобі потрібно виконувати відповідні завдання, і наприкінці дня на вечірньому засіданні загального суду ми дізнаємося, чи змогли тебе розкусити!\n\n<b>Але нікому не кажи, що ти в грі!</b>",
        "civilian": "<b>МИРНИЙ ЖИТЕЛЬ</b>\n\nТвоя роль на сьогодні!\n\n🌻 Тобі потрібно виконувати відповідні завдання, і наприкінці дня на вечірньому засіданні загального суду ми дізнаємося, чи зміг ти вижити!\n\nЯкщо думаєш, що це нудна роль… ти дуже помиляєшся!\nУ нашому містечку в тебе цікаві завдання, і від тебе залежить дуже багато!\n\n<b>Але нікому не кажи, що ти в грі!</b>",
    },
    "bg": {
        "mafia": "<b>МАФИЯ</b>\n\nТвоята роля за днес!\n\n🃏 Трябва да изпълняваш съответните задачи, а в края на деня на вечерното заседание на общия съд ще разберем дали са успели да те разкрият!\n\n<b>Но не казвай на никого, че си в играта!</b>",
        "detective": "<b>ШЕРИФ</b>\n\nТвоята роля за днес!\n\n🔎 Трябва да изпълняваш съответните задачи, а в края на деня на вечерното заседание на общия съд ще разберем дали си успял да познаеш мафията и маниаците!\n\n<b>Но не казвай на никого, че си в играта!</b>",
        "doctor": "<b>ДОКТОР</b>\n\nТвоята роля за днес!\n\n🚑 Трябва да изпълняваш съответните задачи, а в края на деня на вечерното заседание на общия съд ще разберем дали си успял да спасиш някого!\n\n<b>Но не казвай на никого, че си в играта!</b>",
        "maniac": "<b>МАНИАК</b>\n\nТвоята роля за днес!\n\n😈 Трябва да изпълняваш съответните задачи, а в края на деня на вечерното заседание на общия съд ще разберем дали са успели да те разкрият!\n\n<b>Но не казвай на никого, че си в играта!</b>",
        "civilian": "<b>МИРЕН ЖИТЕЛ</b>\n\nТвоята роля за днес!\n\n🌻 Трябва да изпълняваш съответните задачи, а в края на деня на вечерното заседание на общия съд ще разберем дали си успял да оцелееш!\n\nАко мислиш, че това е скучна роля… много грешиш!\nВ нашето градче имаш интересни задачи и много зависи от теб!\n\n<b>Но не казвай на никого, че си в играта!</b>",
    },
    "en": {
        "mafia": "<b>MAFIA</b>\n\nYour role for today!\n\n🃏 You need to complete the matching tasks, and at the evening meeting of the town court we will find out whether they managed to expose you!\n\n<b>But do not tell anyone that you are in the game!</b>",
        "detective": "<b>SHERIFF</b>\n\nYour role for today!\n\n🔎 You need to complete the matching tasks, and at the evening meeting of the town court we will find out whether you managed to guess the mafia and the maniacs!\n\n<b>But do not tell anyone that you are in the game!</b>",
        "doctor": "<b>DOCTOR</b>\n\nYour role for today!\n\n🚑 You need to complete the matching tasks, and at the evening meeting of the town court we will find out whether you managed to save someone!\n\n<b>But do not tell anyone that you are in the game!</b>",
        "maniac": "<b>MANIAC</b>\n\nYour role for today!\n\n😈 You need to complete the matching tasks, and at the evening meeting of the town court we will find out whether they managed to expose you!\n\n<b>But do not tell anyone that you are in the game!</b>",
        "civilian": "<b>CIVILIAN</b>\n\nYour role for today!\n\n🌻 You need to complete the matching tasks, and at the evening meeting of the town court we will find out whether you managed to survive!\n\nIf you think this is a boring role… you are very wrong!\nIn our town, you have interesting tasks, and a lot depends on you!\n\n<b>But do not tell anyone that you are in the game!</b>",
    },
}

TASKS = {
    "uk": {
        "mafia": [
            {"text": "Питай сьогодні людей:\n\n«Сьогодні дивний день, так?»\n\nМожеш додавати, що саме дивного бачиш ти, щоб звучало переконливіше.", "photo": False},
            {"text": "Підійди до 3 різних компаній.\n\nПостой поруч мовчки 20–30 секунд, потім спитай:\n\n«Ви граєте в мафію?»\n\nІ просто піди.", "photo": False},
            {"text": "Зроби селфі з людьми.\n\nКраще з тими, кого погано знаєш або взагалі не знаєш. Чим більше селфі, тим сильніша твоя мафіозна легенда.", "photo": True},
            {"text": "Не ходи туди, куди тебе сьогодні буде кликати хтось із дітей.\n\nМафія не піддається на чужі плани.", "photo": False},
        ],
        "detective": [
            {"text": "Шукай усіх, хто поводиться підозріло.\n\nЗапам’ятовуй дивні фрази, дивні рухи, дивні збіги і все, що здається не просто так.", "photo": False},
            {"text": "Непомітно фотографуй тих, кого вважаєш мафією.\n\nЦе твої докази для вечірнього розслідування.", "photo": True},
            {"text": "Умов мінімум 3 людей піти на творчу анімацію.\n\nНе просто поклич, а саме переконай.", "photo": False},
            {"text": "Знімай сьогоднішній день на відео так, ніби це трилер, а ти ведеш розслідування.\n\nКоментуй, що здається підозрілим, кого ти підозрюєш і що відбувається в місті.", "photo": True},
        ],
        "doctor": [
            {"text": "Зроби компліменти 10 людям.\n\nЩирі, короткі, несподівані. Лікар лікує атмосферу.", "photo": False},
            {"text": "Сьогодні ні з ким не фотографуйся.\n\nНе потрапляй ні на одне фото будь-якими способами. Якщо хтось хоче селфі з тобою, м’яко викручуйся.", "photo": False},
            {"text": "Допомагай аніматорам якнайбільше.\n\nОрганізувати, покликати, зібрати, пояснити, принести. Сьогодні ти польовий лікар команди.", "photo": False},
            {"text": "Допомагай усім носити речі.\n\nБачиш, що хтось щось несе? Запропонуй допомогу. Навіть якщо це дрібниця.", "photo": False},
        ],
        "maniac": [
            {"text": "Поводься максимально схоже на аніматора.\n\nДопомагай, клич людей на активності, створюй рух і роби вигляд, що все під контролем.", "photo": False},
            {"text": "Умов 5 незнайомих людей сфотографуватися разом.\n\nЯкщо вони погодилися, вони стали частиною твоєї дивної історії.", "photo": True},
            {"text": "Роби дивні речі, після яких тобі скажуть:\n\n«Що це зараз було?»\n\nЧим більше таких реакцій, тим краще.", "photo": False},
            {"text": "Відвідай якомога більше активностей сьогодні.\n\nМаніяк має бути всюди: на арті, іграх, спорті, біля басейну, на будь-якому русі.", "photo": False},
        ],
        "civilian": [
            {"text": "Познайомся з 2 новими людьми.\n\nДізнайся їхні імена і хоча б одну цікаву деталь про кожного.", "photo": False},
            {"text": "Погоджуйся йти туди, куди тебе сьогодні кличуть інші.\n\nЯкщо кличуть на активність, гру або арт, кажи «так» і йди.", "photo": False},
            {"text": "Змайструй щось своїми руками на арті.\n\nБудь-яку маленьку поробку, прикрасу, малюнок або щось красиве.", "photo": False},
            {"text": "На сніданку, обіді або вечері допомагай іншим.\n\nРадь, що взяти, допомагай накладати їжу, пропонуй принести сік, фрукти або десерт.", "photo": False},
        ],
    },
    "bg": {
        "mafia": [
            {"text": "Питай хората днес:\n\n„Днес е странен ден, нали?“\n\nМожеш да добавяш какво странно виждаш ти, за да звучи по-убедително.", "photo": False},
            {"text": "Отиди при 3 различни компании.\n\nПостой до тях мълчаливо 20–30 секунди, после попитай:\n\n„Играете ли мафия?“\n\nИ просто си тръгни.", "photo": False},
            {"text": "Направи селфи с хора.\n\nНай-добре с такива, които почти не познаваш или изобщо не познаваш. Колкото повече селфита, толкова по-силна е мафиотската ти легенда.", "photo": True},
            {"text": "Не ходи там, където днес някое дете ще те кани.\n\nМафията не се поддава на чужди планове.", "photo": False},
        ],
        "detective": [
            {"text": "Търси всички, които се държат подозрително.\n\nЗапомняй странни фрази, странни движения, странни съвпадения и всичко, което не изглежда случайно.", "photo": False},
            {"text": "Снимай незабелязано тези, които смяташ за мафия.\n\nТова са твоите доказателства за вечерното разследване.", "photo": True},
            {"text": "Убеди минимум 3 души да отидат на творческа анимация.\n\nНе просто ги покани, а наистина ги убеди.", "photo": False},
            {"text": "Снимай днешния ден на видео така, сякаш е трилър, а ти водиш разследване.\n\nКоментирай какво изглежда подозрително, кого подозираш и какво се случва в града.", "photo": True},
        ],
        "doctor": [
            {"text": "Направи комплименти на 10 души.\n\nИскрени, кратки, неочаквани. Докторът лекува атмосферата.", "photo": False},
            {"text": "Днес не се снимай с никого.\n\nНе попадай на нито една снимка по никакъв начин. Ако някой иска селфи с теб, измъкни се меко.", "photo": False},
            {"text": "Помагай на аниматорите колкото се може повече.\n\nДа организираш, да повикаш, да събереш, да обясниш, да донесеш. Днес си полевият доктор на отбора.", "photo": False},
            {"text": "Помагай на всички да носят вещи.\n\nВидиш ли, че някой носи нещо? Предложи помощ. Дори да е дреболия.", "photo": False},
        ],
        "maniac": [
            {"text": "Дръж се максимално като аниматор.\n\nПомагай, кани хора на активности, създавай движение и се прави, че всичко е под контрол.", "photo": False},
            {"text": "Убеди 5 непознати души да се снимат заедно.\n\nАко се съгласят, те стават част от твоята странна история.", "photo": True},
            {"text": "Прави странни неща, след които да ти кажат:\n\n„Какво беше това сега?“\n\nКолкото повече такива реакции, толкова по-добре.", "photo": False},
            {"text": "Посети колкото се може повече активности днес.\n\nМаниакът трябва да бъде навсякъде: на арт, игри, спорт, до басейна, при всяко движение.", "photo": False},
        ],
        "civilian": [
            {"text": "Запознай се с 2 нови души.\n\nНаучи имената им и поне една интересна подробност за всеки.", "photo": False},
            {"text": "Съгласявай се да отидеш там, където днес те канят другите.\n\nАко те викат на активност, игра или арт, кажи „да“ и отиди.", "photo": False},
            {"text": "Изработи нещо със собствените си ръце на арта.\n\nМалка творба, украшение, рисунка или нещо красиво.", "photo": False},
            {"text": "На закуска, обяд или вечеря помагай на другите.\n\nСъветвай какво да вземат, помагай да си сложат храна, предлагай да донесеш сок, плодове или десерт.", "photo": False},
        ],
    },
    "en": {
        "mafia": [
            {"text": "Ask people today:\n\n“Today is a strange day, right?”\n\nYou can add what strange things you notice, so it sounds more convincing.", "photo": False},
            {"text": "Go up to 3 different groups.\n\nStand next to them silently for 20–30 seconds, then ask:\n\n“Are you playing Mafia?”\n\nThen simply walk away.", "photo": False},
            {"text": "Take selfies with people.\n\nIt is better if they are people you barely know or do not know at all. The more selfies, the stronger your mafia legend becomes.", "photo": True},
            {"text": "Do not go anywhere a child invites you today.\n\nThe mafia does not follow other people’s plans.", "photo": False},
        ],
        "detective": [
            {"text": "Look for everyone who acts suspiciously.\n\nRemember strange phrases, strange movements, strange coincidences, and anything that feels not random.", "photo": False},
            {"text": "Secretly take photos of the people you think are mafia.\n\nThese are your clues for the evening investigation.", "photo": True},
            {"text": "Convince at least 3 people to go to a creative activity.\n\nDo not just invite them. Actually persuade them.", "photo": False},
            {"text": "Film today like it is a thriller and you are leading an investigation.\n\nComment on what looks suspicious, who you suspect, and what is happening in the town.", "photo": True},
        ],
        "doctor": [
            {"text": "Give compliments to 10 people.\n\nSincere, short, unexpected. The doctor heals the atmosphere.", "photo": False},
            {"text": "Do not take photos with anyone today.\n\nAvoid appearing in any photo in any way. If someone wants a selfie with you, gently escape.", "photo": False},
            {"text": "Help the animators as much as possible.\n\nOrganize, invite, gather, explain, bring things. Today you are the field doctor of the team.", "photo": False},
            {"text": "Help everyone carry things.\n\nIf you see someone carrying something, offer help. Even if it is something small.", "photo": False},
        ],
        "maniac": [
            {"text": "Act as much like an animator as possible.\n\nHelp, invite people to activities, create energy, and pretend that everything is under control.", "photo": False},
            {"text": "Convince 5 strangers to take a photo together.\n\nIf they agree, they become part of your strange story.", "photo": True},
            {"text": "Do strange things that make people say:\n\n“What was that just now?”\n\nThe more reactions like this you get, the better.", "photo": False},
            {"text": "Visit as many activities as possible today.\n\nThe maniac must be everywhere: art, games, sports, by the pool, and anywhere something is happening.", "photo": False},
        ],
        "civilian": [
            {"text": "Meet 2 new people.\n\nLearn their names and at least one interesting detail about each of them.", "photo": False},
            {"text": "Agree to go wherever other people invite you today.\n\nIf they invite you to an activity, a game, or art, say “yes” and go.", "photo": False},
            {"text": "Make something with your own hands at the art activity.\n\nAny small craft, decoration, drawing, or something beautiful.", "photo": False},
            {"text": "At breakfast, lunch, or dinner, help others.\n\nSuggest what to take, help them serve food, offer to bring juice, fruit, or dessert.", "photo": False},
        ],
    },
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Українська 🇺🇦", callback_data="lang_uk")],
        [InlineKeyboardButton("Български 🇧🇬", callback_data="lang_bg")],
        [InlineKeyboardButton("English 🇬🇧", callback_data="lang_en")],
    ]

    await update.message.reply_text(
        TEXTS["en"]["choose_language"],
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, "en")

    user_roles.pop(user_id, None)
    user_languages.pop(user_id, None)
    user_tasks_sent.discard(user_id)

    await update.message.reply_text(TEXTS[lang]["reset"])


async def send_tasks(query, role, user_id, lang):
    if user_id in user_tasks_sent:
        await query.message.reply_text(TEXTS[lang]["already_tasks"])
        return

    emoji = ROLE_EMOJI[role]

    for index, task in enumerate(TASKS[lang][role], start=1):
        keyboard = None

        if task["photo"]:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(TEXTS[lang]["send_photo"], callback_data=f"send_photo_{role}_{index}")]
            ])

        await query.message.reply_text(
            f"<b>{TEXTS[lang]['task_word']} {index}</b>\n\n{emoji} {task['text']}",
            parse_mode="HTML",
            reply_markup=keyboard,
        )

    user_tasks_sent.add(user_id)




async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    try:
        await query.answer()
    except Exception:
        pass

    user_id = query.from_user.id
    data = query.data

    if data.startswith("lang_"):
        lang = data.replace("lang_", "")
        user_languages[user_id] = lang

        keyboard = [
            [InlineKeyboardButton(TEXTS[lang]["role_button"], callback_data="get_role")]
        ]

        await query.message.reply_text(
            TEXTS[lang]["intro"],
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif data == "get_role":
        lang = user_languages.get(user_id, "en")
        role = user_roles.get(user_id)

        if not role:
            await context.bot.send_dice(chat_id=user_id, emoji="🎲")
            await asyncio.sleep(5)

            role = random.choices(
                ROLE_KEYS,
                weights=ROLE_WEIGHTS,
                k=1
            )[0]

            user_roles[user_id] = role

        keyboard = [
            [InlineKeyboardButton(TEXTS[lang]["tasks_button"], callback_data="get_tasks")]
        ]

        await query.message.reply_text(
            ROLE_MESSAGES[lang][role],
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif data == "get_tasks":
        lang = user_languages.get(user_id, "en")
        role = user_roles.get(user_id)

        if not role:
            await query.message.reply_text(TEXTS[lang]["need_role"])
            return

        await send_tasks(query, role, user_id, lang)

    elif data.startswith("send_photo_"):
        lang = user_languages.get(user_id, "en")

        parts = data.split("_")
        role = parts[2]
        task_number = parts[3]

        pending_photo_tasks[user_id] = {
            "role": role,
            "task_number": task_number,
            "lang": lang,
        }

        await query.message.reply_text(TEXTS[lang]["photo_request"])


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = update.effective_user

    task_info = pending_photo_tasks.get(user_id)

    if not task_info:
        await update.message.reply_text(
            "Спочатку натисни кнопку 📸 / Първо натисни бутона 📸 / First press the 📸 button."
        )
        return

    role = task_info["role"]
    task_number = task_info["task_number"]
    lang = task_info["lang"]

    photo = update.message.photo[-1]

    username = f"@{user.username}" if user.username else "немає / няма / none"
    full_name = user.full_name or user.first_name or "Unknown"

    role_title = ROLE_NAMES[lang].get(role, role)
    role_emoji = ROLE_EMOJI.get(role, "")

    caption = (
        f"{role_emoji} {role_title}\n\n"
        f"{TEXTS[lang]['task_word']} {task_number}\n\n"
        f"👤 Name: {full_name}\n"
        f"🔗 Username: {username}\n"
        f"🆔 User ID: {user_id}"
    )

    await context.bot.send_photo(
        chat_id=MAFIA_GROUP_ID,
        message_thread_id=MAFIA_TOPIC_ID,
        photo=photo.file_id,
        caption=caption,
    )

    success_texts = {
        "uk": "Фото відправлено аніматорам ✅",
        "bg": "Снимката е изпратена на аниматорите ✅",
        "en": "Photo sent to the animators ✅",
    }

    await update.message.reply_text(success_texts[lang])

    pending_photo_tasks.pop(user_id, None)


async def topic_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message

    await update.message.reply_text(
        f"📌 Group ID:\n<code>{chat.id}</code>\n\n"
        f"📌 Topic ID:\n<code>{message.message_thread_id}</code>",
        parse_mode="HTML",
    )


def main():
    if not TOKEN:
        print("Ошибка: BOT_TOKEN не найден в файле .env")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(CommandHandler("id", topic_id))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))


    print("Mafia Bot запущен 🃏")
    app.run_polling()


if __name__ == "__main__":
    main()
