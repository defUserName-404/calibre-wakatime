from calibre.customize import InterfaceActionBase


class WakaTimePlugin(InterfaceActionBase):
    name = 'WakaTime'
    description = 'Track e-book reading time (calibre viewer) in WakaTime'
    supported_platforms = ['osx']
    author = 'defUserName-404'
    version = (1, 0, 0)
    minimum_calibre_version = (6, 0, 0)
    actual_plugin = 'calibre_plugins.wakatime.ui:WakaTimeAction'

    def is_customizable(self):
        return True

    def config_widget(self):
        from calibre_plugins.wakatime.config import ConfigWidget
        return ConfigWidget()

    def save_settings(self, config_widget):
        config_widget.save_settings()
        ac = self.actual_plugin_
        if ac is not None:
            ac.apply_settings()
