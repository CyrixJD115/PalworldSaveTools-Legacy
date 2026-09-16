import os
import subprocess
import sys
from pathlib import Path

from tests.dynamic_importer import import_from

constants = import_from('palworld_aio.constants')

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _run_isolated(script, timeout=90):
    env = os.environ.copy()
    env['PYTHONPATH'] = os.pathsep.join(
        [
            str(PROJECT_ROOT / 'src' / 'palsav'),
            str(PROJECT_ROOT / 'src'),
            env.get('PYTHONPATH', ''),
        ]
    )
    return subprocess.run(
        [sys.executable, '-c', script],
        capture_output=True,
        text=True,
        check=False,
        cwd=PROJECT_ROOT,
        env=env,
        timeout=timeout,
    )


def test_repo_links_point_to_legacy_fork():
    urls = (
        constants.GIT_REPO_URL,
        constants.GITHUB_RAW_URL,
        constants.GITHUB_URL,
    )
    for url in urls:
        assert 'CyrixJD115/PalworldSaveTools-Legacy' in url, url
        assert 'deafdudecomputers' not in url, url


def test_update_logic_stays_on_the_original_repo_for_the_final_update():
    # 2.4.4 builds must still find the last release: it publishes on the original repo.
    for url in (constants.STABLE_VERSION_URL, constants.RELEASE_DOWNLOAD_URL):
        assert 'deafdudecomputers/PalworldSaveTools' in url, url
        assert 'PalworldSaveTools-Legacy' not in url, url


def test_builtin_announcement_names_the_successor_and_its_links():
    notice = import_from('palworld_aio.notice')
    html = notice.ANNOUNCEMENT_HTML
    assert 'DISCONTINUED' in html
    assert 'PalStudio' in html
    for url in (
        constants.PALSTUDIO_SITE_URL,
        constants.PALSTUDIO_DISCORD_URL,
        constants.PALSTUDIO_NEXUS_URL,
    ):
        assert f'href="{url}"' in html, url
    assert '</a>' in html, 'links are not clickable'


def test_announcement_computes_its_links_offline():
    notice = import_from('palworld_aio.notice')
    assert 'palworldsavepal.app' in notice._link('https://www.palworldsavepal.app/')
    assert constants.PALSTUDIO_DISCORD_URL.removeprefix('https://') in notice._link(constants.PALSTUDIO_DISCORD_URL)


def test_palstudio_chip_sits_left_of_discord_and_opens_all_links():
    result = _run_isolated("""
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

import palworld_aio.constants as constants
from i18n import init_language
init_language('en_US')
from PySide6.QtWidgets import QApplication
from unittest import mock

app = QApplication([])

from palworld_aio.ui.chrome.header_widget import HeaderWidget

header = HeaderWidget()
header.resize(800, 40)
header.show()
app.processEvents()

assert header.palstudio_btn.text() == 'PalStudio', header.palstudio_btn.text()
assert header.palstudio_btn.x() + header.palstudio_btn.width() <= header.discord_btn.x(), \\
    'PalStudio chip must sit left of the Discord chip'

menu = header._build_palstudio_menu()
actions = menu.actions()
expected = [
    ('Website', constants.PALSTUDIO_SITE_URL),
    ('Discord', constants.PALSTUDIO_DISCORD_URL),
    ('Nexus Mods', constants.PALSTUDIO_NEXUS_URL),
]
assert [(a.text(), a.data()) for a in actions] == expected, \\
    [(a.text(), a.data()) for a in actions]

opened = []
with mock.patch('webbrowser.open', side_effect=lambda u: opened.append(u) or u):
    for action in actions:
        action.trigger()

assert opened == [url for _, url in expected], opened
""", timeout=90)
    assert result.returncode == 0, result.stderr


def test_notice_popup_renders_and_remembers_dismissal():
    result = _run_isolated("""
import os
import tempfile
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

app = QApplication([])

import palworld_aio.notice as notice

cfg_path = os.path.join(tempfile.mkdtemp(), 'user.cfg')
notice._user_cfg_path = lambda: cfg_path

state = {}


def probe():
    box = app.activeModalWidget()
    if box is not None:
        state['title'] = box.windowTitle()
        state['text'] = box.text()
        state['has_checkbox'] = box.checkBox() is not None
        box.checkBox().setChecked(True)
        box.accept()


QTimer.singleShot(3000, probe)
shown = notice.show_discontinuation_notice()
app.processEvents()

assert shown is True, 'popup was skipped on a fresh config'
assert state, 'popup never appeared'
assert state['title'], 'popup has no title'
assert state['has_checkbox'], 'popup is missing the dismissal checkbox'
assert 'DISCONTINUED' in state['text'], state['text']
assert 'PalStudio' in state['text'], state['text']
assert '<a href=' in state['text'], 'notice links are not clickable'
assert notice.is_notice_dismissed() is True, 'dismissal choice was not persisted'
assert notice.show_discontinuation_notice() is False, 'popup reappeared after dismissal'
""", timeout=60)
    assert result.returncode == 0, result.stderr


def test_notice_popup_is_shown_before_the_main_window_opens():
    source = (PROJECT_ROOT / 'src' / 'palworld_aio' / 'main.py').read_text(encoding='utf-8')
    notice_at = source.index('show_discontinuation_notice()')
    window_at = source.index('window = MainWindow()')
    assert notice_at < window_at, 'the popup must appear before the main tool window opens'


def test_startup_shows_popup_then_opens_the_main_window_after_dismissal():
    result = _run_isolated("""
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

app = QApplication([])

import palworld_aio.notice as notice
notice.is_notice_dismissed = lambda: False
notice.persist_dismissed = lambda value: None  # keep the real user config untouched

import palworld_aio.main as main_mod

events = []
original_window = main_mod.MainWindow


def window_factory():
    events.append(app.activeModalWidget() is not None)
    return original_window()


main_mod.MainWindow = window_factory
state = {}


def dismiss_popup():
    box = app.activeModalWidget()
    state['popup_shown'] = box is not None and 'DISCONTINUED' in box.text()
    state['window_created_before_dismissal'] = bool(events)
    if box is not None:
        box.accept()


def finish():
    state['window_created_after_dismissal'] = bool(events)
    app.quit()


QTimer.singleShot(2000, dismiss_popup)
QTimer.singleShot(6000, finish)

try:
    main_mod.run_aio()
except SystemExit:
    pass

assert state.get('popup_shown'), 'no discontinuation popup on startup'
assert state.get('window_created_before_dismissal') is False, \
    'the main window opened before the popup was dismissed'
assert state.get('window_created_after_dismissal'), \
    'the main window never opened after the popup was dismissed'
""", timeout=90)
    assert result.returncode == 0, result.stderr