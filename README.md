# Video Annotator
Tool to help researchers annotate videos, created by Toni-Lee Sterley and Nielen Venter

## Using the Annotator
##### Requirements
- [OpenCV](https://pypi.org/project/opencv-python/) (recommended 3.3.1)
- [Kivy](https://kivy.org/#home) (recommended 1.10.0)
- [PyYAML](https://pyyaml.org/wiki/PyYAML) (recommended 3.12)
- [NumPy](http://www.numpy.org/) (recommended 1.13.3)

##### Usage
The annotator can be started using the provided "main_menu.exe" or by running the "main_menu.py" file with Python (e.g. by typing `python main_menu.py` in Command Prompt).

From the main menu, picking "Load" will allow the user to select a video for annotation.

![Choose Video](/images/select_video.PNG?raw=true "Choose Video")

Once a video is selected, the app will display it. Also displayed will be a description of possible keyboard inputs. These include annotations that can be marked, as well as control keys. Customising possible behaviours is done via the config file, described in the "Config File" section below

![Video Chosen](/images/video_display.PNG?raw=true "Left: Keyboard Inputs, Right: Video Display")

`Spacebar` starts and stops the video. `]` and `[` increase and decrease the playback speed respectively, between 1x and 5x the normal speed. `,` and `.` jump the current video position forwards and backwards respectively, to allow quicker navigation through the video.

Pressing `Esc` will stop the annotator, and pressing any other key will bring up a window to save the resulting annotations. To cancel the save, press `Esc` again.

A sample video is provided ("videos\\example.mp4") to help users familiarise themselves with the annotator and its controls.

##### Config File
Markable annotations are stored in "config\\default_config.yaml". They are stored under `selectable:` in the follow format:
```
- name: <annotation_name>
  key: <key_to_press>
  colour: <B>,<G>,<R>
```
Where the BGR values set the annotation colour, and each range from 0-1. The indentation for each annotation must match the others. The default file has 3 example annotations which can be edited, replaced and/or used as reference for any new additions.

##### Colour plots
In addition to saving the annotations, the app will generate simple colour plots, using the annotation colours. These plots are saved in the location as the annotations ("results\\<annotation_name>").

## Creating an executable file
