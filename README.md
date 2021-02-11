# MLT XML Adapter for OpenTimelineIO 

![Supported Versions](https://img.shields.io/badge/OpenTimelineIO-0.12.1%2C%200.13.0-green.svg)
![Supported Versions](https://img.shields.io/badge/python-2.7%2C%203.7%2C%203.8-blue.svg)
![Unit tests](https://github.com/apetrynet/otio-mlt-adapter/workflows/tests/badge.svg?branch=main&event=push)

When installed, the plugin adds itself to the available adapters in 
[OpenTimelineIO](http://opentimeline.io/) <br>
The MLT XML adapter produces mlt flavored [xml](https://www.mltframework.org/docs/mltxml/) 
files used in conjunction with [melt](https://www.mltframework.org/docs/melt/) 
to preview or render timelines.

The adapter is a write-only adapter and can only produce `.mlt` files, 
not parse them. For parsing dialects of the mlt format please check out one 
of the other adapters listed [here](https://github.com/PixarAnimationStudios/OpenTimelineIO/wiki/Tools-and-Projects-Using-OpenTimelineIO).

For more information on MLT please visit: [www.mltframework.org](https://www.mltframework.org)


## Installation

The easiest way to install the adapter is with pip directly from PyPi
```bash
# Install
pip install otio-mlt-adapter

# Check if plugin installed correctly
otiopluginfo mlt_xml
```
If you choose to download the source code and place the package in an alternative 
location, make sure you append the full path to the `plugin_manifest.json` file 
to the `OTIO_PLUGIN_MANIFEST_PATH` environment variable. 


## Usage in command line tools

```bash
# Straight conversion from otio -> mlt
otioconvert -i source_timeline.otio -o destination_timeline.mlt

# Pass adapter arguments
otioconvert -i source_timeline.otio -o destination_timeline.mlt -A colorspace=709

# Play timeline in melt
melt destination_timeline.mlt
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


## Supported OTIO Features

| OTIO Feature            | MLT Adapter |
| :---------------------- | :---------: |
|Single Track of Clips    | W-O         |
|Multiple Video Tracks    | W-O         |
|Audio Tracks & Clips     | W-O         |
|Gap/Filler               | W-O         |
|Markers                  |  ✖          |
|Nesting                  | W-O         |
|Transitions              | W-O         |
|Audio/Video Effects      |  ✖          |
|Linear Speed Effects     | W-O         |
|Fancy Speed Effects      |  ✖          |
|Color Decision List      | N/A         |
|Image Sequence Reference | W-O         |


## Known limitations
* Audio handling is a bit limited. Clips in audio tracks that share the same 
  source as the video clip above will be ignored as MLT will include the audio 
  from the video track by default.

* Effects directly applied on Tracks or Stacks are currently not implemented


## Feedback
Please submit bug reports etc. through github [issues](https://github.com/apetrynet/otio-mlt-adapter/issues)


## License
MLT XML adapter is released under the [MIT License](https://github.com/apetrynet/otio-mlt-adapter/blob/main/LICENSE.txt)
