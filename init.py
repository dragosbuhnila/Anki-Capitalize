from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo
from aqt.browser import Browser
from anki.hooks import wrap  # Import wrap to fix the error
import re

MODES = ["All words (Title Case)", "First letter only"]

def capitalize_all_words(text: str) -> str:
    def cap(m):
        s = m.group(0)
        return s[0].upper() + s[1:].lower() if len(s) > 1 else s.upper()
    return re.sub(r"\w[\w'\-]*", cap, text, flags=re.UNICODE)

def capitalize_first_letter(text: str) -> str:
    m = re.search(r"\w", text, flags=re.UNICODE)
    if not m:
        return text
    i = m.start()
    return text[:i] + text[i].upper() + text[i+1:]

class FieldModeDialog(QDialog):
    def __init__(self, parent, field_names):
        super().__init__(parent)
        self.setWindowTitle("Capitalize Fields")
        self.resize(480, 320)
        self.field_names = sorted(field_names)

        layout = QVBoxLayout()
        self.setLayout(layout)

        label = QLabel("Select fields to update and choose capitalization mode for each:")
        layout.addWidget(label)

        self.table = QTreeWidget()
        self.table.setColumnCount(2)
        self.table.setHeaderLabels(["Field", "Mode"])
        self.table.setRootIsDecorated(False)
        layout.addWidget(self.table)

        for fname in self.field_names:
            item = QTreeWidgetItem(self.table)
            item.setText(0, fname)
            item.setCheckState(0, Qt.Unchecked)
            combo = QComboBox()
            combo.addItems(MODES)
            combo.setCurrentIndex(0)  # default: All words
            self.table.setItemWidget(item, 1, combo)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def selected_field_modes(self):
        out = {}
        for i in range(self.table.topLevelItemCount()):
            item = self.table.topLevelItem(i)
            if item.checkState(0) == Qt.Checked:
                fname = item.text(0)
                combo = self.table.itemWidget(item, 1)
                mode_index = combo.currentIndex()
                out[fname] = mode_index
        return out

def run_capitalize_from_browser(browser):
    if not hasattr(browser, "selectedNotes"):
        showInfo("Please open the Browser and select one or more notes.")
        return

    note_ids = browser.selectedNotes()
    if not note_ids:
        showInfo("No notes selected. Select notes in the Browser first.")
        return

    # collect union of field names across selected notes
    names = set()
    for nid in note_ids:
        try:
            n = mw.col.getNote(nid)
            model_fields = [f["name"] for f in n.model()["flds"]]
            names.update(model_fields)
        except Exception:
            continue

    if not names:
        showInfo("No fields found on selected notes.")
        return

    dlg = FieldModeDialog(browser, names)
    if not dlg.exec_():
        return

    field_modes = dlg.selected_field_modes()
    if not field_modes:
        showInfo("No fields selected.")
        return

    changed = 0
    mw.progress.start(parent=browser, label="Capitalizing fields...", immediate=True)
    try:
        for nid in note_ids:
            note = mw.col.getNote(nid)
            model_fields = [f["name"] for f in note.model()["flds"]]
            updated = False
            for fname, mode in field_modes.items():
                if fname not in model_fields:
                    continue
                idx = model_fields.index(fname)
                old = note.fields[idx] or ""
                if mode == 0:
                    new = capitalize_all_words(old)
                else:
                    new = capitalize_first_letter(old)
                if new != old:
                    note.fields[idx] = new
                    updated = True
            if updated:
                mw.col.update_note(note)
                changed += 1
    finally:
        mw.progress.finish()
    
    if changed:
        mw.checkpoint("Capitalize fields")

    try:
        browser.onSearch()
    except Exception:
        pass

    showInfo(f"Updated {changed} notes (fields changed).")

# Add the action to the Browser's Edit menu
def on_browser_will_show_context_menu(browser):
    action = QAction("Capitalize Fields...", browser)
    action.triggered.connect(lambda: run_capitalize_from_browser(browser))
    browser.form.menuEdit.addAction(action)

# Hook into the Browser
Browser.setupMenus = wrap(Browser.setupMenus, on_browser_will_show_context_menu, "after")