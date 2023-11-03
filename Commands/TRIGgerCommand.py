from enum import Enum
import pyvisa

class SWEep(Enum):
    AUTO = 1
    NORM = 2
    SING = 3

class TRIGgerCommand:

    def __init__(self, device: pyvisa.resources.Resource):
        self.device: pyvisa.resources.Resource = device
        self.sweep = self.get_SWEep()
    
    def get_SWEep(self):
        sweep_str = self.device.query(':TRIGger:SWEep?').strip()
        try:
            self.sweep = SWEep[sweep_str]
            return self.sweep
        except KeyError:
            print("Invalid SWEep returned from the device.")
            return None