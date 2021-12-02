import pytest
from xml.etree import ElementTree as et

import opentimelineio as otio
from opentimelineio.exceptions import AdapterDoesntSupportFunctionError

from otio_mlt_adapter.adapters.mlt_xml import MLTAdapter

OTIO_VERSION = tuple(map(int, otio.__version__.split('.')))


def test_single_clip():
    clip1 = otio.schema.Clip(
        name='clip1',
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(100, 30)
        )
    )

    tree = et.fromstring(otio.adapters.write_to_string(clip1, 'mlt_xml'))
    producer_e = tree.find('./producer/[@id="{}"]'.format(clip1.name))

    assert producer_e is not None
    assert producer_e.attrib['id'] == clip1.name

    playlist_e = tree.find('./playlist/[@id="playlist0"]')
    entry_e = playlist_e.find('./entry/[@producer="{}"]'.format(clip1.name))

    assert entry_e.attrib['producer'] == clip1.name
    assert float(entry_e.attrib['in']) == clip1.source_range.start_time.value
    assert (
            float(entry_e.attrib['out']) ==
            clip1.source_range.end_time_inclusive().value
    )


def test_single_track():
    clip1 = otio.schema.Clip(
        name='clip1',
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(100, 30)
        )
    )

    track = otio.schema.Track('video1')
    track.append(clip1)

    tree = et.fromstring(otio.adapters.write_to_string(track, 'mlt_xml'))
    producer_e = tree.find('./producer/[@id="{}"]'.format(clip1.name))

    assert producer_e is not None
    assert producer_e.attrib['id'] == clip1.name

    playlist_e = tree.find('./playlist/[@id="video1"]')
    assert playlist_e is not None

    entry_e = playlist_e.find('./entry/[@producer="{}"]'.format(clip1.name))
    assert entry_e.attrib['producer'] == clip1.name
    assert (
        float(entry_e.attrib['in']) ==
        clip1.source_range.start_time.value
    )
    assert (
        float(entry_e.attrib['out']) ==
        clip1.source_range.end_time_inclusive().value
    )


def test_pass_unsupported_object():
    stack = otio.schema.Stack('stack1')

    with pytest.raises(ValueError) as err:
        et.fromstring(otio.adapters.write_to_string(stack, 'mlt_xml'))

    assert (
        "Passed OTIO item must be Timeline, Track or Clip. "
        "Not {}".format(type(stack)) ==
        str(err.value)
    )


def test_external_reference():
    path = '/some/path/to/media_file.mov'
    clip_with_media_ref = otio.schema.Clip(
        name='clip_with_media_ref',
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(100, 30)
        ),
        media_reference=otio.schema.ExternalReference(
            target_url=path,
            available_range=otio.opentime.TimeRange(
                otio.opentime.RationalTime(0, 30),
                otio.opentime.RationalTime(100, 30)
            )
        )
    )

    clip2 = otio.schema.Clip(
        name='clip2',
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(100, 30)
        )
    )

    track = otio.schema.Track()
    track.append(clip_with_media_ref)
    track.append(clip2)

    tree = et.fromstring(otio.adapters.write_to_string(track, 'mlt_xml'))

    producer1_e = tree.find(
        './producer/[@id="{}"]'.format(clip_with_media_ref.name)
    )
    property_text = producer1_e.findtext('property', path)
    assert property_text is not None
    assert float(producer1_e.attrib['in']) == 0
    assert float(producer1_e.attrib['out']) == 99

    # Producers with no external reference get clip.name as "path"
    producer2_e = tree.find('./producer/[@id="{}"]'.format(clip2.name))
    property2_text = producer2_e.findtext('property', clip2.name)
    assert property2_text is not None
    assert producer2_e.attrib.get('in') is None
    assert producer2_e.attrib.get('out') is None


