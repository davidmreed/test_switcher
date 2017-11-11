import sublime
import sublime_plugin
import os

class TestSwitcherCommand(sublime_plugin.TextCommand):
    def run(self, args):
        settings = sublime.load_settings("test_switcher.sublime-settings")
        prefixes = [x.lower() for x in settings.get("prefixes") or []]
        suffixes = [x.lower() for x in settings.get("suffixes") or []]
        source_extensions = [x.lower() for x in settings.get("source_extensions") or []]
        test_extensions = [x.lower() for x in settings.get("test_extensions") or []]

        file_name = self.view.file_name()

        if file_name is not None:
            # Pull out the base name of what we are viewing (without extension)
            base_name = os.path.splitext(os.path.basename(file_name))[0].lower()

            if self.is_test_name(base_name, prefixes, suffixes):
                # Current view is showing a test file.
                options = self.find_options(self.find_potential_basenames(base_name, prefixes, suffixes), source_extensions)
            else:
                # Current view is showing a source file.
                options = self.find_options(self.find_potential_testnames(base_name, prefixes, suffixes), test_extensions)

            if len(options) == 0:
                sublime.message_dialog("No test or source file was found to switch to.")
            elif len(options) == 1:
                self.view.window().open_file(options[0])
            else:
                self.view.window().show_quick_panel(options, lambda i: sublime.active_window().open_file(options[i]))

    def is_enabled(self):
        return self.view.file_name() is not None

    def is_test_name(self, file_name, prefixes, suffixes):
        return True in [file_name.startswith(prefix) for prefix in prefixes] \
            or True in [file_name.endswith(suffix) for suffix in suffixes]

    def find_potential_basenames(self, file_name, prefixes, suffixes):
        return [file_name[:-len(suffix)] for suffix in suffixes if file_name.endswith(suffix)] \
           + [file_name[len(prefix):] for prefix in prefixes if file_name.startswith(prefix)]

    def find_potential_testnames(self, name, prefixes, suffixes):
        return [(name + suffix).lower() for suffix in suffixes] \
            + [(prefix + name).lower() for prefix in prefixes]

    def find_options(self, possible_names, extensions):
        # Search open tabs first, for speed, and then scan the open folders for matches
        candidates = self.find_possible_paths(self.view_paths(), possible_names, extensions)
        if len(candidates) == 0:
            candidates = self.find_possible_paths(self.folder_paths(), possible_names, extensions)

        return candidates

    def find_possible_paths(self, generator, possible_names, extensions):
        possible_paths = []

        for path in generator:
            basename, ext = os.path.splitext(os.path.basename(path))
            if basename.lower() in possible_names:
                if len(extensions) == 0 or extension.lower() in extensions:
                    possible_paths.append(path)

        return possible_paths

    def view_paths(self):
        for v in self.view.window().views():
            if v.file_name() is not None:
                yield v.file_name()

    def folder_paths(self):
        for directory in self.view.window().folders():
            for cwd, subfolders, files in os.walk(directory):
                for f in files:
                    yield os.path.join(cwd, f)
