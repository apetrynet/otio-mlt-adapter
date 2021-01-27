# OpenTimelineIO MLT Adapter

The MLT adapter currently only supports writing simplified mlt xml files
geared towards use with the "melt" command line video editor.

Example: `melt my_converted_otio_file.mlt [OPTIONS]`

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

## Installation

```python
pip install otio-mlt-adapter
```

## Usage Command Line
```bash
# Straight conversion from otio -> mlt
otioconvert -i source_timeline.otio -o destination_timeline.mlt

# Pass adapter arguments
otioconvert -i source_timeline.otio -o destination_timeline.mlt -A colorspace=709
```

## Usage Python
```python
import opentimelineio as otio

# Straight conversion
timeline = otio.adapters.read_from_file('source_timeline.otio')
otio.adapters.write_to_file(timeline, 'converted_timeline.mlt')

timeline1 = otio.adapters.read_from_file('source_timeline.otio')
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
