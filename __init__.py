from anki.hooks import addHook
import os.path
import json
import re

import requests
import urllib.parse
import urllib.request    

from aqt.qt import * 
from aqt import mw

def yieldFurigana(motKanji): #return motKanji with furigana added to the string
    try:
        urllib.request.urlretrieve("https://jisho.org/word/" + urllib.parse.quote(motKanji), "tempo.txt")

    except Exception as e:
        print("Error 404")
        return motKanji
        
    with open('tempo.txt') as f:
        L = f.readlines()[574:575]
    
    furigana = re.findall('(?<=i">)[^</spa]*', L[0])
    res = motKanji
    i = 0
    while furigana != [] and i < len(res):
        if res[i] >= u'\u4e00' and res[i] <= u'\u9faf':
            res = res[0:i] + '<ruby>' + res[i] + '<rt>' + furigana[0] + '</rt></ruby>' + res[i+1:]
            i = i + 23 + len(furigana[0])
            furigana.pop(0)
        else:
            i = i + 1
    if res[0] == " ":
        return res[1:]
    else:
        return res

def gc(arg, fail=False):
    return mw.addonManager.getConfig(__name__).get(arg, fail)

def addFurigana(editor):
    selection = editor.web.selectedText()
    current = editor.note.fields[editor.currentField]
    if not selection:
        return
    
    editor.web.setFocus()
    field = editor.currentField
    editor.web.eval("focusField(%d);" % field)
    
    before = re.findall('.*(?=' + selection + ')',current)
    after = re.findall('(?<=' + selection + ').*',current)
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
