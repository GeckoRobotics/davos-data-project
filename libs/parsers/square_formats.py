"""
Module implementing python file readers for the Square data formats

Reference: 
- https://github.com/GeckoRobotics/sasw-exploration/blob/574f80130080d9de0ca1e4e94a6ea2903fcfdc10/olson_formats.py
- https://github.com/GeckoRobotics/sasw-exploration/tree/574f80130080d9de0ca1e4e94a6ea2903fcfdc10
- https://docs.python.org/3/library/struct.html#format-characters
- https://numpy.org/doc/stable/user/basics.types.html
- http://kbandla.github.io/dpkt/creating_parsers.html
- https://docs.python.org/3/library/struct.html#format-characters
- https://docs.python.org/3/library/array.html#module-array
- https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-nrbf/10b218f5-9b2b-4947-b4b7-07725a2c8127
- https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-nrbf/75b9fe09-be15-475f-85b8-ae7b7558cfe5
- https://numpy.org/doc/stable/user/basics.types.html
- https://numpy.org/doc/stable/user/basics.rec.html

"""
import pprint
import typing as t
from pathlib import Path

import dpkt
import numpy as np
import pint
import tqdm


ureg = pint.get_application_registry()
Q_ = ureg.Quantity


class CompatibilityError(Exception):
    pass


