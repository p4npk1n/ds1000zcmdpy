import pyvisa
from enum import Enum
from Commands.TRIGgerCommand import TRIGgerCommand
from Commands.TRIGgerCommand import SWEep
import numpy as np


class MemoryDepth(Enum):
    DS1102Z_E = 24000000 # 24Mpts

class Source(Enum):
    D0 = 0
    D1 = 1
    D2 = 2
    D3 = 3
    D4 = 4
    D5 = 5
    D6 = 6
    D7 = 7
    D8 = 8
    D9 = 9
    D10 = 10
    D11 = 11
    D12 = 12
    D13 = 13
    D14 = 14
    D15 = 15
    CHAN1 = 16
    CHAN2 = 17
    CHAN3 = 18
    CHAN4 = 19
    MATH = 20

class Mode(Enum):
    NORM = 1
    MAX = 2
    RAW = 3

class MaxModeRange:
    def __init__(self, memory_depth: MemoryDepth):
        self.NORM = 1200
        self.MAX = memory_depth.value
        self.RAW = memory_depth.value
        self.value: int = None

    def set_maxmodrange(self, mode: Mode):
        match mode:
            case mode.MAX:
                self.value = self.MAX
            case mode.RAW:
                self.value = self.RAW
            case mode.NORM:
                self.value = self.NORM

class MaxDatasize(Enum):
    WORD = 125000
    BYTE = 250000 
    ASC = 15625

class Format(Enum):
    WORD = 1 
    BYTE = 2
    ASC = 3

