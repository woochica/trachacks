= План работ в Trac =
[[TracGuideToc]]

План работ это представление [wiki:TracTickets подсистемы билетов], которое облегчает планирование и управление будущим развитием проекта.
{{{#!comment
The roadmap provides a view on the [wiki:TracTickets ticket system] that helps planning and managing the future development of a project.
}}}

== Просмотр плана ==

По сути, план работ это просто перечень будущих этапов. К этапам можно добавлять описания (используя [WikiFormatting разметку wiki]), например формулирующие основные цели. В дополнение, билеты, назначенные на этап, группируются и соотношение открытых и решенных билетов отображается в виде полосы прогресса. Можно еще [trac:TracRoadmapCustomGroups настроить группировку под свои нужды] и получить полосу прогресса с дополнительными состояниями билетов.
{{{#!comment
Basically, the roadmap is just a list of future milestones. You can add a description to milestones (using WikiFormatting) describing main objectives, for example. In addition, tickets targeted for a milestone are aggregated, and the ratio between active and resolved tickets is displayed as a milestone progress bar.  It is possible to further [trac:TracRoadmapCustomGroups customise the ticket grouping] and have multiple ticket statuses shown on the progress bar.
}}}

План можно фильтровать для показа или скрытия ''завершенных этапов'' и ''этапов без даты завершения''. В случае выбора одновременно ''показать завершенные этапы'' и ''скрыть этапы без даты завершения'', ''завершенные'' этапы без даты завершения __будут__ отображены.
{{{#!comment
The roadmap can be filtered to show or hide ''completed milestones'' and ''milestones with no due date''. In the case that both ''show completed milestones'' and ''hide milestones with no due date'' are selected, ''completed'' milestones with no due date __will__ be shown.
}}}

== Просмотр этапа ==

{{{#!comment
К каждому этапу можно добавить описание (используя [WikiFormatting разметку wiki]), например формулирующее основные цели. 
You can add a description for each milestone (using WikiFormatting) describing main objectives, for example. In addition, tickets targeted for a milestone are aggregated, and the ratio between active and resolved tickets is displayed as a milestone progress bar.  It is possible to further [trac:TracRoadmapCustomGroups customise the ticket grouping] and have multiple ticket statuses shown on the progress bar.
}}}

Описанную выше простую статистику этапа, предоставляемую планом работ, можно детализировать. Для просмотра страницы этапа щелкните на его названии. По умолчанию соотношение активные/решенные группируется и отображается по компонентам. Можно также перегруппировать состояние по другим критериям, таким как владелец или важность. Количества билетов ссылаются на [wiki:TracQuery произвольные запросы], которые показывают соответствующие билеты.
{{{#!comment
It is possible to drill down into this simple statistic by viewing the individual milestone pages. By default, the active/resolved ratio will be grouped and displayed by component. You can also regroup the status by other criteria, such as ticket owner or severity. Ticket numbers are linked to [wiki:TracQuery custom queries] listing corresponding tickets.
}}}

== Администрирование Плана ==

Имея соответствующие разрешения, можно добавлять, изменять и удалять этапы с помощью web-интерфейса (страницы плана и этапов), интерфейса администрирования или используя `trac-admin`.

'''Замечание:''' на текущий момент нельзя изменять описания этапов с помощью 'trac-admin'.

== Поддержка iCalendar ==

План работ поддерживает формат [http://www.ietf.org/rfc/rfc2445.txt iCalendar] для отслеживания запланированных этапов и связанных билетов из любимой программы календаря. Большинство программ календарей поддерживают спецификацию iCalendar, в том числе
 * [http://www.apple.com/ical/ Apple iCal] для Mac OS X
 * кроссплатформенный [http://www.mozilla.org/projects/calendar/ календарь Mozilla]
 * [http://chandlerproject.org Chandler]
 * [http://kontact.kde.org/korganizer/ Korganizer] (программа календарь из проекта [http://www.kde.org/ KDE])
 * [http://www.novell.com/de-de/products/desktop/features/evolution.html Evolution] тоже поддерживает iCalendar
 * [http://office.microsoft.com/en-us/outlook/ Microsoft Outlook] также может читать файлы iCalendar (это возможно в новом статическом календаре Outlook)

Чтобы подписаться на план работ, скопируйте ссылку iCalendar (она находится внизу страницы), выберите действие "Подписаться на календарь в сети" (или подобное) в вашей программе календаря и вставьте скопированный URL.

'''Замечание:''' чтобы билеты были включены в календарь в виде задач, вам нужно войти в систему, прежде чем копировать ссылку. Вы увидите только билеты, назначенные вам и включенные в этап.
{{{#!comment
'''Note:''' For tickets to be included in the calendar as tasks, you need to be logged in when copying the link. You will only see tickets assigned to yourself, and associated with a milestone.
}}}

Больше информации про iCalendar вы найдете в [http://en.wikipedia.org/wiki/ICalendar Википедии].

----
См. также: TracTickets, TracReports, TracQuery, [trac:TracRoadmapCustomGroups TracRoadmapCustomGroups]
