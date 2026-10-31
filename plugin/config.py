from qt.core import QCheckBox, QComboBox, QFormLayout, QLineEdit, QSpinBox, QWidget

from calibre.utils.config import JSONConfig

prefs = JSONConfig('plugins/wakatime')
prefs.defaults['enabled'] = True
prefs.defaults['idle_timeout_min'] = 5
prefs.defaults['heartbeat_interval_s'] = 120
prefs.defaults['category'] = 'learning'
prefs.defaults['project_mode'] = 'library'  # 'library' | 'fixed'
prefs.defaults['fixed_project'] = ''
prefs.defaults['hide_titles'] = False
prefs.defaults['cli_path'] = ''

CATEGORIES = ('learning', 'researching')


def get_cfg() -> dict:
    return {k: prefs[k] for k in prefs.defaults}


class ConfigWidget(QWidget):
    def __init__(self):
        super().__init__()
        form = QFormLayout(self)

        self.enabled = QCheckBox('Track reading time')
        self.enabled.setChecked(prefs['enabled'])
        form.addRow(self.enabled)

        self.idle = QSpinBox()
        self.idle.setRange(1, 14)
        self.idle.setSuffix(' min')
        self.idle.setValue(prefs['idle_timeout_min'])
        self.idle.setToolTip('Stop counting after this long with no input and no page turn (WakaTime caps gaps at 15 min).')
        form.addRow('Idle timeout:', self.idle)

        self.interval = QSpinBox()
        self.interval.setRange(30, 600)
        self.interval.setSuffix(' s')
        self.interval.setValue(prefs['heartbeat_interval_s'])
        form.addRow('Heartbeat interval:', self.interval)

        self.category = QComboBox()
        self.category.addItems(CATEGORIES)
        self.category.setCurrentText(prefs['category'])
        form.addRow('WakaTime category:', self.category)

        self.project_mode = QComboBox()
        self.project_mode.addItems(['library', 'fixed'])
        self.project_mode.setCurrentText(prefs['project_mode'])
        form.addRow('Project name from:', self.project_mode)

        self.fixed = QLineEdit(prefs['fixed_project'])
        self.fixed.setPlaceholderText('used when "fixed" is selected')
        form.addRow('Fixed project:', self.fixed)

        self.hide = QCheckBox('Hide book titles (send an anonymous id instead)')
        self.hide.setChecked(prefs['hide_titles'])
        form.addRow(self.hide)

        self.cli = QLineEdit(prefs['cli_path'])
        self.cli.setPlaceholderText('auto-detect in ~/.wakatime')
        form.addRow('wakatime-cli path:', self.cli)

    def save_settings(self) -> None:
        prefs['enabled'] = self.enabled.isChecked()
        prefs['idle_timeout_min'] = self.idle.value()
        prefs['heartbeat_interval_s'] = self.interval.value()
        prefs['category'] = self.category.currentText()
        prefs['project_mode'] = self.project_mode.currentText()
        prefs['fixed_project'] = self.fixed.text().strip()
        prefs['hide_titles'] = self.hide.isChecked()
        prefs['cli_path'] = self.cli.text().strip()
