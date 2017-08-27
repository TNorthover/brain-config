import serial, struct
from fields import SETUP_FIELDS, GLOBAL_FIELDS

class Brain:
    SETUP1 = 0
    SETUP2 = 1
    SETUP3 = 2
    GLOBAL = 0xff

    NAMESPACE_NAMES = {
        'global': GLOBAL,
        'setup1': SETUP1,
        'setup2': SETUP2,
        'setup3': SETUP3,
    }

    CMD_VERSION = 1
    CMD_READ = 3
    CMD_WRITE = 4

    PKT_HEAD = b'UU'
    PKT_TAIL = b'<'

    def __init__(self, serial_name):
        self.brain = serial.Serial(serial_name, 115200)
        if self.version() != b'BRAIN2 3.1.010':
            raise IOError('Incompatible Brain firmware found: {}, expect "BRAIN2 3.1.010"'.format(self.version()))

    def quote(self, s):
        s = s.replace(b'\xc3', b'\xc3\xc3')
        s = s.replace(b'\x3c', b'\xc3\x3c')
        s = s.replace(b'\x55', b'\xc3\x55')
        return s

    def checksum(self, data):
        return sum(data) % 256

    def create_packet(self, cmd, payload):
        pkt = b'\x00' # Sender identifier is hex 0
        pkt += bytes([cmd])
        pkt += payload
        pkt += bytes([self.checksum(pkt)])
        pkt = Brain.PKT_HEAD + self.quote(pkt) + Brain.PKT_TAIL

        return pkt

    def write_packet(self, cmd, payload=bytes([])):
        self.brain.write(self.create_packet(cmd, payload))

    def read_packet(self):
        pkt = b''
        escape = False
        while True:
            pkt += self.brain.read(1)
            if escape:
                escape = False
                continue
            if pkt[-1] == 0xc3:
                # Escape. Next character is not special. This affects 0x55, 0x3c
                # and (I'm assuming) 0xc3 itself, which would otherwise signal
                # the start/end of a packet, or an escape.
                pkt = pkt[:-1]
                escape = True
            elif pkt.endswith(Brain.PKT_TAIL):
                break

        if not pkt.startswith(Brain.PKT_HEAD):
            raise ValueError('Malformed packet header from Brain: {}'.format(pkt))

        checksum = self.checksum(pkt[2:-2])
        if checksum != pkt[-2]:
            raise ValueError('Incorrect packet checksum from Brain: {}'.format(pkt))

        if pkt[2] != 0xff:
            raise ValueError('Response from Brain has invalid sender: {}'.format(pkt))

        # Everything looks good. Return a cmd/payload pair.
        return (pkt[3], pkt[4:-2])

    def read(self, namespace, addr):
        self.write_packet(Brain.CMD_READ, bytes([namespace, addr]))
        cmd, resp = self.read_packet()
        if cmd != Brain.CMD_READ:
            raise ValueError('Brain misinterpreted read command as {}'.format(cmd))

        return struct.unpack('<H', resp)[0]

    def write(self, namespace, addr, data):
        assert(data >= 0 and data <= 0xffff)

        payload = bytes([namespace, addr])
        payload += struct.pack('<H', data)

        self.write_packet(Brain.CMD_WRITE, payload)
        cmd, resp = self.read_packet()

        if cmd != Brain.CMD_WRITE:
            raise ValueError('Brain misinterpreted read command as {}'.format(cmd))

        if resp[0] != namespace or resp[1] != addr:
            raise ValueError('Brain misinterpreted read address: {} {}'.format(resp[0], resp[1]))

        written_data = struct.unpack('<H', resp[2:4])[0]
        if written_data != data:
            raise ValueError('Brain wrote incorrect value: {}'.format(written_data))

    def parse_name(self, val):
        if val.count('.') != 1:
            raise ValueError('Configuration parameter should have namespace and name separated by "."')

        namespace, name = val.split('.')
        if namespace not in Brain.NAMESPACE_NAMES:
            raise ValueError('Top-level namespace should be one of "global", "setup1", "setup2" or "setup3"')
        namespace = Brain.NAMESPACE_NAMES[namespace]

        if namespace == Brain.GLOBAL:
            if name not in GLOBAL_FIELDS:
                raise ValueError('Configuration parameter {} not in global namespace'.format(name))
            return (namespace, GLOBAL_FIELDS.index(name))
        else:
            if name not in SETUP_FIELDS:
                raise ValueError('Configuration parameter {} not in setup namespace'.format(name))
            return (namespace, SETUP_FIELDS.index(name))

    def version(self):
        self.write_packet(Brain.CMD_VERSION)
        return self.read_packet()[1]

    def __getitem__(self, item):
        namespace, addr = self.parse_name(item)
        return self.read(namespace, addr)

    def __setitem__(self, item, val):
        namespace, addr = self.parse_name(item)
        return self.write(namespace, addr, val)

if __name__ == '__main__':
    import sys
    b = Brain(sys.argv[1])
#    pkt = bytes([0x55, 0x55, 0x00, 0x04, 0xff, 0x30, 0xc3, 0x55, 0x1e, 0xa6, 0x3c])
#    print('About to send: {}'.format(pkt))
#    b.brain.write(pkt)
#    print(b.read_packet())
#    b.brain.write(bytes([0x55, 0x55, 0x00, 0x03, 0xff, 0x30, 0x32, 0x3c]))
#    print(b.read_packet())
#    print(GLOBAL_FIELDS[0x30])