class WinSSS_SW:
    """Reader for the Olson File Format

    Strictly for version > 1.4

    """

    version: float
    header: "FileHeader"
    lines: t.List["LineHeader"]

    @classmethod
    def from_file(cls, filename: Path):
        with open(filename, "rb") as fobj:
            file_contents = fobj.read()
        return cls(file_contents)

    def _check_version(self, version):
        # Check version
        if version < 1.4:
            raise CompatibilityError(
                f"Incompatible File. Expected >= 1.4. Found version {version}."
            )

    @property
    def sample_rate(self):
        # Units of Hz
        period = float(self.header.contents["timePerPointTextBox"]) * Q_("us")
        return (1 / period).to("Hz").m

    @property
    def velocity_p(self):
        # P-wave velocity Units of ft/s
        return float(self.header.contents["velToolStripTextBox"])

    def __init__(self, buf: bytes):
        # File Version "as written"
        _version = Double(buf)
        buf = buf[len(_version) :]
        version = _version.value
        self._check_version(version)
        self.version = version

        Waveform = FullWaveform if version >= 1.7 else ShortWaveform

        # file header
        header = FileHeader(buf)
        buf = buf[len(header) :]
        self.header = header

        # Some number of scan lines
        line_count = self.header.contents["numLines"]
        self.lines = []
        for i in tqdm.trange(line_count, desc="parsing lines", leave=False):
            line = LineHeader(buf)
            buf = buf[len(line) :]
            self.lines.append(line)

            # Some number of waveforms in this line
            wave_count = line.contents["numWaveforms"]
            waves = []
            for j in tqdm.trange(wave_count, desc="parsing waves", leave=False):
                wave = Waveform(buf)
                buf = buf[len(wave) :]
                waves.append(wave)

            line.waves = waves

        # I think the rest is a color palette. Not particularly interesting to
        # us.
        self.end_bytes = buf

    def signals(self):
        """Returns a list of Numpy arrays of scan line signals

        The length of the list is the number of scan lines.
        The array for each scan line has shape: (pulse count, 2, sample count)
            pulse count - the number of excitation pulses recorded in this scan line
            2 - left and right transducer wheels
            sample count - the length in samples of each amplitude signal.

        """
        # Reshape the parsed data:
        scan_lines = []
        location_data = []
        for scan_number in range(len(self.lines) // 2):
            left_line = self.lines[2 * scan_number]
            right_line = self.lines[(2 * scan_number) + 1]

            if left_line.contents["wheel"] == "R":
                left_line, right_line = right_line, left_line

            pulse_count = len(left_line.waves)
            cube = np.stack(
                [
                    np.array([w.wave.array for w in left_line.waves]),
                    np.array([w.wave.array for w in right_line.waves]),
                ],
                axis=1,
            )
            location = np.zeros((pulse_count, 2, 2), dtype=np.float32)
            left_x = left_line.contents["distance"]
            left_y = [w.distance for w in left_line.waves]
            location[:, 0, 0] = left_x
            location[:, 0, 1] = left_y
            right_x = right_line.contents["distance"]
            right_y = [w.distance for w in right_line.waves]
            location[:, 1, 0] = right_x
            location[:, 1, 1] = right_y

            scan_lines.append(cube)
            location_data.append(location)

        return scan_lines, location_data
    
    
class SquareData:
    """Reader for Square Data File Format

    """

#     version: float
#     header: "FileHeader"
#     lines: t.List["LineHeader"]

#     @classmethod
#     def from_file(cls, filename: Path):
#         with open(filename, "rb") as fobj:
#             file_contents = fobj.read()
#         return cls(file_contents)

#     def _check_version(self, version):
#         # Check version
#         if version < 1.4:
#             raise CompatibilityError(
#                 f"Incompatible File. Expected >= 1.4. Found version {version}."
#             )

#     @property
#     def sample_rate(self):
#         # Units of Hz
#         period = float(self.header.contents["timePerPointTextBox"]) * Q_("us")
#         return (1 / period).to("Hz").m

#     @property
#     def velocity_p(self):
#         # P-wave velocity Units of ft/s
#         return float(self.header.contents["velToolStripTextBox"])

    def __init__(self, buf: bytes):
        # file header
        header = FileHeader(buf)
        buf = buf[len(header) :]
        self.header = header

        # get ref data
        num_selected_probes = header.contents["num_selected_probes"]
        num_cycles = header.contents["num_cycles"]
        encoder_size = header.contents["encoder_size"]
        num_points = header.contents["num_points"]
        
        # iterate through probes
        self.probe_data = []
        for probe_i in range(num_selected_probes):
            probe_data_i = ProbeData(buf)
            if len(probe_data_i)!=482:
                print('ERROR: probe_data len {} != 482'.format(len(probe_data_i)))
            buf = buf[len(probe_data_i) :]
            self.probe_data.append(probe_data_i)
            
        # skip reserved2 block
        buf = buf[192 :]
        
        # get angles array
        self.angles_array = np.frombuffer(buf, dtype=np.double, count=num_cycles)
        buf = buf[8*num_cycles : ]
        
        # get exits array
        self.exits_array = np.frombuffer(buf, dtype=np.double, count=num_cycles)
        buf = buf[8*num_cycles : ]
        
        # get Raw PAUT waveform data
        self.raw_paut_waveform_data = np.frombuffer(buf, dtype=np.int8, count=encoder_size*num_cycles*num_points)
        self.raw_paut_waveform_data.shape = (encoder_size, num_cycles, num_points)
        buf = buf[len(self.raw_paut_waveform_data) : ]
        
        # get probe_numbers array
        self.probe_numbers_array = np.frombuffer(buf, dtype=np.int32, count=encoder_size*num_cycles)
        buf = buf[len(self.probe_numbers_array) : ]
        
        # get digital_inputs array
        self.digital_inputs_array = np.frombuffer(buf, dtype=np.int32, count=encoder_size*num_cycles)
        buf = buf[len(self.digital_inputs_array) : ]
        
        # get timestamps array
        self.timestamps_array = np.frombuffer(buf, dtype=np.double, count=encoder_size)
        buf = buf[len(self.timestamps_array) : ]
        
        # skip reserved3 block
        buf = buf[1 :]
        
        # get gates
        gates_data = Gates(buf)
        self.gates = gates_data
        

        


# WinSSS-SW
class Entry(dpkt.Packet):
    """All serialized values use little-endian or machine byte ordering."""

    __byte_order__ = "<"  # little-endian

    def unpack(self, buf):
        super().unpack(buf)
        self.data = b""


class Double(Entry):
    __hdr__ = (("value", "d", 0),)
    

class Uint32(Entry):
    __hdr__ = (("value", "I", 0),)

    
class Int32(Entry):
    __hdr__ = (("value", "i", 0),)


class Int64(Entry):
    __hdr__ = (("value", "q", 0),)


class Boolean(Entry):
    __hdr__ = (("value", "?", 0),)


class String(Entry):
    __hdr__ = (
        # ("pre", "H", 0),
        ("len", "B", 0),
    )

    def unpack(self, buf):
        super().unpack(buf)
        buf = buf[self.__hdr_len__ :]
        self.value = buf[: self.len]
        self.data = b""

    def __len__(self):
        return self.__hdr_len__ + self.len
    
    ## NOTE: the following function has been provided by Jerome from Square Robot for processing their data
#     def get_ms_prefix_length_string( lwld_file ):
#         """

#         """
#         str_len_byte = struct.unpack( 'B', lwld_file.read(1) )[0]
#         str_len = ( str_len_byte & 0x7F )
#         shift_count = 1
#         # This section is kind of from AOS and untested until a string is greater the 127 bytes

#         while str_len_byte > 127:
#             str_len_byte = struct.unpack( 'B', lwld_file.read(1) )[0]
#             add_len = ( str_len_byte & 0x7F )
#             add_len = add_len << (shift_count*7)
#             str_len = str_len + add_len
#             shift_count = shift_count + 1
#         if str_len == 0:
#             return ""
#         return (lwld_file.read( str_len )).decode( 'utf-8' )
    
    
class Reserved(Entry):
    __hdr__ = (("value", "192s", 0),)
    
    
class DepthReceptions(Entry):
    # An array of depth_receptions [double], length 32*8
    __hdr__ = (("value", "256s", 0),) # 32d is now 256s, this is a string not a double now



class Group:
    """Logical grouping of fields

    This differs from dpkt unpacking in that we have to parse each field
    individual because some fields (Strings) are unknown in length so the group
    cannot be parsed in one big block.

    """

    _fields: t.Tuple[
        t.Tuple[str, t.Any],
    ]
    contents: t.Dict
    length: int

    def __init__(self, buf: bytes):
        # Parse the fields into the contents
        self.contents = {}
        # Keep track of total length of the binary data consumed
        self.length = 0
        for attr_name, _type in self._fields:
            # parse and consume one entry from the stream
            entry = _type(buf)
            consumed = len(entry)
            buf = buf[consumed:]
            self.contents[attr_name] = entry.value
            self.length += consumed

    def __len__(self):
        return self.length


class FileHeader(Group):
    _fields = (
        ("encoder_size", Uint32),
        ("num_cycles", Uint32),
        ("num_points", Uint32),
        ("bit_size", Int32),
        ("scan_length", Double),
        ("scan_step", Double),
        ("sampling_period", Double),
        ("vel_1", Double),
        ("vel_2", Double),
        ("vel_3", Double),
        ("thickness", Double),
        ("ascan_type", Int32),
        ("vel_couplant", Double),
        ("ascan_type2", Int32),
        ("sw_version", Int32),
        ("probe_mode", Int32),
        ("num_selected_probes", Int32),
        ("ascan_start", Double),
        ("ascan_range", Double),
        ("compression_type", Int32),
        ("point_factor", Double),
        ("posix_time_start", String),
        ("posix_time_end", String),
        ("nav_trackline_id", String),
        ("nav_num_pulses", String),
        ("reserved1", Reserved),
        ("master_setup_filename", String),
        ("slave_setup_filename", String),
        ("driver_version", String),
        ("cycle_count_per_device", Int32),
        ("gain_analog", Double),
        ("time_slot", Double),
        ("filter_index", Int32),
        ("dac_enabled", Boolean),
    )

class ProbeData(Group):
    _fields = (
        ("selected", Boolean),
        ("element_count", Int32),
        ("pitch", Double),
        ("frequency", Double),
        ("radius", Double),
        ("wedge_enable", Boolean),
        ("wedge_velocity", Double),
        ("wedge_height", Double),
        ("wedge_angle", Double),
        ("specimen_velocity", Double),
        ("specimen_wave", Int32),
        ("specimen_radius", Double),
        ("elem_count", Int32),
        ("depth_emission", Double),
        ("depth_reception_array", DepthReceptions),
        ("num_ddf", Int32),
        ("angle_start", Double),
        ("angle_stop", Double),
        ("angle_step", Double),
        ("elem_start", Int32),
        ("elem_stop", Int32),
        ("elem_step", Int32),
        ("depth_mode", Int32),
        ("start", Double),
        ("range", Double),
        ("timeslot", Double),
        ("trigger", Int32),
        ("io", Int32),
        ("encoder_step", Double),
        ("enc1_type", Int32),
        ("1A", Int32),
        ("1B", Int32),
        ("enc2_type", Int32),
        ("2A", Int32),
        ("2B", Int32),
        ("enc1res", Int64),
        ("enc1div", Int64),
        ("enc2res", Int64),
        ("enc2div", Int64)
    )
    
class Gates(Group):
    _fields = (
        ("gate1_start", Double),
        ("gate1_length", Double),
        ("gate1_thres", Double),
        ("gate2_start", Double),
        ("gate2_length", Double),
        ("gate2_thres", Double),
        ("gate3_start", Double),
        ("gate3_length", Double),
        ("gate3_thres", Double),
    )
    
    
    
    
#-----------------------------------------------------
# Section below this is leftover
#-----------------------------------------------------
    
    
class LineHeader(Group):
    _fields = (
        ("name", String),
        ("wheel", String),
        ("distance", Double),
        ("gain", Int32),
        ("startScan", Double),
        ("direction", Boolean),
        ("minThreshold", Double),
        ("minAmpF", Double),
        ("thicknessMin", Double),
        ("thicknessMax", Double),
        ("ch", Int32),
        ("nominalThickness", Double),
        ("filterPass", String),
        ("f1", Int32),
        ("f2", Int32),
        ("numWaveforms", Int32),
    )

    waves: t.List["Waveform"]


class ShortWaveform(Entry):
    __hdr__ = (
        ("thickness", "d", 0),
        ("f", "i", 0),
        ("thicknessChangeDisabled", "?", 0),
        ("omitted", "?", 0),
        ("distance", "d", 0),
        ("t1", "i", 0),
        ("t2", "i", 0),
        ("t3", "i", 0),
        ("maxAmpF", "d", 0),
        ("dominantFlag", "?", 0),
        ("delaminationFlag", "?", 0),
    )

    def unpack(self, buf: bytes):
        super().unpack(buf)
        self.data = b""
        buf = buf[self.__hdr_len__ :]

        self.wave = Wave(buf)
        buf = buf[len(self.wave) :]

        # a few mask points
        self.mask = Mask(buf)
        buf = buf[len(self.mask) :]

    def __len__(self):
        return self.__hdr_len__ + len(self.wave) + len(self.mask)


class FullWaveform(Entry):
    __hdr__ = (
        ("thickness", "d", 0),
        ("f", "i", 0),
        ("thicknessChangeDisabled", "?", 0),
        ("omitted", "?", 0),
        ("distance", "d", 0),
        # The following gps fields requie version >= 1.7:
        ("timestamp", "q", 0),  # wTime
        ("gpsLat", "d", 0),  # wLat
        ("gpsLon", "d", 0),  # wLong
        ("gpsLatCorr", "d", 0),  # wLatCorr
        ("gpsLonCorr", "d", 0),  # wLonCorr
        ("gpsHeight", "d", 0),  # wHeight
        ("gpsQual", "i", 0),  # wQual
        ("gpsOffsetInchesX", "d", 0),  # GPS Control
        ("gpsOffsetInchesY", "d", 0),  # GPS Control
        ("t1", "i", 0),
        ("t2", "i", 0),
        ("t3", "i", 0),
        ("maxAmpF", "d", 0),
        ("dominantFlag", "?", 0),
        ("delaminationFlag", "?", 0),
    )

    def unpack(self, buf: bytes):
        super().unpack(buf)
        self.data = b""
        buf = buf[self.__hdr_len__ :]

        self.wave = Wave(buf)
        buf = buf[len(self.wave) :]

        # a few mask points
        self.mask = Mask(buf)
        buf = buf[len(self.mask) :]

    def __len__(self):
        return self.__hdr_len__ + len(self.wave) + len(self.mask)


class Wave(Entry):
    # An array of sampled data
    __hdr__ = (("_length", "i", 0),)

    def unpack(self, buf: bytes):
        super().unpack(buf)
        self.data = b""
        assert self._length == 1024 or self._length == 2048
        buf = buf[self.__hdr_len__ :]
        sample_buf = buf[: 4 * self._length]
        self.array = np.frombuffer(sample_buf, dtype=np.int32)

    def __len__(self):
        return self.__hdr_len__ + (4 * self._length)


class Mask(Entry):
    """Mask points describe the regions of the phase diagram that is excluded
    from

    """

    __hdr__ = (("points", "i", 2),)

    def unpack(self, buf: bytes):
        super().unpack(buf)
        buf = buf[self.__hdr_len__ :]
        _len = 0
        points = []
        for i in range(self.points):
            p = MaskP(buf)
            buf = buf[len(p) :]
            points.append(p)
            _len += len(p)

        self._len = _len

    def __len__(self):
        return self.__hdr_len__ + self._len


class MaskP(Entry):
    __hdr__ = (
        ("F1", "d", 0),
        ("F2", "d", 0),
        ("cycle", "i", 0),
    )