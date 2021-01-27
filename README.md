# OpenTimelineIO MLT Adapter

The MLT adapter is a write-only adapter to produce 
[mlt xml](https://www.mltframework.org/docs/mltxml/) files
for use with the [melt](https://www.mltframework.org/docs/melt/) command line 
video editor.

The motivation for writing this adapter is playback or
rendering of mini-cuts for instance and not parsing project files for
applications based on MLT such as kdenlive, Shotcut etc.
There already exists an adapter for kdenlive files in OTIO.

Therefore, reading of mlt files is not supported at the moment.
This is also partly due to the flexible nature of the MLT format making it a
bit hard to write a solid parser based on etree.

If someone wants to implement parsing/reading of mlt files feel free to do so.
You might want to use the python-mlt bindings available for a more robust
parser, but please note that adds a third-party dependency to the adapter.

For more info on the MLT visit the website: https://www.mltframework.org/

## Feature Matrix
| Feature | MLT   |
| :------ | :---: |
|Single Track of Clips    | W-O |
|Multiple Video Tracks    | W-O |
|Audio Tracks & Clips     | W-O |
|Gap/Filler               | W-O |
|Markers                  |  ✖  |
|Nesting                  | W-O |
|Transitions              | W-O |
|Audio/Video Effects      |  ✖  |
|Linear Speed Effects     | W-O |
|Fancy Speed Effects      |  ✖  |
|Color Decision List      | N/A |
|Image Sequence Reference | W-O |


## Installation
The easiest way to install the adapter is through pip
```python
pip install otio-mlt-adapter
```
If you choose to download the source code and place it in an alternative 
location, make sure you add the path to the `plugin_manifest.json` file to
the `OTIO_PLUGIN_MANIFEST_PATH` environment variable. 

## Usage with command line tools
```bash
# Straight conversion from otio -> mlt
otioconvert -i source_timeline.otio -o destination_timeline.mlt

# Pass adapter arguments
otioconvert -i source_timeline.otio -o destination_timeline.mlt -A colorspace=709
```

## Usage in python
```python
import opentimelineio as otio

# Straight conversion
timeline = otio.adapters.read_from_file('source_timeline.otio')
otio.adapters.write_to_file(timeline, 'converted_timeline.mlt')

# Conversion with adapter argument
timeline = otio.adapters.read_from_file('source_timeline.otio')
otio.adapters.write_to_file(timeline, 'converted_timeline.mlt', colorspace=709)
```

## Development
```bash
pip install -e .[dev]
```

### NOTES
    Audio handling is a bit limited. Audio clips that have the same source
    in video track will be ignored as MLT will include audio from the video
    track by default.

    Effects directly on Track and Stack is currently not implemented
