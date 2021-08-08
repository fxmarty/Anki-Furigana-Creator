from anki.hooks import addHook
import os.path
import json
import re

import requests
import urllib.parse

from bs4 import BeautifulSoup

from aqt.qt import *
from aqt import mw


def yieldFurigana(word):
    """
    Returns `word` with inserted furigana in brackets
    """
    try:
        r = requests.get('https://jisho.org/word/' + urllib.parse.quote(word))
        soup = BeautifulSoup(r.text, "html.parser")

    except Exception as e:
        print(e)
        return word

    furigana_data = soup.find_all("span", {"class": "furigana"})

    if len(furigana_data) == 0:
        return word

    if len(furigana_data[0]) < 3:
        return word

    furigana_useful_data = furigana_data[0].contents

    del(furigana_useful_data[-1])
    del(furigana_useful_data[0])

    assert len(furigana_useful_data) == len(word)

    res = ''
    character_index = 0
    n = len(word)

    furigana_placement_index = -1
    displaced = False
    for i in range(n - 1, -1, -1):
        possible_furigana = furigana_useful_data[i].contents

        # if is kanji
        if word[i] >= u'\u4e00' and word[i] <= u'\u9faf':
            # no furigana
            if possible_furigana == []:
                # first kanji to the right with no furigana, place it on top once
                # the furigana has been found further to the left
                if furigana_placement_index == -1:
                    furigana_placement_index = i
                    displaced = True
            else:
                if displaced is True:
                    res = (word[i:furigana_placement_index + 1] + '['
                           + possible_furigana[0] + ']' + res)
                else:
                    if i == 0:
                        res = word[i] + '[' + possible_furigana[0] + ']' + res
                    else:  # need an additional space
                        res = ' ' + word[i] + '[' + possible_furigana[0] + ']' + res

                displaced = False  # reset
                furigana_placement_index = -1  # reset
        else:
            res = word[i] + res

    return res


def gc(arg, fail=False):
    return mw.addonManager.getConfig(__name__).get(arg, fail)


def addFurigana(editor):
    selection = editor.web.selectedText()

    # this is rather solw and sometimes wrong, I did not find a solution
    current = editor.note.fields[editor.currentField]

    if not selection:
        return

    editor.web.setFocus()
    field = editor.currentField
    editor.web.eval("focusField(%d);" % field)

    before = re.findall('.*(?=' + selection + ')', current)
    after = re.findall('(?<=' + selection + ').*', current)

    if len(before) >= 1 and len(after) >= 1:
        editor.note.fields[editor.currentField] = before[0] + yieldFurigana(selection) + after[0]

    editor.loadNote()
    # focus the field, so that changes are saved
    # this causes the cursor to go to the end of the field
    editor.web.setFocus()
    field = editor.currentField
    editor.web.eval("focusField(%d);" % field)


def setupEditorButtonsFilter(buttons, editor):
    key = QKeySequence(gc('Key_insert_furigana'))
    keyStr = key.toString(QKeySequence.NativeText)
    if gc('Key_insert_furigana'):
        b = editor.addButton(
            os.path.join(os.path.dirname(__file__), "icons", "furigana.png"),
            "button_add_furigana",
            addFurigana,
            tip="Insert furigana ({})".format(keyStr),
            keys=gc('Key_insert_furigana')
            )
        buttons.append(b)
    return buttons

addHook("setupEditorButtons", setupEditorButtonsFilter)