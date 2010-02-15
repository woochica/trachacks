= TracAdmin =

[[TracGuideToc]]

Вместе с Trac поставляется мощный консольный инструмент конфигурирования. Его можно использовать для настройки Trac для ваших нужд.

Некоторые из этих операций также могут быть выполнены через веб-интерфейс ''Admin'', и обновленная версия дополнения [http://trac.edgewall.org/wiki/WebAdmin WebAdmin] в настоящее время (начиная с версии 0.11) встроена в Trac.

== Использование ==

Вы можете получить исчерпывающий список доступных опций, команд и подкоманд по вызову `trac-admin` с командой `help`:

{{{
trac-admin help
}}}

За исключением использования подкоманд `help`, `about` или `version`, вам необходимо прописать путь к рабочему окружению Trac (TracEnviroment), которое вы администрируете. Например:

{{{
trac-admin /path/to/projenv wiki list
}}}

== Интерактивный режим ==

Если указать только путь к окружению, `trac-admin` запустится в интерактивном режиме. Команды могут быть выполнены в выбранном окружении с помощью командной оболочки, которая поддерживает автозавершение команд по клавише tab (в не-Windows окружении, и когда модуль `readline` Python доступен) и автоматическое повторение последней команды. Находясь в интерактивном режиме, вы можете также получить справку по специфическим командам или подмножествам команд. Например, чтобы получить пояснение к команде `resync`, наберите:

{{{
> help resync
}}}

Чтобы получить справку по командам wiki, наберите:

{{{
> help wiki
}}}

== Полный список команд ==

{{{
help
-- Показать документацию

initenv
-- Интерактивно создать и инициализировать новое рабочее окружение.

initenv <projectname> <db> <repostype> <repospath>
-- Создать и инициализировать новое рабочее окружение по аргументам.

hotcopy <backupdir>
-- Сделать "горячий" бэкап окружения

resync
-- Синхронизировать trac с репозиторием

resync <rev>
-- Синхронизировать только ревизию <rev>

upgrade
-- Обновить базу данных до текущей версии

deploy <directory>
-- Извлечь статические ресурсы из Trac и всех плагинов

permission list [user]
-- Список правил доступа

permission add <user> <action> [action] [...]
-- Добавить новое правило доступа

permission remove <user> <action> [action] [...]
-- Удалить правило доступа

wiki list
-- Список страниц wiki

wiki remove <page>
-- Удалить страницу wiki

wiki export <page> [file]
-- Экспортировать страницу wiki page в файл или stdout

wiki import <page> [file]
-- Импортировать страницу wiki из файла или stdin

wiki dump <directory>
-- Экспортировать все страницы wiki в файлы, именованные по title

wiki load <directory>
-- Импортировать все страницы wiki из директории

wiki upgrade
-- Обновить страницы wiki по умолчанию до текущей версии

ticket remove <number>
-- Удалить билет

ticket_type list
-- Показать список возможных типов билетов

ticket_type add <value>
-- Добавить тип билета

ticket_type change <value> <newvalue>
-- Изменить тип билета

ticket_type remove <value>
-- Удалить тип билета

ticket_type order <value> up|down
-- Переместить тип билета вверх или вниз по списку

priority list
-- Показать возможные приоритеты билетов

priority add <value>
-- Добавить значение приоритета

priority change <value> <newvalue>
-- Изменить значение приоритета

priority remove <value>
-- Удалить значение приоритета

priority order <value> up|down
-- Переместить значение приоритета вверх или вниз в списке

severity list
-- Показать возможные значения важности билетов

severity add <value>
-- Добавить значение важности билета

severity change <value> <newvalue>
-- Изменить значение важности

severity remove <value>
-- Удалить значение важности

severity order <value> up|down
-- Переместить значение важности вверх или вниз по списку

component list
-- Показать доступные компоненты

component add <name> <owner>
-- Добавить новый компонент

component rename <name> <newname>
-- Переименовать компонент

component remove <name>
-- Удалить компонент

component chown <name> <owner>
-- Изменить владельца компонента

version list
-- Показать список версий

version add <name> [time]
-- Добавить версию

version rename <name> <newname>
-- Переименовать версию

version time <name> <time>
-- Установить время версии (Формат: "YYYY-MM-DD", "now" или "")

version remove <name>
-- Удалить версию

milestone list
-- Показать этапы

milestone add <name> [due]
-- Добавить этап

milestone rename <name> <newname>
-- Переименовать этап

milestone due <name> <due>
-- Установить запланированную дату окончания этапа (Формат: "YYYY-MM-DD", "now" или "")

milestone completed <name> <completed>
-- Установить фактическую дату окончания этапа (Формат: "YYYY-MM-DD", "now" или "")

milestone remove <name>
-- Удалить этап

resolution list
-- Показать список причин, по которым может быть закрыт билет

resolution add <value>
-- Добавить возможную причину, по которой может быть закрыт билет

resolution change <value> <newvalue>
-- Изменить значение возможной причины, по которой может быть закрыт билет

resolution remove <value>
-- Удалить возможную причину, по которой может быть закрыт билет

resolution order <value> up|down
-- Переместить причину закрытия билета вверх или вних по списку
}}}

=== Замечания ===

`initenv` также поддерживает дополнительнуй опцию `--inherit`, которую можно использовать для задания опции `[inherit] file` во время создания среды, так, что в файл conf/trac.ini новой среды будут записаны только опции, которые еще "не" заданы в файле глобальной конфигурации.

См. TracIni#GlobalConfiguration

Обратите внимание, что в версии Trac 0.11 `initenv` потеряла дополнительный последний аргумент `<templatepath>`, который использовался в предыдущих версиях для указания на папку `templates`. Если в этом случае вы используете однострочную команду '`trac-admin /path/to/trac/ initenv <projectname> <db> <repostype> <repospath>`' и получаете ошибку ''''`Wrong number of arguments to initenv: 4`'''', то это потому, что вы используете скрипт `trac-admin` из старой версии Trac.

----

См. также: TracGuide, TracBackup, TracPermissions, TracEnvironment, TracIni, [trac:TracMigrate TracMigrate]