@pytest.mark.skipif(
    OTIO_VERSION < (0, 13, 0),
    reason="ImageSequenceReference was introduced in 0.13.0 "
           "This is v{version}".format(version=otio.__version__)
)
def test_image_sequence():
    clip1 = otio.schema.Clip(
        name='imageseq',
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(10, 30),
            otio.opentime.RationalTime(80, 30)
        ),
        media_reference=otio.schema.ImageSequenceReference(
            target_url_base='/path/to/files/',
            name_prefix='image.',
            start_frame=1001,
            frame_zero_padding=4,
            frame_step=1,
            name_suffix='.png',
            rate=30,
            available_range=otio.opentime.TimeRange(
                otio.opentime.RationalTime(0, 30),
                otio.opentime.RationalTime(100, 30)
            )
        )
    )
    track = otio.schema.Track('images')
    track.append(clip1)

    tree = et.fromstring(otio.adapters.write_to_string(track, 'mlt_xml'))

    producer_e = tree.find('./producer/[@id="imageseq"]')
    assert producer_e is not None

    abstract_url = '/path/to/files/image.%04d.png?start_number=1001'
    assert (
        producer_e.find('./property/[@name="resource"]').text ==
        abstract_url
    )

    # Default image2 producer
    assert (
        producer_e.find('./property/[@name="mlt_service"]').text ==
        'image2'
    )

    # Pass alternative pixbuf argument
    tree = et.fromstring(
        otio.adapters.write_to_string(
            track,
            'mlt_xml',
            image_producer='pixbuf'
        )
    )

    producer_e = tree.find('./producer/[@id="imageseq"]')

    # Overridden pixbuf producer
    assert (
        producer_e.find('./property/[@name="mlt_service"]').text ==
        'pixbuf'
    )

    abstract_url = '/path/to/files/image.%04d.png?begin=1001'
    assert (
        producer_e.find('./property/[@name="resource"]').text ==
        abstract_url
    )

    # Test unsupported image producer
    with pytest.raises(ValueError) as err:
        otio.adapters.write_to_string(
            track,
            'mlt_xml',
            image_producer='nothinhere'
        )
    assert (
            'Image producer must be "image2" or "pixbuf"' ==
            str(err.value)
    )


def test_de_duplication_of_producers():
    clipname = 'clip'
    clip1 = otio.schema.Clip(
        name=clipname,
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(100, 30)
        )
    )

    clip2 = otio.schema.Clip(
        name=clipname,
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(100, 30)
        )
    )

    same_but_different_name = 'clip1'
    clip3 = otio.schema.Clip(
        name=same_but_different_name,
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(100, 30)
        ),
        media_reference=otio.schema.ExternalReference(
            target_url='/path/one/to/clip.mov'
        )
    )

    clip4 = otio.schema.Clip(
        name=same_but_different_name,
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(100, 30)
        ),
        media_reference=otio.schema.ExternalReference(
            target_url='/path/two/to/clip.mov'
        )
    )
    clip5 = otio.schema.Clip(
        name=same_but_different_name,
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(100, 30)
        ),
        media_reference=otio.schema.ExternalReference(
            target_url='/path/two/to/clip.mov'
        )
    )

    track = otio.schema.Track()
    track.append(clip1)
    track.append(clip2)
    track.append(clip3)
    track.append(clip4)
    track1 = otio.schema.Track('audio1', kind=otio.schema.TrackKind.Audio)
    track1.append(clip5)

    timeline = otio.schema.Timeline()
    timeline.tracks.append(track)
    timeline.tracks.append(track1)

    tree = et.fromstring(otio.adapters.write_to_string(timeline, 'mlt_xml'))

    producers_noref = tree.findall('./producer/[@id="{}"]'.format(clipname))
    assert len(producers_noref) == 1

    producers_ref = tree.findall(
        './producer/[@id="{}"]'.format(same_but_different_name)
    )

    assert len(producers_ref) == 2
    assert (
        producers_ref[0].attrib['id'] ==
        producers_ref[1].attrib['id']
    )
    assert tree.findtext('property', '/path/one/to/clip.mov') is not None
    assert tree.findtext('property', '/path/two/to/clip.mov') is not None


