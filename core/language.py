import core.database as db

# Translations dictionary
TRANSLATIONS = {
    "en": {
        # MENU & SETTINGS
        "menu_commands_btn": "📖 Commands",
        "menu_settings_btn": "⚙️ Settings",
        "settings_greeting": "⚙️ <b>Settings Menu</b>\n\nSelect an option below to configure your bot:",
        "menu_language_btn": "🌍 Language",
        "menu_currencies_btn": "💱 Currency",
        "menu_pushover_btn": "📲 Pushover",
        "menu_back_btn": "⬅️ Back to settings",
        "choose_language": "Choose your language / Оберіть мову / Выберите язык:",
        "lang_changed": "✅ Language successfully changed to English!",
        "choose_currency": "Select currency to display prices:",
        "cur_crypto_title": "— 💎 CRYPTOCURRENCIES —",
        "group_admin_only": "⚠️ Only group administrators can change bot settings.",
        "start_greeting": (
            "Hello, <b>{name}</b>! 👋\n\n"
            "I am your professional crypto assistant. Here is what I can do:\n\n"
            "📊 <b>Market & Prices:</b>\n"
            "• <code>/price btc</code> — Current price of a coin (or <code>/price 1.5 eth</code>).\n"
            "• <code>/chart btc</code> — Generate a candlestick chart.\n"
            "• <code>/top 10</code> — Top 10 gainers (add 'l' for losers: <code>/top 5 l</code>).\n"
            "• <code>/funding btc</code> — Perpetual funding rate.\n\n"
            "🔔 <b>Alerts & Notifications:</b>\n"
            "• <code>/alert btc 65000</code> — Set a price alert <i>(add <code>repeat 10</code> to repeat every 10 seconds)</i>.\n"
            "• <code>/alerts</code> — Manage active alerts.\n"
            "• <code>/pushover</code> — Set up phone push notifications.\n\n"
            "🔢 <i>Tip: Send any math expression (e.g., <code>15*65000</code>) to use the inline calculator!</i>\n\n"
            "💡 <i>Prefer short commands? Tap /shortcuts to see all aliases!</i>"
        ),
        "commands_private": (
            "📖 <b>Available Commands (Private Chat)</b>\n\n"
            "• <code>/price [coin]</code> (<code>/p</code>) — Current price (e.g. <code>/p 2.5 eth</code>)\n"
            "• <code>/chart [coin]</code> (<code>/c</code>) — Interactive candlestick chart\n"
            "• <code>/top [1-50] [h/l]</code> (<code>/t</code>) — Top 24h gainers or losers\n"
            "• <code>/funding [coin]</code> (<code>/f</code>) — Perpetual futures funding rate\n"
            "• <code>/cal [expr]</code> — Math calculator (also works without command)\n"
            "• <code>/alert [coin] [price] [r] [sec]</code> (<code>/a</code>) — Set price alert\n"
            "• <code>/alerts</code> (<code>/as</code>) — Manage active alerts\n"
            "• <code>/pushover [key]</code> — Configure mobile push notifications\n"
            "• <code>/testpush</code> — Send a test push notification\n"
            "• <code>/settings</code>, <code>/currency</code>, <code>/language</code> (<code>/l</code>) — Bot settings"
        ),
        "commands_group": (
            "📖 <b>Available Commands (Group Chat)</b>\n\n"
            "• <code>/price [coin]</code> (<code>/p</code>) — Current price\n"
            "• <code>/chart [coin]</code> (<code>/c</code>) — Interactive candlestick chart\n"
            "• <code>/top [1-50] [h/l]</code> (<code>/t</code>) — Top 24h gainers or losers\n"
            "• <code>/funding [coin]</code> (<code>/f</code>) — Perpetual futures funding rate\n"
            "• <code>/cal [expr]</code> — Math calculator\n"
            "• <code>/settings</code>, <code>/currency</code>, <code>/language</code> — Group settings <i>(admins only)</i>\n\n"
            "<i>💡 Price alerts and Pushover work in private messages with the bot.</i>"
        ),

        # COMMAND USAGES & ERRORS
        "price_usage": "ℹ️ <b>Format:</b> <code>/price [coin]</code>\nExample: <code>/price btc</code> or <code>/price 1.5 eth</code>",
        "price_invalid": "❌ Invalid format or coin not found.",
        "price_pieces": " pcs.",

        "cal_usage": "ℹ️ <b>Format:</b> <code>/cal [expression]</code>\nExample: <code>/cal (1500 + 250) * 2</code>",
        "cal_invalid": "❌ Invalid math expression.",

        "funding_usage": "ℹ️ <b>Format:</b> <code>/funding [coin]</code>\nExample: <code>/funding sol</code>",
        "funding_longs": "Longs pay",
        "funding_shorts": "Shorts pay",
        "funding_error": "❌ Spot only / Not found",
        "funding_global_err": "❌ Error checking funding.",

        "top_usage": "ℹ️ <b>Format:</b> <code>/top [1-50] [h/l]</code>\nExamples: <code>/top 10</code> (gainers), <code>/top 5 l</code> (losers)",
        "top_limit_err": "❌ Limit must be between 1 and 50.",
        "top_dir_err": "❌ Direction must be <b>h</b> (gainers) or <b>l</b> (losers).",
        "top_val_err": "❌ Limit must be a number. Example: <code>/top 10</code>",
        "top_fetch_err": "❌ Failed to fetch market data.",
        "top_gainers": "Top gainers",
        "top_losers": "Top losers",
        "top_global_err": "❌ Error loading top coins.",
        "top_status_msg": "⏳ Gathering data from the exchange...",

        "shortcuts_text": "⚡️ <b>Command Shortcuts</b>\n\n• <code>/p</code> = <code>/price</code>\n• <code>/c</code> = <code>/chart</code>\n• <code>/t</code> = <code>/top</code>\n• <code>/f</code> = <code>/funding</code>\n• <code>/a</code> = <code>/alert</code>\n• <code>/l</code> = <code>/language</code>\n\n<i>You can use these short commands interchangeably with the full ones!</i>",

        # ALERTS
        "alert_usage": "ℹ️ <b>Format:</b> <code>/alert [coin] [price]</code>\nExample: <code>/alert btc 65000</code>\n<i>(Add <code>repeat 10</code> or <code>r 10</code> to repeat every 10s)</i>",
        "alert_invalid_fmt": "❌ Invalid format. Example: <code>/alert btc 65000</code>",
        "alert_nan": "❌ Price must be a number.",
        "alert_not_found": "❌ Coin {ticker} not found.",
        "alert_api_err": "❌ Exchange connection error.",
        "alert_limit": "❌ Maximum 20 active alerts.",
        "alert_created": "✅ <b>Alert created!</b>\nCoin: <b>{ticker}</b>\nTarget: <b>{target:g}</b> USDT{repeat}",
        "alert_repeat_sfx": " <b>(r {interval}s)</b>",
        "alert_not_exists": "This alert no longer exists.",
        "alert_deleted_alert": "✅ Alert deleted!",
        "alert_turned_off": "\n\n<i>❌ Notification turned off.</i>",
        "alerts_no_active": "You have no active alerts.",
        "alerts_list_text": "Here are your active alerts. Click any to delete:",
        "alert_del_all_btn": "🗑 Delete ALL",
        "alert_del_yes_btn": "✅ Yes, delete",
        "alert_del_no_btn": "❌ No, cancel",
        "alert_del_confirm_text": "⚠️ <b>Delete this alert?</b>\n\nCoin: <b>{symbol}</b>\nTarget: <b>{target:g}</b> USDT{repeat}",
        "alert_del_all_yes_btn": "✅ Yes, delete ALL",
        "alert_del_all_confirm_text": "⚠️ <b>Are you sure you want to delete ALL your alerts?</b>",
        "alert_all_deleted_popup": "✅ All alerts deleted!",
        "alert_all_deleted_text": "All active alerts have been successfully cleared.",
        "alert_triggered_up": "📈 rose ABOVE",
        "alert_triggered_down": "📉 fell BELOW",
        "alert_triggered_msg": "🔔 <b>PRICE ALERT</b> 🔔\n\nCoin <b>{symbol}</b> {dir_text} target <b>{target:g}</b> USDT!\nCurrent price: <b>{current:g}</b> USDT",
        "alert_repeat_msg": "\n<i>(🔄 Repeats every {interval}s)</i>",
        "alert_turn_off_btn": "🔕 Turn off this alert",
        "open_private_btn": "💬 Open private chat",
        "group_alerts_disabled": "ℹ️ Price alerts and Pushover work only in private chat with the bot.",

        # PUSHOVER
        "pushover_usage": "ℹ️ <b>Setup Pushover:</b>\nSend your User Key: <code>/pushover u1234...</code>",
        "pushover_saved": "✅ <b>Pushover User Key successfully saved!</b>\n\n{text}",
        "push_test_tg_sent": "🔔 Test notification sent to Telegram!",
        "push_test_success_msg": "✅ Pushover works perfectly! Connection established.",
        "push_test_title": "Crypto Bot Test",
        "push_test_success_alert": "✅ Test push successfully sent to your phone!",
        "push_test_fail": "❌ Pushover error. Check your User Key and App Token.",
        "push_test_tg_only": "ℹ️ You are set to 'TG Only'. Change to 'TG + Pushover' in /settings.",
        "push_test_no_key": "❌ You haven't set a User Key. Use <code>/pushover [key]</code>.",
        "push_menu_title": "<b>Pushover Settings</b> 📲\n\nReceive loud push notifications on your phone.\n\n<b>Key Status:</b> {key_set}\n<b>Delivery:</b> {method}\n\n<i>💡 To update your User Key, send:\n<code>/pushover your_key</code></i>",
        "push_key_yes": "✅ Set",
        "push_key_no": "❌ Not set",
        "push_only_tg": "TG Only",
        "push_only_push": "Pushover Only",
        "push_both": "TG + Pushover",
        "push_sound_btn": "🔊 Sound ({sound})",
        "push_choose_sound": "<b>Choose sound for Pushover notifications:</b>",

        # CHART
        "chart_usage": "ℹ️ Please provide a coin. Example: <code>/chart btc</code>",
        "chart_generating": "⏳ Generating chart. Please wait...",
        "chart_error": "❌ Error generating chart. Check the ticker or try again later.",
        "chart_updating": "⏳ Updating...",
    },

    "uk": {
        # MENU & SETTINGS
        "menu_commands_btn": "📖 Команди",
        "menu_settings_btn": "⚙️ Налаштування",
        "settings_greeting": "⚙️ <b>Меню налаштувань</b>\n\nОберіть потрібний пункт нижче:",
        "menu_language_btn": "🌍 Мова",
        "menu_currencies_btn": "💱 Валюта",
        "menu_pushover_btn": "📲 Pushover",
        "menu_back_btn": "⬅️ Назад до налаштувань",
        "choose_language": "Оберіть мову / Choose your language / Выберите язык:",
        "lang_changed": "✅ Мову успішно змінено на Українську!",
        "choose_currency": "Виберіть валюту для відображення цін:",
        "cur_crypto_title": "— 💎 КРИПТОВАЛЮТИ —",
        "group_admin_only": "⚠️ Змінювати налаштування бота в групі можуть лише адміністратори.",
        "start_greeting": (
            "Привіт, <b>{name}</b>! 👋\n\n"
            "Я твій професійний крипто-помічник. Ось що я вмію:\n\n"
            "📊 <b>Ринок та Ціни:</b>\n"
            "• <code>/price btc</code> — Поточна ціна (або <code>/price 1.5 eth</code>).\n"
            "• <code>/chart btc</code> — Графік монети (свічки).\n"
            "• <code>/top 10</code> — Топ 10 росту (додай 'l' для падіння: <code>/top 5 l</code>).\n"
            "• <code>/funding btc</code> — Фандінг (хто кому платить).\n\n"
            "🔔 <b>Нагадування та Пуші:</b>\n"
            "• <code>/alert btc 65000</code> — Створити пуш-нагадування <i>(додай <code>repeat 10</code> для повтору кожні 10 секунд)</i>.\n"
            "• <code>/alerts</code> — Керування активними пушами.\n"
            "• <code>/pushover</code> — Налаштувати сповіщення на телефон.\n\n"
            "🔢 <i>Підказка: Надішли будь-який приклад (напр. <code>15*65000</code>), щоб використати калькулятор!</i>\n\n"
            "💡 <i>Віддаєш перевагу коротким командам? Натисни /shortcuts, щоб побачити всі скорочення!</i>"
        ),
        "commands_private": (
            "📖 <b>Доступні команди (Особистий чат)</b>\n\n"
            "• <code>/price [монета]</code> (<code>/p</code>) — Поточна ціна (напр. <code>/p 2.5 eth</code>)\n"
            "• <code>/chart [монета]</code> (<code>/c</code>) — Інтерактивний свічковий графік\n"
            "• <code>/top [1-50] [h/l]</code> (<code>/t</code>) — Топ росту або падіння за 24г\n"
            "• <code>/funding [монета]</code> (<code>/f</code>) — Ставка фінансування ф'ючерсів\n"
            "• <code>/cal [вираз]</code> — Калькулятор (працює і без команди)\n"
            "• <code>/alert [монета] [ціна] [r] [сек]</code> (<code>/a</code>) — Створити ціновий алерт\n"
            "• <code>/alerts</code> (<code>/as</code>) — Керування активними алертами\n"
            "• <code>/pushover [ключ]</code> — Налаштування пушів на телефон\n"
            "• <code>/testpush</code> — Тестове пуш-сповіщення\n"
            "• <code>/settings</code>, <code>/currency</code>, <code>/language</code> (<code>/l</code>) — Налаштування"
        ),
        "commands_group": (
            "📖 <b>Доступні команди (Груповий чат)</b>\n\n"
            "• <code>/price [монета]</code> (<code>/p</code>) — Поточна ціна\n"
            "• <code>/chart [монета]</code> (<code>/c</code>) — Інтерактивний свічковий графік\n"
            "• <code>/top [1-50] [h/l]</code> (<code>/t</code>) — Топ росту або падіння за 24г\n"
            "• <code>/funding [монета]</code> (<code>/f</code>) — Ставка фінансування ф'ючерсів\n"
            "• <code>/cal [вираз]</code> — Калькулятор\n"
            "• <code>/settings</code>, <code>/currency</code>, <code>/language</code> — Налаштування групи <i>(лише адміни)</i>\n\n"
            "<i>💡 Цінові алерти та Pushover працюють в особистих повідомленнях з ботом.</i>"
        ),

        # COMMAND USAGES & ERRORS
        "price_usage": "ℹ️ <b>Формат:</b> <code>/price [монета]</code>\nПриклад: <code>/price btc</code> або <code>/price 1.5 eth</code>",
        "price_invalid": "❌ Невірний формат або монету не знайдено.",
        "price_pieces": " шт.",

        "cal_usage": "ℹ️ <b>Формат:</b> <code>/cal [вираз]</code>\nПриклад: <code>/cal (1500 + 250) * 2</code>",
        "cal_invalid": "❌ Невірний математичний вираз.",

        "funding_usage": "ℹ️ <b>Формат:</b> <code>/funding [тікер]</code>\nПриклад: <code>/funding sol</code>",
        "funding_longs": "Лонги платять",
        "funding_shorts": "Шорти платять",
        "funding_error": "❌ Тільки спот або не знайдено",
        "funding_global_err": "❌ Помилка перевірки фандінгу.",

        "top_usage": "ℹ️ <b>Формат:</b> <code>/top [1-50] [h/l]</code>\nПриклади: <code>/top 10</code> (ріст), <code>/top 5 l</code> (падіння)",
        "top_limit_err": "❌ Ліміт має бути від 1 до 50.",
        "top_dir_err": "❌ Напрямок має бути <b>h</b> (ріст) або <b>l</b> (падіння).",
        "top_val_err": "❌ Ліміт має бути числом. Приклад: <code>/top 10</code>",
        "top_fetch_err": "❌ Не вдалося отримати дані з біржі.",
        "top_gainers": "Топ росту",
        "top_losers": "Топ падіння",
        "top_global_err": "❌ Помилка завантаження топу монет.",
        "top_status_msg": "⏳ Збираю дані з біржі...",

        "shortcuts_text": "⚡️ <b>Скорочення команд</b>\n\n• <code>/p</code> = <code>/price</code>\n• <code>/c</code> = <code>/chart</code>\n• <code>/t</code> = <code>/top</code>\n• <code>/f</code> = <code>/funding</code>\n• <code>/a</code> = <code>/alert</code>\n• <code>/l</code> = <code>/language</code>\n\n<i>Ти можеш використовувати ці короткі команди замість повних у будь-який час!</i>",

        # ALERTS
        "alert_usage": "ℹ️ <b>Формат:</b> <code>/alert [монета] [ціна]</code>\nПриклад: <code>/alert btc 65000</code>\n<i>(Додай <code>repeat 10</code> або <code>r 10</code> для повтору кожні 10с)</i>",
        "alert_invalid_fmt": "❌ Невірний формат. Приклад: <code>/alert btc 65000</code>",
        "alert_nan": "❌ Ціна має бути числом.",
        "alert_not_found": "❌ Монету {ticker} не знайдено.",
        "alert_api_err": "❌ Помилка з'єднання з біржею.",
        "alert_limit": "❌ Максимум 20 активних нагадувань.",
        "alert_created": "✅ <b>Нагадування створено!</b>\nМонета: <b>{ticker}</b>\nЦіль: <b>{target:g}</b> USDT{repeat}",
        "alert_repeat_sfx": " <b>(r {interval}с)</b>",
        "alert_not_exists": "Це нагадування вже не існує.",
        "alert_deleted_alert": "✅ Нагадування видалено!",
        "alert_turned_off": "\n\n<i>❌ Сповіщення вимкнено.</i>",
        "alerts_no_active": "У вас немає активних нагадувань.",
        "alerts_list_text": "Ось ваші активні нагадування. Натисніть на будь-яке, щоб видалити:",
        "alert_del_all_btn": "🗑 Видалити ВСІ",
        "alert_del_yes_btn": "✅ Так, видалити",
        "alert_del_no_btn": "❌ Ні, скасувати",
        "alert_del_confirm_text": "⚠️ <b>Видалити це нагадування?</b>\n\nМонета: <b>{symbol}</b>\nЦіль: <b>{target:g}</b> USDT{repeat}",
        "alert_del_all_yes_btn": "✅ Так, видалити ВСІ",
        "alert_del_all_confirm_text": "⚠️ <b>Чи дійсно ви хочете видалити ВСІ ваші нагадування?</b>",
        "alert_all_deleted_popup": "✅ Всі нагадування видалено!",
        "alert_all_deleted_text": "Усі активні нагадування успішно видалено.",
        "alert_triggered_up": "📈 зросла ВИЩЕ",
        "alert_triggered_down": "📉 впала НИЖЧЕ",
        "alert_triggered_msg": "🔔 <b>ПУШ-СПОВІЩЕННЯ</b> 🔔\n\nМонета <b>{symbol}</b> {dir_text} цілі <b>{target:g}</b> USDT!\nПоточна ціна: <b>{current:g}</b> USDT",
        "alert_repeat_msg": "\n<i>(🔄 Повтор кожні {interval}с)</i>",
        "alert_turn_off_btn": "🔕 Вимкнути це сповіщення",
        "open_private_btn": "💬 Відкрити особистий чат",
        "group_alerts_disabled": "ℹ️ Алерти та Pushover працюють лише в особистих повідомленнях з ботом.",

        # PUSHOVER
        "pushover_usage": "ℹ️ <b>Налаштування Pushover:</b>\nНадішліть свій User Key: <code>/pushover u1234...</code>",
        "pushover_saved": "✅ <b>Pushover User Key успішно збережено!</b>\n\n{text}",
        "push_test_tg_sent": "🔔 Тестове сповіщення в Telegram надіслано!",
        "push_test_success_msg": "✅ Pushover працює ідеально! Зв'язок з телефоном встановлено.",
        "push_test_title": "Тест Крипто-Бота",
        "push_test_success_alert": "✅ Тестовий пуш успішно відправлено на ваш телефон!",
        "push_test_fail": "❌ Помилка відправки в Pushover. Перевірте ваш User Key та App Token.",
        "push_test_tg_only": "ℹ️ У вас в налаштуваннях стоїть 'Тільки TG'. Змініть на 'TG + Pushover' в налаштуваннях.",
        "push_test_no_key": "❌ Ви не вказали свій User Key. Використайте <code>/pushover [ключ]</code>.",
        "push_menu_title": "<b>Налаштування Pushover</b> 📲\n\nДозволяє отримувати гучні пуш-сповіщення прямо на телефон.\n\n<b>Статус ключа:</b> {key_set}\n<b>Метод доставки:</b> {method}\n\n<i>💡 Щоб оновити свій User Key, надішліть:\n<code>/pushover ваш_ключ</code></i>",
        "push_key_yes": "✅ Встановлено",
        "push_key_no": "❌ Немає",
        "push_only_tg": "Тільки TG",
        "push_only_push": "Тільки Pushover",
        "push_both": "TG + Pushover",
        "push_sound_btn": "🔊 Звук ({sound})",
        "push_choose_sound": "<b>Оберіть звук для Pushover-сповіщень:</b>",

        # CHART
        "chart_usage": "ℹ️ Вкажи монету. Приклад: <code>/chart btc</code>",
        "chart_generating": "⏳ Будую графік. Зачекай...",
        "chart_error": "❌ Помилка побудови графіка. Перевір тікер або спробуй пізніше.",
        "chart_updating": "⏳ Оновлюю...",
    },

    "ru": {
        # MENU & SETTINGS
        "menu_commands_btn": "📖 Команды",
        "menu_settings_btn": "⚙️ Настройки",
        "settings_greeting": "⚙️ <b>Меню настроек</b>\n\nВыберите нужный пункт ниже:",
        "menu_language_btn": "🌍 Язык",
        "menu_currencies_btn": "💱 Валюта",
        "menu_pushover_btn": "📲 Pushover",
        "menu_back_btn": "⬅️ Назад к настройкам",
        "choose_language": "Выберите язык / Choose your language / Оберіть мову:",
        "lang_changed": "✅ Язык успешно изменен на Русский!",
        "choose_currency": "Выберите валюту для отображения цен:",
        "cur_crypto_title": "— 💎 КРИПТОВАЛЮТЫ —",
        "group_admin_only": "⚠️ Изменять настройки бота в группе могут только администраторы.",
        "start_greeting": (
            "Привет, <b>{name}</b>! 👋\n\n"
            "Я твой профессиональный крипто-помощник. Вот что я умею:\n\n"
            "📊 <b>Рынок и Цены:</b>\n"
            "• <code>/price btc</code> — Текущая цена (или <code>/price 1.5 eth</code>).\n"
            "• <code>/chart btc</code> — График монеты (свечи).\n"
            "• <code>/top 10</code> — Топ 10 роста (добавь 'l' для падения: <code>/top 5 l</code>).\n"
            "• <code>/funding btc</code> — Фандинг (кто кому платит).\n\n"
            "🔔 <b>Уведомления и Пуши:</b>\n"
            "• <code>/alert btc 65000</code> — Создать пуш-уведомление <i>(добавь <code>repeat 10</code> для повтора каждые 10 секунд)</i>.\n"
            "• <code>/alerts</code> — Управление активными пушами.\n"
            "• <code>/pushover</code> — Настроить уведомления на телефон.\n\n"
            "🔢 <i>Подсказка: Отправь любой пример (напр. <code>15*65000</code>), чтобы использовать калькулятор!</i>\n\n"
            "💡 <i>Предпочитаешь короткие команды? Нажми /shortcuts, чтобы увидеть все сокращения!</i>"
        ),
        "commands_private": (
            "📖 <b>Доступные команды (Личный чат)</b>\n\n"
            "• <code>/price [монета]</code> (<code>/p</code>) — Текущая цена (напр. <code>/p 2.5 eth</code>)\n"
            "• <code>/chart [монета]</code> (<code>/c</code>) — Интерактивный свечной график\n"
            "• <code>/top [1-50] [h/l]</code> (<code>/t</code>) — Топ роста или падения за 24ч\n"
            "• <code>/funding [монета]</code> (<code>/f</code>) — Ставка финансирования фьючерсов\n"
            "• <code>/cal [выражение]</code> — Калькулятор (работает и без команды)\n"
            "• <code>/alert [монета] [цена] [r] [сек]</code> (<code>/a</code>) — Создать ценовой алерт\n"
            "• <code>/alerts</code> (<code>/as</code>) — Управление активными алертами\n"
            "• <code>/pushover [ключ]</code> — Настройка пушей на телефон\n"
            "• <code>/testpush</code> — Тестовое пуш-уведомление\n"
            "• <code>/settings</code>, <code>/currency</code>, <code>/language</code> (<code>/l</code>) — Настройки"
        ),
        "commands_group": (
            "📖 <b>Доступные команды (Групповой чат)</b>\n\n"
            "• <code>/price [монета]</code> (<code>/p</code>) — Текущая цена\n"
            "• <code>/chart [монета]</code> (<code>/c</code>) — Интерактивный свечной график\n"
            "• <code>/top [1-50] [h/l]</code> (<code>/t</code>) — Топ роста или падения за 24ч\n"
            "• <code>/funding [монета]</code> (<code>/f</code>) — Ставка финансирования фьючерсов\n"
            "• <code>/cal [выражение]</code> — Калькулятор\n"
            "• <code>/settings</code>, <code>/currency</code>, <code>/language</code> — Настройки группы <i>(только админы)</i>\n\n"
            "<i>💡 Ценовые алерты и Pushover работают в личных сообщениях с ботом.</i>"
        ),

        # COMMAND USAGES & ERRORS
        "price_usage": "ℹ️ <b>Формат:</b> <code>/price [монета]</code>\nПример: <code>/price btc</code> или <code>/price 1.5 eth</code>",
        "price_invalid": "❌ Неверный формат или монета не найдена.",
        "price_pieces": " шт.",

        "cal_usage": "ℹ️ <b>Формат:</b> <code>/cal [выражение]</code>\nПример: <code>/cal (1500 + 250) * 2</code>",
        "cal_invalid": "❌ Неверное математическое выражение.",

        "funding_usage": "ℹ️ <b>Формат:</b> <code>/funding [тикер]</code>\nПример: <code>/funding sol</code>",
        "funding_longs": "Лонги платят",
        "funding_shorts": "Шорты платят",
        "funding_error": "❌ Только спот или не найдено",
        "funding_global_err": "❌ Ошибка проверки фандинга.",

        "top_usage": "ℹ️ <b>Формат:</b> <code>/top [1-50] [h/l]</code>\nПримеры: <code>/top 10</code> (рост), <code>/top 5 l</code> (падение)",
        "top_limit_err": "❌ Лимит должен быть от 1 до 50.",
        "top_dir_err": "❌ Направление должно быть <b>h</b> (рост) или <b>l</b> (падение).",
        "top_val_err": "❌ Лимит должен быть числом. Пример: <code>/top 10</code>",
        "top_fetch_err": "❌ Не удалось получить данные с биржи.",
        "top_gainers": "Топ роста",
        "top_losers": "Топ падения",
        "top_global_err": "❌ Ошибка загрузки топа монет.",
        "top_status_msg": "⏳ Собираю данные с биржи...",

        "shortcuts_text": "⚡️ <b>Сокращения команд</b>\n\n• <code>/p</code> = <code>/price</code>\n• <code>/c</code> = <code>/chart</code>\n• <code>/t</code> = <code>/top</code>\n• <code>/f</code> = <code>/funding</code>\n• <code>/a</code> = <code>/alert</code>\n• <code>/l</code> = <code>/language</code>\n\n<i>Ты можешь использовать эти короткие команды вместо полных в любое время!</i>",

        # ALERTS
        "alert_usage": "ℹ️ <b>Формат:</b> <code>/alert [монета] [цена]</code>\nПример: <code>/alert btc 65000</code>\n<i>(Добавь <code>repeat 10</code> или <code>r 10</code> для повтора каждые 10с)</i>",
        "alert_invalid_fmt": "❌ Неверный формат. Пример: <code>/alert btc 65000</code>",
        "alert_nan": "❌ Цена должна быть числом.",
        "alert_not_found": "❌ Монета {ticker} не найдена.",
        "alert_api_err": "❌ Ошибка соединения с биржей.",
        "alert_limit": "❌ Максимум 20 активных уведомлений.",
        "alert_created": "✅ <b>Уведомление создано!</b>\nМонета: <b>{ticker}</b>\nЦель: <b>{target:g}</b> USDT{repeat}",
        "alert_repeat_sfx": " <b>(r {interval}с)</b>",
        "alert_not_exists": "Это уведомление уже не существует.",
        "alert_deleted_alert": "✅ Уведомление удалено!",
        "alert_turned_off": "\n\n<i>❌ Уведомление выключено.</i>",
        "alerts_no_active": "У вас нет активных уведомлений.",
        "alerts_list_text": "Вот ваши активные уведомления. Нажмите на любое, чтобы удалить:",
        "alert_del_all_btn": "🗑 Удалить ВСЕ",
        "alert_del_yes_btn": "✅ Да, удалить",
        "alert_del_no_btn": "❌ Нет, отменить",
        "alert_del_confirm_text": "⚠️ <b>Удалить это уведомление?</b>\n\nМонета: <b>{symbol}</b>\nЦель: <b>{target:g}</b> USDT{repeat}",
        "alert_del_all_yes_btn": "✅ Да, удалить ВСЕ",
        "alert_del_all_confirm_text": "⚠️ <b>Вы действительно хотите удалить ВСЕ ваши уведомления?</b>",
        "alert_all_deleted_popup": "✅ Все уведомления удалены!",
        "alert_all_deleted_text": "Все активные уведомления успешно удалены.",
        "alert_triggered_up": "📈 выросла ВЫШЕ",
        "alert_triggered_down": "📉 упала НИЖЕ",
        "alert_triggered_msg": "🔔 <b>ПУШ-УВЕДОМЛЕНИЕ</b> 🔔\n\nМонета <b>{symbol}</b> {dir_text} цели <b>{target:g}</b> USDT!\nТекущая цена: <b>{current:g}</b> USDT",
        "alert_repeat_msg": "\n<i>(🔄 Повтор каждые {interval}с)</i>",
        "alert_turn_off_btn": "🔕 Отключить это уведомление",
        "open_private_btn": "💬 Открыть личный чат",
        "group_alerts_disabled": "ℹ️ Алерты и Pushover работают только в личных сообщениях с ботом.",

        # PUSHOVER
        "pushover_usage": "ℹ️ <b>Настройка Pushover:</b>\nОтправьте свой User Key: <code>/pushover u1234...</code>",
        "pushover_saved": "✅ <b>Pushover User Key успешно сохранен!</b>\n\n{text}",
        "push_test_tg_sent": "🔔 Тестовое уведомление в Telegram отправлено!",
        "push_test_success_msg": "✅ Pushover работает идеально! Связь с телефоном установлена.",
        "push_test_title": "Тест Крипто-Бота",
        "push_test_success_alert": "✅ Тестовый пуш успешно отправлен на ваш телефон!",
        "push_test_fail": "❌ Ошибка отправки в Pushover. Проверьте ваш User Key и App Token.",
        "push_test_tg_only": "ℹ️ У вас в настройках стоит 'Только TG'. Измените на 'TG + Pushover' в настройках.",
        "push_test_no_key": "❌ Вы не указали свой User Key. Используйте <code>/pushover [ключ]</code>.",
        "push_menu_title": "<b>Настройки Pushover</b> 📲\n\nПозволяет получать громкие уведомления на телефон.\n\n<b>Статус ключа:</b> {key_set}\n<b>Метод доставки:</b> {method}\n\n<i>💡 Чтобы обновить User Key, отправьте:\n<code>/pushover ваш_ключ</code></i>",
        "push_key_yes": "✅ Установлен",
        "push_key_no": "❌ Нет",
        "push_only_tg": "Только TG",
        "push_only_push": "Только Pushover",
        "push_both": "TG + Pushover",
        "push_sound_btn": "🔊 Звук ({sound})",
        "push_choose_sound": "<b>Выберите звук для Pushover:</b>",

        # CHART
        "chart_usage": "ℹ️ Укажи монету. Пример: <code>/chart btc</code>",
        "chart_generating": "⏳ Строю график. Подожди...",
        "chart_error": "❌ Ошибка построения графика. Проверь тикер или попробуй позже.",
        "chart_updating": "⏳ Обновляю...",
    },
}


def get_text(user_id: int, key: str, **kwargs) -> str:
    """Retrieves the localized text string for a specific user, falling back to English."""
    user = db.get_user(user_id)
    lang = user.get("language", "en")

    if lang not in TRANSLATIONS:
        lang = "en"

    text = TRANSLATIONS[lang].get(key, TRANSLATIONS["en"].get(key, key))

    if kwargs:
        return text.format(**kwargs)
    return text