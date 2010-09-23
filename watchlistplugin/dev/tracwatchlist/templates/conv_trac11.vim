
:%s/<i18n:choose\s\+numeral="\([^\"]\+\)" params="[^\"]*">/<py:choose test="\1">/
:%s/<\/i18n:choose>/<\/py:choose>/
:%s/i18n:singular=""/py:when="1"/
:%s/i18n:plural=""/py:otherwise=""/