def test_timeline_with_tracks():
    clip1 = otio.schema.Clip(
        name='clip1',
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(50, 30)
        )
    )

    clip2 = otio.schema.Clip(
        name='clip2',
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(500, 30)
        )
    )

    clip3 = otio.schema.Clip(
        name='clip3',
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(50, 30)
        )
    )

    gap1 = otio.schema.Gap(
        name='gap1',
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(50, 30)
        )
    )

    gap2 = otio.schema.Gap(
        name='gap2',
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(50, 30)
        )
    )

    timeline = otio.schema.Timeline()
    track1 = otio.schema.Track('video1')
    track2 = otio.schema.Track('video2')
    track3 = otio.schema.Track('audio1', kind=otio.schema.TrackKind.Audio)
    track4 = otio.schema.Track('audio2', kind=otio.schema.TrackKind.Audio)
    timeline.tracks.append(track1)
    timeline.tracks.append(track2)
    timeline.tracks.append(track3)
    timeline.tracks.append(track4)

    track1.append(clip1)
    track1.append(gap1)
    track1.append(clip2)

    track2.append(gap2)
    track2.append(clip3)

    # Same as video1
    track3.append(clip1.clone())
    track3.append(gap1.clone())
    track3.append(clip2.clone())

    # Same as video1
    track4.append(clip1.clone())
    track4.append(gap1.clone())
    track4.append(clip2.clone())

    tree = et.fromstring(
        otio.adapters.write_to_string(timeline, 'mlt_xml')
    )

    playlists = tree.findall('./playlist')
    tracks = tree.findall('./tractor/multitrack/track')

    # Check for background and the four tracks == 5
    assert len(playlists) == 5
    assert len(tracks) == 5

    track1_e = tree.find('./playlist/[@id="video1"]')

    assert track1_e[0].attrib['producer'] == clip1.name
    assert (
        float(track1_e[0].attrib['in']) ==
        clip1.source_range.start_time.value
    )
    assert (
        float(track1_e[0].attrib['out']) ==
        clip1.source_range.end_time_inclusive().value
    )
    assert track1_e[1].tag == 'blank'
    assert (
        float(track1_e[1].attrib['length']) ==
        gap1.duration().value
    )
    assert track1_e[2].attrib['producer'] == clip2.name
    assert (
        float(track1_e[2].attrib['in']) ==
        clip2.source_range.start_time.value
    )
    assert (
        float(track1_e[2].attrib['out']) ==
        clip2.source_range.end_time_inclusive().value
    )

    track2_e = tree.find('./playlist/[@id="video2"]')
    assert track2_e[0].tag == 'blank'
    assert (
        float(track2_e[0].attrib['length']) ==
        gap2.duration().value
    )
    assert track2_e[1].attrib['producer'] == clip3.name
    assert (
        float(track2_e[1].attrib['in']) ==
        clip3.source_range.start_time.value
    )
    assert (
        float(track2_e[1].attrib['out']) ==
        clip3.source_range.end_time_inclusive().value
    )

    # Check if first tracks after background are audio
    track3_e = tracks[2]
    assert track3_e.attrib['producer'] == 'audio1'

    track4_e = tracks[1]
    assert track4_e.attrib['producer'] == 'audio2'


def test_nested_timeline():
    clip1 = otio.schema.Clip(
        name='clip1',
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(50, 30)
        )
    )

    clip2 = otio.schema.Clip(
        name='clip2',
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(500, 30)
        )
    )

    timeline1 = otio.schema.Timeline(name='timeline1')
    track1 = otio.schema.Track('video1')
    track1.append(clip1)
    timeline1.tracks.append(track1)

    nested_stack = otio.schema.Stack(name='nested')
    nested_stack.append(clip2)

    track1.append(nested_stack)

    tree = et.fromstring(
        otio.adapters.write_to_string(timeline1, 'mlt_xml')
    )

    playlists = tree.findall('./playlist')
    assert len(playlists) == 3

    nested = tree.find('.playlist/[@id="nested"]')
    nested_clip = nested[0]

    assert nested is not None
    assert (
        float(nested_clip.attrib['out']) ==
        clip2.source_range.end_time_inclusive().value
    )

    tracks = tree.findall('./tractor/multitrack/track')
    assert tracks[0].attrib['producer'] == 'background'
    assert tracks[1].attrib['producer'] == 'video1'

    assert nested.find('./entry/[@producer="clip2"]') is not None


