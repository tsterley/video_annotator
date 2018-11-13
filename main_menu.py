from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.filechooser import FileChooserListView
from functools import partial
from time import sleep

from video_annotator import *
from analysis import *
import sys, os, yaml, errno


class MenuRoot(BoxLayout):
    def __init__(self):
        super(MenuRoot, self).__init__()
        # if getattr(sys, 'frozen', False):
        #     self.root_folder = sys._MEIPASS
        if getattr(sys, 'frozen', False):
            self.root_folder = os.path.dirname(os.path.realpath(sys.executable))
        elif __file__:
            self.root_folder = os.path.dirname(os.path.realpath(__file__))

        self._update_config_options()

    def _update_config_options(self):
        # Load config options
        conf_location = os.path.join(self.root_folder, "config", "default_config.yaml")
        with open(conf_location, 'r') as ymlfile:
            config = yaml.load(ymlfile)
            self.mouse_actions  = tuple([act for act in config["actions"]["selectable"]])

    def _load_video(self, filechooser, load_vid_popup, button):
        if len(filechooser.selection) != 1: return # bad selection

        # Get file details
        file_url = filechooser.selection[0]
        file_name, file_ext = os.path.splitext(os.path.basename(file_url))

        # If file is a video, load it
        if file_ext.lower() in (".mts", ".mp4", ".avi"):
            load_vid_popup.dismiss() # kill loading popup

            # Analyse video
            recorded_actions = analyse_video(file_url, self.mouse_actions)

            # Save results
            if recorded_actions:
                self._save_popup(recorded_actions, file_name)

    def _save_popup(self, recorded_actions, default_name=""):
        # Build popup
        saver = BoxLayout(orientation="vertical")
        name_input = TextInput(text=default_name, size_hint=(1, 0.6))
        btn = Button(text='Ok', size_hint=(1, 0.4))

        saver.add_widget(name_input)
        saver.add_widget(btn)

        # Launch popup
        save_vid_popup = Popup(title="Choose Name", content=saver, size_hint=(0.8, 0.3), auto_dismiss=False)
        btn.bind(on_release=partial(self._save_results, (name_input, recorded_actions), save_vid_popup))
        save_vid_popup.open()

    def _save_results(self, data, save_vid_popup, button):
        name_input, recorded_actions = data

        results_name = name_input.text
        results_path = os.path.join(self.root_folder, "results", results_name)
        file_name_valid = True; message = ""

        if not len(results_name):
            file_name_valid = False; message = "Please specify a valid name"
        elif os.path.isdir(results_path):
            file_name_valid = False; message = "Name already exists"

        if file_name_valid:
            save_vid_popup.dismiss() # kill saving popup

            # Create folder
            try:
                os.makedirs(results_path)
            except OSError as e:
                if e.errno != errno.EEXIST: raise

            save_location = os.path.join(results_path, "annotations.csv")
            with open(save_location, 'w') as output_file:
                output_file.write("Behaviour, start_time(ms)\n")
                for action in recorded_actions:
                    output_file.write("%s,%.4f\n" % (action[0], action[1]))

            # Analyse output
            analyse_annotation(results_path)
        else:
            btn = Button(text='Ok')
            err_popup = Popup(title=message, content=btn, size_hint=(0.5, 0.2))
            btn.bind(on_release=err_popup.dismiss)
            err_popup.open()

    def on_button_load(self):
        # Build popup
        loader = BoxLayout(orientation="vertical")
        start_path  = os.path.join(self.root_folder, "videos")
        formats = ["*.mts", "*.MTS", "*.mp4", "*.MP4", "*.avi", "*.AVI"]
        fileChooser = FileChooserListView(path=start_path, filters=formats, size_hint=(0.9, 0.9))
        btn = Button(text='Ok', size_hint=(1, 0.1))

        loader.add_widget(fileChooser)
        loader.add_widget(btn)

        # Launch popup
        load_vid_popup = Popup(title="Choose Video", content=loader, size_hint=(.7, .7))
        btn.bind(on_release=partial(self._load_video, fileChooser, load_vid_popup))
        load_vid_popup.open()

    def on_button_config(self):
        options = BoxLayout(orientation="vertical")

        # Actions
        for a in self.mouse_actions:
            box = BoxLayout(orientation="horizontal")
            box.add_widget(Label(text=a["name"]))
            box.add_widget(Label(text=a["key"]))
            box.add_widget(Label(text=a["colour"]))

            options.add_widget(box)

        # Exit button
        btn = Button(text='Ok')
        options.add_widget(btn)

        config_pop_up = Popup(title="Config", content=options)
        btn.bind(on_release=config_pop_up.dismiss)
        config_pop_up.open()

    def on_button_quit(self):
        print("Bye.")
        sys.exit(0)


class MenuApp(App):
    def build(self):
        # Return root widget
        return MenuRoot()

if __name__ == "__main__":
    MenuApp().run()