class WAVeformCommands:
    def __init__(self, device: pyvisa.resources.Resource, memory_depth: MemoryDepth, trigger: TRIGgerCommand):
        self.device: pyvisa.resources.Resource = device
        self.memory_depth: MemoryDepth = memory_depth
        self.max_moderange: MaxModeRange = MaxModeRange(self.memory_depth)
        self.data = None
        self.trigger: TRIGgerCommand = trigger

        self.start_point: int
        self.stop_point: int 
        self.origin = self.TwoDiv(x = 0.0, y = 0.0)
        self.reference = self.TwoDiv(x = 0.0, y = 0.0)
        self.increment = self.TwoDiv(x = 0.0, y = 0.0)
        self.source: Source
        self.format_type: Format
        self.max_datasize: MaxDatasize
        self.mode: Mode

        self.get_SOURce()
        self.get_STARt()
        self.get_STOP()
        self.get_MODE()
        self.get_FORMat()
        self.get_ORigin()
        self.get_REFrenece()
        self.get_INCrement()
    
    class TwoDiv:
        def __init__(self, x = None, y = None):
            self.x = None
            self.y = None

    def set_SOURce(self, source: Source):
        self.device.write(':WAVeform:SOURce {}'.format(source.name))

    def get_SOURce(self) -> Source:
        source_str = self.device.query(':WAVeform:SOURce?').strip()
        try:
            source = Source[source_str]
            self.source = source
            return source
        except KeyError:
            print("Invalid source returned from the device.")
            return None
    
    def SOURce(self, source: Source) -> Source:
        self.set_SOURce(source)
        return self.get_SOURce()
        
    
    def set_MODE(self, mode: Mode):
        self.device.write(':WAVeform:MODE {}'.format(mode.name))

    def get_MODE(self) -> Mode:
        mode_str = self.device.query(':WAVeform:MODE?').strip()
        try:
            mode = Mode[mode_str]
            if mode == Mode.MAX or mode == Mode.RAW:
                if self.trigger.sweep is not SWEep.SING:
                    print("The mode MAX and RAW has to set the triger mode to SINGLE")
                    return None
            self.mode = mode 
            self.max_moderange.set_maxmodrange(self.mode)
            return mode
        except KeyError:
            print("Invalid mode returned from the device.")
            return None
    
    def MODE(self, mode: Mode) -> Mode:
        self.set_MODE(mode)
        return self.get_MODE()

    def set_FORMat(self, format_type: Format):
        self.device.write(':WAVeform:FORMat {}'.format(format_type.name))

    def get_FORMat(self) -> (Format, MaxDatasize):
        format_str = self.device.query(':WAVeform:FORMat?').strip()
        try:
            self.format_type = Format[format_str]
            self.max_datasize = MaxDatasize[format_str]
            return (self.format_type, self.max_datasize)
        except ValueError:
            print("Invalid format returned from the device.")
            return None
    
    def FORMat(self, format_type: Format) -> (Format, MaxDatasize):
        self.set_FORMat(format_type)
        return self.get_FORMat()

    def set_STARt(self, start_point: int):
        if self.max_moderange.value < start_point:
            return None 
        self.device.write(':WAVeform:STARt {}'.format(start_point))

    def get_STARt(self) -> int:
        self.start_point = int(self.device.query(':WAVeform:STARt?').strip())
        return self.start_point
    
    def STARt(self, start_point: int) -> int:
        self.set_STARt(start_point)
        return self.get_STARt()

    def set_STOP(self, stop_point: int):
        if (stop_point - self.start_point)  > self.max_datasize.value:
            print("the points from start to stop is exceeded max datasize")
            return None
        if stop_point > self.max_moderange.value:
            print("the stop point is exceeded max datasize")
            return None
        self.device.write(':WAVeform:STOP {}'.format(stop_point))
        self.stop_point = stop_point

    def get_STOP(self) -> int:
        self.stop_point = int(self.device.query(':WAVeform:STOP?').strip())
        return self.stop_point
    
    def STOP(self, stop_point: int):
        self.set_STOP(stop_point)
        return self.get_STOP()

    def get_DATA(self):
        match self.format_type:
            case Format.ASC:
                data = self.device.query(':WAVeform:DATA?')
                self.data = [float(value) for value in data[11:].split(',')]
            case Format.BYTE:
                self.data = self.device.query_binary_values(':WAVeform:DATA?', datatype='B', chunk_size=self.max_datasize.value)
                
            case Format.WORD:
                self.data = self.device.query_binary_values(':WAVeform:DATA?', datatype='H')
        return self.data

    def convert_voltage(self):
        v = []
        match self.format_type:
            case Format.BYTE:
                v = [(float(value) - self.origin.y - self.reference.y) * self.increment.y for value in self.data]
            case Format.WORD:
                # In the WORD format, each data point is encoded in 16 bits (2 bytes).
                # However, according to the document, only the lower 8 bits are used, and the upper 8 bits are set to 0.
                v = [(float(value) - self.origin.y - self.reference.y) * self.increment.y for value in self.data]
            case Format.ASC:
                # In the ASCII format, the data points are already encoded as voltage values.
                # Therefore, no additional conversion is required.
                v = self.data
        t = [self.origin.x + i * self.increment.x for i in range(len(self.data))]
        return (t, v)

    def get_XINCrement(self) -> float:
        result = self.device.query(':WAVeform:XINCrement?')
        try:
            self.increment.x = float(result)
        except ValueError:
            print("can not convert to float")
            return None
        return self.increment.x

    def get_YINCrement(self) -> float:
        result = self.device.query(':WAVeform:YINCrement?')
        try:
            self.increment.y = float(result)
        except ValueError:
            print("can not convert to float")
            return None
        return self.increment.y

    def get_INCrement(self) -> (float, float):
        return (self.get_XINCrement(), self.get_YINCrement())
    
    def get_XORigin(self) -> float:
        result = self.device.query(':WAVeform:XORigin?')
        try:
            self.origin.x = float(result)
        except ValueError:
            print("can not convert to float")
            return None
        return self.origin.x

    def get_YORigin(self) -> float:
        result = self.device.query(':WAVeform:YORigin?')
        try:
            self.origin.y = float(result)
        except ValueError:
            print("can not convert to float")
            return None
        return self.origin.y

    def get_ORigin(self) -> (float, float):
        return (self.get_XORigin(), self.get_YORigin())

    def get_XREFerence(self) -> float:
        result = self.device.query(':WAVeform:XREFerence?')
        try:
            self.reference.x = float(result)
        except ValueError:
            print("can not convert to float")
            return None
        return self.reference.x

    def get_YREFerence(self) -> float:
        result = self.device.query(':WAVeform:YREFerence?')
        try:
            self.reference.y = float(result)
        except ValueError:
            print("can not convert to float")
            return None
        return self.reference.y

    def get_REFrenece(self) -> (float, float):
        return (self.get_XREFerence(), self.get_YREFerence())


    def get_data_range(self, start_point: int, stop_point: int):
        if start_point <= 0:
            print("start point is minus")
            return None
        total_data_points = stop_point - start_point + 1
        if total_data_points > self.max_moderange.value:
            print("the total_data_points is exceeded the max_moderange")
        data = np.zeros(total_data_points)
        current_start = start_point
        index = 0
        while total_data_points > 0:
            data_points_to_fetch = min(self.max_datasize.value, total_data_points)
            print(f"start point = {current_start}, end point = {current_start + data_points_to_fetch - 1}")
            self.STARt(current_start)
            self.STOP(current_start + data_points_to_fetch - 1)
            print("aaaaaaaa")
            fetched_data = self.get_DATA()
            print("iiiiiiii")
            data[index:index + data_points_to_fetch] = fetched_data
            print("uuuuuuuuu")
            #data.extend(fetched_data)
            current_start += data_points_to_fetch
            total_data_points -= data_points_to_fetch
            index += data_points_to_fetch
        self.data = data
        return self.data