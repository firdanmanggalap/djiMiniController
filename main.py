# Modifikasi khusus DJI MR1SD25 ke Virtual Xbox 360 Controller
import serial
import vgamepad as vg
import argparse

parser = argparse.ArgumentParser(description='Mavic Mini RC <-> Xbox 360 Interface.')
parser.add_argument('-p', '--port', help='RC Serial Port', required=True)
parser.add_argument('-i', '--invert', help='Invert lv, lh, rv, rh, or cam axis', nargs='*', default=['lv', 'rv'])

args = parser.parse_args()
invert = frozenset(args.invert)

# Nilai batas tengah dan maksimum untuk sirkuit XInput/Xbox (-32768 s/d 32767)
# Berbeda dengan vJoy yang pakainya range positif 0 - 32768
def parseInputXbox(input_bytes, name):
    # Hitung nilai mentah bawaan DJI (0 s/d 32768)
    vjoy_val = (int.from_bytes(input_bytes, byteorder='little') - 364) * 4096 // 165
    
    # KONEKSI NORMAL: Biarkan sirkuit asli DJI yang menentukan arahnya
    # (Kita hapus fungsi invert otomatis yang bikin angkanya jadi positif pas di bawah)
        
    # Konversi dari range vJoy ke range Xbox Short (-32768 s/d 32767)
    xbox_val = int((vjoy_val / 32768) * 65535 - 32768)
    
    # Pembatas agar tidak overflow/eror sirkuit
    return max(-32768, min(32767, xbox_val))

# Ping Data bawaan DJI Mavic Mini
pingData = bytearray.fromhex('550d04330a0e0300400601f44a')

# Buka Serial Port USB DJI
try:
    s = serial.Serial(port=args.port, baudrate=115200)
    print('Opened serial device:', s.name)
except serial.SerialException as e:
    print('Could not open serial device:', e)
    exit(1)

# Buka Sirkuit Virtual Xbox 360 (VIGEM)
try:
    gamepad = vg.VX360Gamepad()
    print('Sirkuit Virtual Xbox 360 BERHASIL Dibuat!')
except Exception as e:
    print('Gagal membuat sirkuit Xbox. Pastikan ViGEmBus sudah terinstall:', e)
    exit(1)

print('\n=== REMOTE DJI SEBAGAI STICK XBOX AKTIF ===')
print('Press Ctrl+C to stop.\n')

try:
    while True:
        s.write(pingData)
        print('\rPinged. ', end='')

        data = s.readline()

        if len(data) == 38:
            # Parse data analog stick remote
            left_vertical = parseInputXbox(data[13:15], 'lv')
            left_horizontal = parseInputXbox(data[16:18], 'lh')
            right_vertical = parseInputXbox(data[10:12], 'rv')
            right_horizontal = parseInputXbox(data[7:9], 'rh')
            camera = parseInputXbox(data[19:21], 'cam') # Dial kamera dipetakan ke trigger jika butuh

            # Masukkan data stick ke Controller Xbox Virtual
            gamepad.left_joystick(x_value=left_horizontal, y_value=left_vertical)
            gamepad.right_joystick(x_value=right_horizontal, y_value=right_vertical)
            
            # Map dial kamera ke Right Trigger secara opsional
            trigger_val = int(((camera + 32768) / 65535) * 255)
            gamepad.right_trigger(value=max(0, min(255, trigger_val)))

            # Kirim perintah data ke Windows secara instan
            gamepad.update()

            # Log monitor ke layar monitor
            print('L: H{:06d},V{:06d}; R: H{:06d},V{:06d}'.format(left_horizontal, left_vertical, right_horizontal, right_vertical), end='')
            
except serial.SerialException as e:
    print('\n\nCould not read/write:', e)
except KeyboardInterrupt:
    print('\n\nDetected keyboard interrupt.')
    pass

print('Stopping.')