def test_video_fade_in():
    # beginning of timeline
    fade_in1 = otio.schema.Transition(
        name='fadeIn',
        in_offset=otio.opentime.RationalTime(0, 30),
        out_offset=otio.opentime.RationalTime(30, 30)
    )

    clip1 = otio.schema.Clip(
        name='clip1',
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(50, 30)
        )
    )

    track1 = otio.schema.Track('faded_beginning')
    track1.append(fade_in1)
    track1.append(clip1)

    tree = et.fromstring(
        otio.adapters.write_to_string(track1, 'mlt_xml')
    )

    tractor1_e = tree.find('./tractor/[@id="transition_tractor0"]')
    assert (
        float(tractor1_e.attrib['out']) ==
        fade_in1.out_offset.value - 1
    )
    assert tractor1_e is not None

    tracks1 = tractor1_e.findall('./track')
    assert tracks1[0].attrib['producer'] == 'solid_black'
    assert (
        tracks1[1].attrib['producer'] ==
        'clip1_transition_post'
    )

    playlist1_e = tree.find('./playlist/[@id="faded_beginning"]')
    assert playlist1_e is not None
    assert (
        playlist1_e[0].attrib['producer'] ==
        'transition_tractor0'
    )
    assert (
        playlist1_e[1].attrib['producer'] ==
        'clip1'
    )
    assert (
        float(playlist1_e[1].attrib['in']) ==
        30
    )

    # further in
    gap1 = otio.schema.Gap(
        name='gap1',
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(50, 30)
        )
    )

    fade_in2 = otio.schema.Transition(
        name='fadeIn',
        in_offset=otio.opentime.RationalTime(0, 30),
        out_offset=otio.opentime.RationalTime(30, 30)
    )

    clip2 = otio.schema.Clip(
        name='clip2',
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(50, 30)
        )
    )

    track2 = otio.schema.Track('faded_indented')
    track2.append(gap1)
    track2.append(fade_in2)
    track2.append(clip2)

    tree = et.fromstring(
        otio.adapters.write_to_string(track2, 'mlt_xml')
    )

    tractor2_e = tree.find('./tractor/[@id="transition_tractor0"]')
    assert (
        float(tractor2_e.attrib['out']) ==
        fade_in1.out_offset.value - 1
    )
    assert tractor2_e is not None

    tracks2 = tractor2_e.findall('./track')
    assert tracks2[0].attrib['producer'] == 'solid_black'
    assert (
        tracks2[1].attrib['producer'] ==
        'clip2_transition_post'
    )

    playlist2_e = tree.find('./playlist/[@id="faded_indented"]')
    assert playlist2_e is not None
    assert playlist2_e[0].tag == 'blank'
    assert (
        playlist2_e[1].attrib['producer'] ==
        'transition_tractor0'
    )
    assert (
        playlist2_e[2].attrib['producer'] ==
        'clip2'
    )
    assert(
        float(playlist2_e[2].attrib['in']) ==
        30
    )

    # Useless fade
    fade_in3 = otio.schema.Transition(
        name='fadeIn',
        in_offset=otio.opentime.RationalTime(0, 30),
        out_offset=otio.opentime.RationalTime(30, 30)
    )
    track3 = otio.schema.Track('faded_useless')
    track3.append(fade_in3)
    tree = et.fromstring(
        otio.adapters.write_to_string(track3, 'mlt_xml')
    )

    tractor3_e = tree.find('./tractor/[@id="transition_tractor0"]')
    assert (
        tractor3_e[0].attrib['producer'] ==
        tractor3_e[1].attrib['producer']
    )


def test_video_fade_out():
    # beginning of timeline (useless)
    fade_out1 = otio.schema.Transition(
        name='fadeOut',
        in_offset=otio.opentime.RationalTime(30, 30),
        out_offset=otio.opentime.RationalTime(0, 30)
    )

    track1 = otio.schema.Track('fadeout_useless')
    track1.append(fade_out1)

    tree = et.fromstring(
        otio.adapters.write_to_string(track1, 'mlt_xml')
    )

    tractor1_e = tree.find('./tractor/[@id="transition_tractor0"]')
    assert (
        tractor1_e[0].attrib['producer'] ==
        tractor1_e[1].attrib['producer']
    )

    # Regular fade out
    fade_out2 = otio.schema.Transition(
        name='fadeOut',
        in_offset=otio.opentime.RationalTime(30, 30),
        out_offset=otio.opentime.RationalTime(0, 30)
    )

    clip1 = otio.schema.Clip(
        name='clip1',
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(50, 30)
        )
    )

    track2 = otio.schema.Track('fadeout')
    track2.append(clip1)
    track2.append(fade_out2)

    tree = et.fromstring(
        otio.adapters.write_to_string(track2, 'mlt_xml')
    )

    tractor2_e = tree.find('./tractor/[@id="tractor0"]')

    tracks = tractor2_e.findall('./multitrack/track')
    assert tracks[1].attrib['producer'] == 'fadeout'

    transition_e = tree.find('./tractor/[@id="transition_tractor0"]')
    assert (
        transition_e[0].attrib['producer'] ==
        'clip1_transition_pre'
    )
    assert (
        float(transition_e[0].attrib['in']) ==
        clip1.source_range.duration.value - fade_out2.in_offset.value
    )

    playlist_e = tree.find('./playlist/[@id="fadeout"]')
    assert (
        float(playlist_e[0].attrib['out']) ==
        float(transition_e[0].attrib['in']) - 1
    )


