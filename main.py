import pyvisa
import time
import matplotlib.pyplot as plt
import Commands.WAVeformCommands as cmd
import Commands.TRIGgerCommand as trigger

if __name__=="__main__":
    device = pyvisa.ResourceManager().open_resource("TCPIP::169.254.245.109::INSTR")
    print(device.query('*IDN?'))
    trigger_cmd = trigger.TRIGgerCommand(device = device)
    waveform_cmd = cmd.WAVeformCommands(device = device, memory_depth = cmd.MemoryDepth.DS1102Z_E, trigger=trigger_cmd)
    waveform_cmd.FORMat(cmd.Format.BYTE)
    waveform_cmd.SOURce(cmd.Source.CHAN1)
    waveform_cmd.MODE(cmd.Mode.MAX)
    #waveform_cmd.get_DATA()
    waveform_cmd.get_data_range(1, 24000000)
    (t, v) = waveform_cmd.convert_voltage()
    plt.plot(t, v)
    plt.grid(True)
    plt.show()
