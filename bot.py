import os
import random
import asyncio
from datetime import time
from zoneinfo import ZoneInfo
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
user_task7_sent = set()
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
        "already_tasks": "Ти вже отримав завдання 1–6 🕯",
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
        "already_tasks": "Вече получи задачи 1–6 🕯",
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
        "already_tasks": "You have already received tasks 1–6 🕯",
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
            {"text": "ВИБИРАЙ ЖЕРТВ!\n\nЛюдей у чорному, людей у білому, в окулярах або в зелених капцях.\n\nЗ ними потрібно заговорити зранку, потім протягом дня ще раз, а потім утретє так, ніби ви НЕ спілкувалися.", "photo": False},
            {"text": "Питай сьогодні якомога більше людей:\n\n«Сьогодні дивний день, так?»\n\nГовори, що дивного бачиш ти, щоб вони повірили.", "photo": False},
            {"text": "Підійди до 3 різних компаній, постій з ними 1–2 хвилини й піди без пояснення.\n\nДізнайся, чи грають вони в мафію. Якщо ні, поклич ненав’язливо.", "photo": False},
            {"text": "Зроби так, щоб хтось змінив плани.\n\nНаприклад, пішов на іншу активність. Чим більше людей переманиш, тим краще.\n\nОсобливо якщо вмовиш тих, хто не хоче. Увечері розкажеш, кого переконав.", "photo": False},
            {"text": "Переконай незнайомих людей зробити з тобою селфі.\n\nЯкщо переконав, це твої жертви.\n\nТільки з однією людиною, групою не можна.", "photo": True},
            {"text": "Не ходи туди, куди тебе сьогодні буде кликати хтось із дітей.", "photo": False},
            {"text": "Збери свідків!\n\n2 людини. Вони мають увечері підтвердити, що ти змінив їхні плани вдень.\n\nНе кажи їм навіщо. Просто переконайся, що вони будуть з тобою на вечірці й 100% підтвердять те, що ти скажеш.", "photo": False},
        ],
        "detective": [
            {"text": "Запам’ятовуй дивну поведінку людей.", "photo": False},
            {"text": "Знайди людину, яка виглядає підозріло.", "photo": False},
            {"text": "Візьми 2–3 людей, які явно не знайомі між собою, і запропонуй їм разом піти на якусь анімацію.", "photo": False},
            {"text": "Зроби селфі, але природно, щоб ніхто ні про що не здогадався, з людьми, яких вважаєш мафією.", "photo": True},
            {"text": "Знімай сьогоднішній день на відео від імені детектива.\n\nЯк трилер. Це влог твого дня! Розповідай, що підозріло, що роблять інші. Змонтуй, ми подивимося ввечері.", "photo": True},
            {"text": "Підійди до 3 людей і скажи:\n\n«Пішли зараз на будь-яку активність, буде прикольно».\n\nЗавдання: не просто покликати, а переконати хоча б 1 погодитися.", "photo": False},
            {"text": "Зроби фінальні висновки: хто мафія.\n\nМожеш їх навіть таємно сфоткати, щоб довести на вечірці.", "photo": True},
        ],
        "doctor": [
            {"text": "Зроби комплімент 10 людям.", "photo": False},
            {"text": "Допомагай усім носити речі.\n\nНе важливо кому, важливо що. Бачиш, що людина щось несе, запропонуй допомогу.", "photo": False},
            {"text": "Якщо бачиш одну людину або когось, хто сумує, почни з ним розмову і запроси на якусь анімацію або активність.", "photo": False},
            {"text": "ЗАПАМ’ЯТАЙ!\n\nНе фотографуйся ні з ким. Сьогодні не має бути жодного фото когось із тобою.\n\nЯкщо поруч з тобою хтось збирається фотографуватися або робити селфі, зроби все можливе, щоб цього не сталося.", "photo": False},
            {"text": "Сам зроби селфі з людьми, з ким вважаєш потрібним, але тільки по одному і так, щоб ніхто не бачив.\n\nЯк відчуваєш, кого треба лікувати.\n\nМожеш зробити одне своє селфі в ролі лікаря. Класне селфі.", "photo": True},
            {"text": "Допомагай аніматорам стежити за порядком.\n\nДопомагай на анімації щось організувати, зібрати дітей тощо.", "photo": False},
            {"text": "Збери свідків!\n\n3 людини. Вони мають увечері підтвердити, що ти:\n\n1) одному з них зробив комплімент\n2) одному допоміг\n3) повів на анімацію\n\nНе кажи їм навіщо. Просто переконайся, що вони будуть з тобою на вечірці й 100% підтвердять те, що ти скажеш.", "photo": False},
        ],
        "maniac": [
            {"text": "Поводься максимально схоже на аніматора цілий день.\n\nНамагайся їм допомагати, організовувати анімацію. Ти як вони.", "photo": False},
            {"text": "Переконай 5 незнайомих людей зробити фото разом.\n\nЯкщо переконав, це твої жертви.", "photo": True},
            {"text": "Роби дії, після яких людина скаже:\n\n«Що це було?»\n\nЧим більше таких питань збереш, тим більше балів.", "photo": False},
            {"text": "Відвідай якомога більше активностей сьогодні.", "photo": False},
            {"text": "Скажи 10 людям, яких вважаєш мафією:\n\n«Я тебе запам’ятав».\n\nНічого не пояснюй.", "photo": False},
            {"text": "Знімай сьогоднішній день на відео від імені маніяка.\n\nЯк трилер. Це влог твого дня! Розповідай, що підозріло, що робиш ти, що роблять інші. Змонтуй, ми подивимося ввечері.", "photo": True},
            {"text": "Збери свідків!\n\n3 людини. Вони мають увечері підтвердити, що ти:\n\n1) поводився як аніматор\n2) робив дивні дії\n3) комусь із них сказав «Я тебе запам’ятав»\n\nНе кажи їм навіщо. Просто переконайся, що вони будуть з тобою на вечірці й 100% підтвердять те, що ти скажеш.", "photo": False},
        ],
        "civilian": [
            {"text": "Познайомся з 2 новими людьми.", "photo": False},
            {"text": "Погоджуйся йти туди, куди тебе сьогодні кличуть інші.", "photo": False},
            {"text": "Спробуй нову активність.", "photo": False},
            {"text": "Зроби мінімум 3 селфі з дуже великими компаніями.\n\nЧим більше людей збереш, тим краще.", "photo": True},
            {"text": "Змайструй щось своїми руками, зроби щось красиве і подаруй 1 незнайомій людині.", "photo": False},
            {"text": "На сніданку, обіді або вечері допомагай усім, кому можеш, з вибором їжі.\n\nРадь, що взяти. Проходячи повз столик, спитай, чи не принести комусь ще соку, фруктів або десерту.\n\nБудь дуже ввічливим і уважним. Навіть із незнайомими.", "photo": False},
            {"text": "Збери свідків!\n\n5 людей. Хтось із них має підтвердити, що ти:\n\n1) зробив подарунок\n2) спробував щось нове з активностей у таборі\n3) двоє підтвердять, що ти з ними познайомився\n4) ще один підтвердить, що ти був активним у ресторані\n\nНе кажи їм навіщо. Просто переконайся, що вони будуть з тобою на вечірці 100%.", "photo": False},
        ],
    },
    "bg": {
        "mafia": [
            {"text": "ИЗБИРАЙ ЖЕРТВИ!\n\nХора в черно, хора в бяло, с очила или със зелени чехли.\n\nТрябва да заговориш с тях сутринта, после още веднъж през деня, а после трети път, сякаш изобщо НЕ сте общували.", "photo": False},
            {"text": "Питай днес колкото се може повече хора:\n\n„Днес е странен ден, нали?“\n\nКазвай какво странно виждаш ти, за да ти повярват.", "photo": False},
            {"text": "Отиди при 3 различни компании, постой с тях 1–2 минути и си тръгни без обяснение.\n\nРазбери дали играят мафия. Ако не, покани ги ненатрапчиво.", "photo": False},
            {"text": "Направи така, че някой да си промени плановете.\n\nНапример да отиде на друга активност. Колкото повече хора пренасочиш, толкова по-добре.\n\nОсобено ако убедиш тези, които не искат. Вечерта ще разкажеш кого си убедил.", "photo": False},
            {"text": "Убеди непознат човек да си направи селфи с теб.\n\nАко го убедиш, той е твоята жертва.\n\nСамо с един човек, групово не може.", "photo": True},
            {"text": "Не ходи там, където днес някое дете ще те кани.", "photo": False},
            {"text": "Събери свидетели!\n\n2 души. Вечерта те трябва да потвърдят, че си променил плановете им през деня.\n\nНе им казвай защо. Просто се увери, че ще бъдат с теб на вечерната програма и 100% ще потвърдят това, което кажеш.", "photo": False},
        ],
        "detective": [
            {"text": "Запомняй странното поведение на хората.", "photo": False},
            {"text": "Намери човек, който изглежда подозрително.", "photo": False},
            {"text": "Вземи 2–3 души, които очевидно не се познават, и им предложи заедно да отидат на някаква анимация.", "photo": False},
            {"text": "Направи селфи естествено, така че никой да не се досети, с хората, които смяташ за мафия.", "photo": True},
            {"text": "Снимай днешния ден на видео от гледната точка на детектив.\n\nКато трилър. Това е влогът на твоя ден! Разказвай кое е подозрително и какво правят другите. Монтирай го, ще го гледаме вечерта.", "photo": True},
            {"text": "Отиди при 3 души и кажи:\n\n„Хайде сега на някаква активност, ще бъде забавно“.\n\nЗадача: не просто да поканиш, а да убедиш поне 1 човек да се съгласи.", "photo": False},
            {"text": "Направи финални изводи: кой е мафията.\n\nМожеш дори тайно да ги снимаш, за да докажеш вечерта.", "photo": True},
        ],
        "doctor": [
            {"text": "Направи комплимент на 10 души.", "photo": False},
            {"text": "Помагай на всички да носят вещи.\n\nНе е важно на кого, важно е какво. Ако видиш, че някой носи нещо, предложи помощ.", "photo": False},
            {"text": "Ако видиш човек сам или някой, който скучае, започни разговор с него и го покани на някаква анимация или активност.", "photo": False},
            {"text": "ЗАПОМНИ!\n\nНе се снимай с никого. Днес не трябва да има нито една снимка на някого с теб.\n\nАко някой около теб се кани да се снима или да прави селфи, направи всичко възможно това да не се случи.", "photo": False},
            {"text": "Сам направи селфи с хора, с които смяташ за нужно, но само по един човек и така, че никой да не види.\n\nКакто усещаш кого трябва да лекуваш.\n\nМожеш да направиш и едно свое селфи в ролята на доктор. Яко селфи.", "photo": True},
            {"text": "Помагай на аниматорите да следят за реда.\n\nПомагай на анимацията да организирате нещо, да съберете децата и т.н.", "photo": False},
            {"text": "Събери свидетели!\n\n3 души. Вечерта те трябва да потвърдят, че ти:\n\n1) на един от тях си направил комплимент\n2) на един си помогнал\n3) си завел някого на анимация\n\nНе им казвай защо. Просто се увери, че ще бъдат с теб вечерта и 100% ще потвърдят това, което кажеш.", "photo": False},
        ],
        "maniac": [
            {"text": "Дръж се максимално като аниматор през целия ден.\n\nОпитвай се да им помагаш, да организираш анимация. Ти си като тях.", "photo": False},
            {"text": "Убеди 5 непознати души да направят снимка заедно.\n\nАко ги убедиш, те са твоите жертви.", "photo": True},
            {"text": "Прави действия, след които човек да каже:\n\n„Какво беше това?“\n\nКолкото повече такива въпроси събереш, толкова повече точки.", "photo": False},
            {"text": "Посети колкото се може повече активности днес.", "photo": False},
            {"text": "Кажи на 10 души, които смяташ за мафия:\n\n„Запомних те“.\n\nНе обяснявай нищо.", "photo": False},
            {"text": "Снимай днешния ден на видео от гледната точка на маниак.\n\nКато трилър. Това е влогът на твоя ден! Разказвай кое е подозрително, какво правиш ти и какво правят другите. Монтирай го, ще го гледаме вечерта.", "photo": True},
            {"text": "Събери свидетели!\n\n3 души. Вечерта те трябва да потвърдят, че ти:\n\n1) си се държал като аниматор\n2) си правил странни действия\n3) си казал на някого „Запомних те“\n\nНе им казвай защо. Просто се увери, че ще бъдат с теб вечерта и 100% ще потвърдят това, което кажеш.", "photo": False},
        ],
        "civilian": [
            {"text": "Запознай се с 2 нови души.", "photo": False},
            {"text": "Съгласявай се да отидеш там, където днес те канят другите.", "photo": False},
            {"text": "Пробвай нова активност.", "photo": False},
            {"text": "Направи минимум 3 селфита с много големи компании.\n\nКолкото повече хора събереш, толкова по-добре.", "photo": True},
            {"text": "Изработи нещо със собствените си ръце, направи нещо красиво и го подари на 1 непознат човек.", "photo": False},
            {"text": "На закуска, обяд или вечеря помагай на всички, на които можеш, с избора на храна.\n\nСъветвай какво да вземат. Когато минаваш покрай маса, попитай дали да донесеш на някого сок, плодове или десерт.\n\nБъди много учтив и услужлив. Дори с непознати.", "photo": False},
            {"text": "Събери свидетели!\n\n5 души. Някой от тях трябва да потвърди, че ти:\n\n1) си направил подарък\n2) си пробвал нещо ново от активностите в лагера\n3) двама ще потвърдят, че си се запознал с тях\n4) още един ще потвърди, че си бил активен в ресторанта\n\nНе им казвай защо. Просто се увери, че ще бъдат с теб вечерта 100%.", "photo": False},
        ],
    },
    "en": {
        "mafia": [
            {"text": "CHOOSE YOUR VICTIMS!\n\nPeople in black, people in white, people with glasses, or people in green slippers.\n\nYou need to talk to them in the morning, then again during the day, and then a third time as if you have NEVER spoken before.", "photo": False},
            {"text": "Ask as many people as possible today:\n\n“Today is a strange day, right?”\n\nTell them what strange things you notice so they believe you.", "photo": False},
            {"text": "Go up to 3 different groups, stand with them for 1–2 minutes, and then leave without explaining.\n\nFind out if they are playing Mafia. If not, invite them casually.", "photo": False},
            {"text": "Make someone change their plans.\n\nFor example, convince them to go to another activity. The more people you redirect, the better.\n\nEspecially if you convince people who did not want to. In the evening, you will tell us who you convinced.", "photo": False},
            {"text": "Convince a stranger to take a selfie with you.\n\nIf you convince them, they are your victim.\n\nOnly one person. Group photos do not count.", "photo": True},
            {"text": "Do not go anywhere a child invites you today.", "photo": False},
            {"text": "Gather witnesses!\n\n2 people. In the evening, they must confirm that you changed their plans during the day.\n\nDo not tell them why. Just make sure they will be with you at the evening event and will 100% confirm what you say.", "photo": False},
        ],
        "detective": [
            {"text": "Remember strange behavior you notice in people.", "photo": False},
            {"text": "Find someone who looks suspicious.", "photo": False},
            {"text": "Take 2–3 people who clearly do not know each other and suggest that they go to an animation activity together.", "photo": False},
            {"text": "Take a selfie naturally, so nobody suspects anything, with the people you think are mafia.", "photo": True},
            {"text": "Film today from the point of view of a detective.\n\nMake it like a thriller. This is your day vlog! Talk about what looks suspicious and what other people are doing. Edit it, we will watch it in the evening.", "photo": True},
            {"text": "Go up to 3 people and say:\n\n“Let’s go to any activity now, it will be fun.”\n\nYour task: not just to invite them, but to convince at least 1 person to agree.", "photo": False},
            {"text": "Make your final conclusions: who is mafia.\n\nYou can even secretly take photos of them as proof for the evening event.", "photo": True},
        ],
        "doctor": [
            {"text": "Give compliments to 10 people.", "photo": False},
            {"text": "Help everyone carry things.\n\nIt does not matter who it is, the important thing is helping. If you see someone carrying something, offer help.", "photo": False},
            {"text": "If you see someone alone or bored, start a conversation with them and invite them to an animation activity or any other activity.", "photo": False},
            {"text": "REMEMBER!\n\nDo not take photos with anyone. Today there must not be a single photo of someone with you.\n\nIf someone near you wants to take a photo or selfie, do everything possible to stop it from happening.", "photo": False},
            {"text": "You may take selfies with people you think are important, but only one person at a time and so that nobody sees.\n\nTrust your feeling about who needs healing.\n\nYou can also take one selfie of yourself as the doctor. A cool selfie.", "photo": True},
            {"text": "Help the animators keep order.\n\nHelp organize activities, gather children, and support the animation team.", "photo": False},
            {"text": "Gather witnesses!\n\n3 people. In the evening, they must confirm that you:\n\n1) gave one of them a compliment\n2) helped one of them\n3) brought someone to an activity\n\nDo not tell them why. Just make sure they will be with you in the evening and will 100% confirm what you say.", "photo": False},
        ],
        "maniac": [
            {"text": "Act as much like an animator as possible all day.\n\nTry to help them and organize activities. You are like them.", "photo": False},
            {"text": "Convince 5 strangers to take a photo together.\n\nIf you convince them, they are your victims.", "photo": True},
            {"text": "Do things that make people ask:\n\n“What was that?”\n\nThe more of these questions you collect, the more points you get.", "photo": False},
            {"text": "Visit as many activities as possible today.", "photo": False},
            {"text": "Tell 10 people you think are mafia:\n\n“I remembered you.”\n\nDo not explain anything.", "photo": False},
            {"text": "Film today from the point of view of a maniac.\n\nMake it like a thriller. This is your day vlog! Talk about what looks suspicious, what you are doing, and what others are doing. Edit it, we will watch it in the evening.", "photo": True},
            {"text": "Gather witnesses!\n\n3 people. In the evening, they must confirm that you:\n\n1) acted like an animator\n2) did strange things\n3) told someone “I remembered you”\n\nDo not tell them why. Just make sure they will be with you in the evening and will 100% confirm what you say.", "photo": False},
        ],
        "civilian": [
            {"text": "Meet 2 new people.", "photo": False},
            {"text": "Agree to go wherever other people invite you today.", "photo": False},
            {"text": "Try a new activity.", "photo": False},
            {"text": "Take at least 3 selfies with very large groups.\n\nThe more people you gather, the better.", "photo": True},
            {"text": "Make something with your own hands, create something beautiful, and give it to 1 stranger.", "photo": False},
            {"text": "At breakfast, lunch, or dinner, help everyone you can with choosing food.\n\nSuggest what to take. When passing by a table, ask if someone needs juice, fruit, or dessert.\n\nBe very polite and helpful. Even with strangers.", "photo": False},
            {"text": "Gather witnesses!\n\n5 people. Some of them must confirm that you:\n\n1) made a gift\n2) tried something new from the camp activities\n3) two people confirm that you met them\n4) one more person confirms that you were active in the restaurant\n\nDo not tell them why. Just make sure they will be with you in the evening 100%.", "photo": False},
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
    user_task7_sent.discard(user_id)

    await update.message.reply_text(TEXTS[lang]["reset"])


async def send_tasks_1_to_6(query, role, user_id, lang):
    if user_id in user_tasks_sent:
        await query.message.reply_text(TEXTS[lang]["already_tasks"])
        return

    emoji = ROLE_EMOJI[role]

    for index, task in enumerate(TASKS[lang][role][:6], start=1):
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


async def send_all_task_7(context: ContextTypes.DEFAULT_TYPE):
    for user_id, role in list(user_roles.items()):
        if user_id in user_task7_sent:
            continue

        lang = user_languages.get(user_id, "en")
        emoji = ROLE_EMOJI[role]
        task = TASKS[lang][role][6]

        keyboard = None
        if task["photo"]:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(TEXTS[lang]["send_photo"], callback_data=f"send_photo_{role}_7")]
            ])

        await context.bot.send_message(
            chat_id=user_id,
            text=f"<b>{TEXTS[lang]['task_word']} 7</b>\n\n{emoji} {task['text']}",
            parse_mode="HTML",
            reply_markup=keyboard,
        )

        user_task7_sent.add(user_id)


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

        await send_tasks_1_to_6(query, role, user_id, lang)

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

    app.job_queue.run_daily(
        send_all_task_7,
        time=time(hour=18, minute=30, tzinfo=ZoneInfo("Europe/Sofia")),
    )

    print("Mafia Bot запущен 🃏")
    app.run_polling()


if __name__ == "__main__":
    main()