def test_video_dissolve():
    clip1 = otio.schema.Clip(
        name='clip1',
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(50, 30)
        )
    )

    clip2 = otio.schema.Clip(
        name='clip2',
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(500, 30)
        )
    )

    dissolve1 = otio.schema.Transition(
        name='dissolve',
        in_offset=otio.opentime.RationalTime(30, 30),
        out_offset=otio.opentime.RationalTime(0, 30)
    )

    clip3 = otio.schema.Clip(
        name='clip3',
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(500, 30)
        )
    )

    clip4 = otio.schema.Clip(
        name='clip4',
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(30, 30),
            otio.opentime.RationalTime(500, 30)
        )
    )

    dissolve2 = otio.schema.Transition(
        name='dissolve',
        in_offset=otio.opentime.RationalTime(30, 30),
        out_offset=otio.opentime.RationalTime(0, 30)
    )

    track1 = otio.schema.Track('dissolve')
    track1.append(clip1)
    track1.append(dissolve1)
    track1.append(clip2)

    tree = et.fromstring(
        otio.adapters.write_to_string(track1, 'mlt_xml')
    )

    transition1_e = tree.find('./tractor/[@id="transition_tractor0"]')
    assert (
        transition1_e[0].attrib['producer'] ==
        'clip1_transition_pre'
    )
    assert (
        transition1_e[1].attrib['producer'] ==
        'clip2_transition_post'
    )

    # Clip2 doesn't have enough media to cover the dissolve and has
    # negative values
    assert (
        float(transition1_e[1].attrib['in']) ==
        -30.
    )

    track2 = otio.schema.Track('dissolve')
    track2.append(clip3)
    track2.append(dissolve2)
    track2.append(clip4)

    tree = et.fromstring(
        otio.adapters.write_to_string(track2, 'mlt_xml')
    )

    transition2_e = tree.find('./tractor/[@id="transition_tractor0"]')
    assert (
        transition2_e[0].attrib['producer'] ==
        'clip3_transition_pre'
    )
    assert (
        transition2_e[1].attrib['producer'] ==
        'clip4_transition_post'
    )

    assert (
        float(transition2_e[1].attrib['in']) ==
        0.
    )

    # Video tracks dissolve with "luma" service
    service = transition2_e.find(
        './transition/property/[@name="mlt_service"]'
    )
    assert service.text == 'luma'


def test_audio_dissolve():
    clip1 = otio.schema.Clip(
        name='clip1',
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(500, 30)
        )
    )

    clip2 = otio.schema.Clip(
        name='clip2',
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(30, 30),
            otio.opentime.RationalTime(500, 30)
        )
    )

    dissolve1 = otio.schema.Transition(
        name='dissolve',
        in_offset=otio.opentime.RationalTime(30, 30),
        out_offset=otio.opentime.RationalTime(0, 30)
    )

    track1 = otio.schema.Track(
        'dissolve',
        kind=otio.schema.TrackKind.Audio
    )
    track1.append(clip1)
    track1.append(dissolve1)
    track1.append(clip2)

    tree = et.fromstring(
        otio.adapters.write_to_string(track1, 'mlt_xml')
    )
    transition1_e = tree.find('./tractor/[@id="transition_tractor0"]')

    # Audio tracks dissolve with "mix" service
    service = transition1_e.find(
        './transition/property/[@name="mlt_service"]'
    )
    assert service.text == 'mix'


