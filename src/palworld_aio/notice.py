import os
from urllib.parse import urlparse

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QMessageBox

from i18n import t
from palworld_aio import constants


def _link(url):
    host = urlparse(url).netloc.removeprefix('www.')
    return f'<a href="{url}" style="color: #4a90e2;">{host}</a>'


ANNOUNCEMENT_HTML = f'''<h2 style="color: #4a90e2; margin: 0 0 8px 0;">PALWORLD SAVE TOOLS - DISCONTINUED</h2>
<p style="margin: 0 0 8px 0;"><b>Version 2.4.5 is the final release.</b> The project is outdated and several features
are broken because Palworld has moved past what this version supports. Continued use is no longer recommended.</p>
<p style="margin: 0 0 8px 0;">It was originally started by <b>Pylar</b>, but things came up for him and he has since moved on. PST has been merged
into the successor toolkit <b>PalStudio</b> (formerly Palworld Save Pal), which combines PST and Palworld Save Pal
into one modern, maintained tool.</p>
<p style="margin: 0 0 8px 0;">The outdated codebase lives on as a legacy project at
<a href="https://github.com/CyrixJD115/PalworldSaveTools-Legacy" style="color: #4a90e2;">PalworldSaveTools-Legacy</a>,
under Cyrix, originally Pylar's co-partner, who took it over and keeps it as an outdated archive that now serves as
a learning resource for how save editing works. PalStudio is still the better option.</p>
<ul style="margin: 0 0 8px 0;">
<li>Website: {_link(constants.PALSTUDIO_SITE_URL)}</li>
<li>Discord: {_link(constants.PALSTUDIO_DISCORD_URL)}</li>
<li>Nexus: {_link(constants.PALSTUDIO_NEXUS_URL)}</li>
</ul>
<p style="margin: 0;">Thank you to everyone who used and supported Palworld Save Tools. See you on the PalStudio Discord.</p>'''


def _user_cfg_path():
    from boot_paths import CONFIG_DIR, USER_CONFIG_DIR
    path = str(USER_CONFIG_DIR / 'user.cfg')
    if not os.path.exists(path):
        path = os.path.join(str(CONFIG_DIR), 'user.cfg')
    return path


def is_notice_dismissed():
    try:
        from palsav import json_tools
        path = _user_cfg_path()
        if os.path.exists(path):
            data = json_tools.load(path)
            return bool(data.get('announcement_dismissed', False))
    except Exception as e:
        print(f'Failed to read announcement setting: {e}')
    return False


def persist_dismissed(value):
    try:
        from palsav import json_tools
        path = _user_cfg_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = json_tools.load(path) if os.path.exists(path) else {}
        data['announcement_dismissed'] = value
        json_tools.dump(data, path, indent=2)
    except Exception as e:
        print(f'Failed to save announcement setting: {e}')


def show_discontinuation_notice():
    """Show the discontinuation popup before the main tool window opens.

    Blocks until the user dismisses it. Returns True if the popup was shown
    (even if only to be closed), False when skipped because of a prior
    "Don't show this announcement again" choice.
    """
    if is_notice_dismissed():
        return False
    box = QMessageBox()
    box.setWindowFlags(Qt.Dialog | Qt.WindowType.Window | Qt.WindowStaysOnTopHint)
    box.setWindowModality(Qt.ApplicationModal)
    box.setIcon(QMessageBox.Information)
    box.setWindowTitle(t('notice.dlg_title') if t else 'Palworld Save Tools - Discontinued')
    box.setTextFormat(Qt.RichText)
    box.setText(ANNOUNCEMENT_HTML)
    box.setMinimumWidth(520)
    dont_again = QCheckBox(t('notice.dont_show_again') if t else "Don't show this announcement again")
    box.setCheckBox(dont_again)
    ok_btn = box.addButton(t('button.ok') if t else 'OK', QMessageBox.AcceptRole)
    box.setDefaultButton(ok_btn)
    box.exec()
    if dont_again.isChecked():
        persist_dismissed(True)
    return True