def test_time_warp():
    path = '/some/path/to/media_file.mov'

    # Speedup
    clip_with_speedup1 = otio.schema.Clip(
        name='clip_with_speedup',
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(100, 30)
        ),
        media_reference=otio.schema.ExternalReference(
            target_url=path,
            available_range=otio.opentime.TimeRange(
                otio.opentime.RationalTime(0, 30),
                otio.opentime.RationalTime(100, 30)
            )
        )
    )
    clip_with_speedup1.effects.append(
        otio.schema.LinearTimeWarp(
            time_scalar=2.
        )
    )

    track1 = otio.schema.Track('speedup')
    track1.append(clip_with_speedup1)

    tree = et.fromstring(
        otio.adapters.write_to_string(track1, 'mlt_xml')
    )

    assert tree.find('./producer/[@id="clip_with_speedup"]') is not None

    # The adapter creates a new producer with the speed adjustment
    producer_e = tree.find('./producer/[@id="2.0:clip_with_speedup"]')
    assert producer_e is not None
    assert (
        producer_e.find('./property/[@name="mlt_service"]').text ==
        'timewarp'
    )

    playlist1_e = tree.find('.playlist/[@id="speedup"]')
    assert (
        playlist1_e[0].attrib['producer'] ==
        '2.0:clip_with_speedup'
    )

    # Slowdown
    clip_with_slowdown1 = otio.schema.Clip(
        name='clip_with_slowdown',
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(100, 30)
        ),
        media_reference=otio.schema.ExternalReference(
            target_url=path,
            available_range=otio.opentime.TimeRange(
                otio.opentime.RationalTime(0, 30),
                otio.opentime.RationalTime(100, 30)
            )
        )
    )
    clip_with_slowdown1.effects.append(
        otio.schema.LinearTimeWarp(
            time_scalar=-2.
        )
    )

    track2 = otio.schema.Track('speedup')
    track2.append(clip_with_slowdown1)

    tree = et.fromstring(
        otio.adapters.write_to_string(track2, 'mlt_xml')
    )

    # The adapter creates a new producer with the speed adjustment
    assert tree.find('./producer/[@id="-2.0:clip_with_slowdown"]') is not None


def test_freeze_frame():
    path = '/some/path/to/media_file.mov'
    clip_with_freeze1 = otio.schema.Clip(
        name='clip_with_freeze',
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(100, 30)
        ),
        media_reference=otio.schema.ExternalReference(
            target_url=path,
            available_range=otio.opentime.TimeRange(
                otio.opentime.RationalTime(0, 30),
                otio.opentime.RationalTime(100, 30)
            )
        )
    )
    clip_with_freeze1.effects.append(
        otio.schema.FreezeFrame()
    )

    track1 = otio.schema.Track('speedup')
    track1.append(clip_with_freeze1)

    tree = et.fromstring(
        otio.adapters.write_to_string(track1, 'mlt_xml')
    )

    # The adapter creates a new producer with "freeze0.0" suffix where
    # 0.0 is based on the source_range.start_time.value
    producer_e = tree.find(
        './producer/[@id="clip_with_freeze_freeze{}"]'
        .format(clip_with_freeze1.source_range.start_time.value)
    )
    assert producer_e is not None
    assert (
        producer_e.find('./property/[@name="mlt_service"]').text ==
        'hold'
    )


def test_ignoring_generator_reference():
    generator_clip1 = otio.schema.Clip(
        name='generator_clip1',
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(50, 30)
        ),
        media_reference=otio.schema.GeneratorReference(
            name='colorbars',
            generator_kind='SMPTEBars',
            available_range=otio.opentime.TimeRange(
                otio.opentime.RationalTime(0, 30),
                otio.opentime.RationalTime(50, 30)
            )
        )
    )
    track = otio.schema.Track('gen')
    track.append(generator_clip1)

    tree = et.fromstring(
        otio.adapters.write_to_string(track, 'mlt_xml')
    )

    producer_e = tree.find('./producer/[@id="colorbars"]')
    assert producer_e is not None


def test_passing_adapter_arguments():
    clip1 = otio.schema.Clip(
        name='clip1',
        source_range=otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(500, 30)
        )
    )

    track = otio.schema.Track('video')
    track.append(clip1)

    tree = et.fromstring(
        otio.adapters.write_to_string(
            track,
            'mlt_xml',
            width='1920',
            height=1080
        )
    )

    profile_e = tree.find('./profile')
    assert profile_e is not None
    assert int(profile_e.attrib['width']) == 1920
    assert int(profile_e.attrib['height']) == 1080


def test_value_to_string_conversion():
    tl = otio.schema.Timeline()
    mlt = MLTAdapter(tl)
    data = {
        'int_key': 42,
        'float_key': 42.0,
        'str_key': '43'
    }
    converted = mlt._stringify_values(data)

    assert isinstance(converted['int_key'], str)
    assert isinstance(converted['float_key'], str)
    assert isinstance(converted['str_key'], str)


def test_raise_error_mlt_on_read():
    with pytest.raises(AdapterDoesntSupportFunctionError) as err:
        otio.adapters.read_from_file('bogus.mlt')

    assert (
        "Sorry, mlt_xml doesn't support read_from_file." ==
        str(err.value)
    )
