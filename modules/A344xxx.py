try:
    import pyvisa
    PYVISA_AVAILABLE = True
except ImportError:
    PYVISA_AVAILABLE = False
    print("pyvisa not available. Install with: pip install pyvisa")

import time
import os
from enum import Enum, auto
import sys
import datetime

class Range_state_t(Enum):
  DCI_3A = auto()
  DCI_1A = auto()
  DCI_100mA = auto()
  DCI_10mA = auto()
  DCV_100V = auto()
  DCV_10V = auto()
  DCV_1V = auto()
  range_max = auto()

count_list = []
avg_list = []
min_list = []
max_list = []
count = 0
avg_value = 0.0
min_value = 0.0
max_value = 0.0
read_flag = False
avg_running_flag = False
force_stop_flag = False

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
elif __file__:
    application_path = os.path.dirname(__file__)
keysight_path_64 = 'C:\\Program Files (x86)\\Keysight\\IO Libraries Suite\\bin'
keysight_path_32 = 'C:\\Program Files\\Keysight\\IO Libraries Suite\\bin'

rm = None  # Global ResourceManager

def init_resource_manager():
    """ResourceManager를 초기화하거나 재초기화"""
    global rm
    if not PYVISA_AVAILABLE:
        print("pyvisa not available, skipping ResourceManager initialization")
        return False
    try:
        if os.path.isdir(keysight_path_64):
            os.add_dll_directory(keysight_path_64)
            rm = pyvisa.ResourceManager('ktvisa32')
            print(f"ResourceManager initialized: {rm}")
            return True
        elif os.path.isdir(keysight_path_32):
            os.add_dll_directory(keysight_path_32)
            rm = pyvisa.ResourceManager('ktvisa32')
            print(f"ResourceManager initialized: {rm}")
            return True
        else:
            print("Keysight IO Libraries Suite not found")
            return False
    except Exception as ex:
        print(f"Failed to initialize ResourceManager: {ex}")
        import traceback
        traceback.print_exc()
        return False

# 최초 초기화 시도
if PYVISA_AVAILABLE:
    if not init_resource_manager():
        print("WARNING: ResourceManager initialization failed at module load")
        rm = None
else:
    rm = None

def CMD_Write(myPna, cmd):
    try:
        myPna.write(cmd)

    except  Exception as ex:
        print(ex)

def CMD_Read(myPna, cmd, print_en = False):
    try:
        myPna.write(cmd)
        result = myPna.read()
        if print_en:
            print(result)
        return result

    except Exception as ex:
        print(f"CMD_Read error (cmd={cmd}): {ex}")
        return None


def CMD_Reset(myPna):
    try:
        myPna.timeout =  10000
        # CMD_Write(myPna,"*RST")
        CMD_Write(myPna,"*CLS")

    except  Exception as ex:
        print(ex)

def set_range(myPna,range_state, nplc_high=True, set_nplc=True):
    try:
        if range_state == Range_state_t.DCI_3A:
            CMD_Write(myPna,"CONF:CURR:DC 3 A")
        elif range_state == Range_state_t.DCI_1A:
            CMD_Write(myPna,"CONF:CURR:DC 1 A")
        elif range_state == Range_state_t.DCI_100mA:
            CMD_Write(myPna,"CONF:CURR:DC 100 mA")
        elif range_state == Range_state_t.DCI_10mA:
            CMD_Write(myPna,"CONF:CURR:DC 10 mA")
        elif range_state == Range_state_t.DCV_100V:
            CMD_Write(myPna,"CONF:VOLT:DC 100 V")
        elif range_state == Range_state_t.DCV_10V:
            CMD_Write(myPna,"CONF:VOLT:DC 10 V")
        elif range_state == Range_state_t.DCV_1V:
            CMD_Write(myPna,"CONF:VOLT:DC 1 V")

        # NPLC 설정: set_nplc=False인 경우 NPLC 설정을 건너뜀 (별도로 설정할 경우)
        if set_nplc:
            # NPLC 설정: 전압/전류 모드에 따라 다른 명령 사용
            if nplc_high:
                if range_state.value > Range_state_t.DCI_10mA.value:
                    # DCV 모드
                    CMD_Write(myPna,"VOLT:DC:NPLC 10")
                else:
                    # DCI 모드
                    CMD_Write(myPna,"CURR:DC:NPLC 10")
            else:
                if range_state.value > Range_state_t.DCI_10mA.value:
                    # DCV 모드
                    CMD_Write(myPna,"VOLT:DC:NPLC 0.02")
                else:
                    # DCI 모드
                    CMD_Write(myPna,"CURR:DC:NPLC 0.02")

    except  Exception as ex:
        print(ex)

def set_nplc(myPna, nplc_value, range_state=None):
    """NPLC 값을 설정합니다"""
    try:
        # 전압 모드인지 전류 모드인지 확인
        if range_state and range_state.value > Range_state_t.DCI_10mA.value:
            # DCV 모드: 전압 NPLC 설정
            CMD_Write(myPna, f"VOLT:DC:NPLC {nplc_value}")
        else:
            # DCI 모드: 전류 NPLC 설정
            CMD_Write(myPna, f"CURR:DC:NPLC {nplc_value}")
    except Exception as ex:
        print(ex)

def optimize_for_speed(myPna, range_state=None):
    """
    고속 측정을 위한 최적화 설정
    - Auto-zero 비활성화: 매 측정마다 영점 보정하지 않음 (속도 10배 향상)
    - Aperture time 최소화: NPLC와 별개로 aperture time 설정
    - Display update 비활성화: 디스플레이 업데이트로 인한 지연 제거

    주의: 정확도가 약간 감소할 수 있음 (일반적으로 무시 가능한 수준)
    """
    try:
        print("A344xxx: Optimizing for speed...")

        # 1. Auto-zero 비활성화 (속도 향상의 핵심) => 오차 발생으로 인해 disable
        # AUTO: 매 측정마다 영점 보정 (느림, 정확)
        # ONCE: 한 번만 영점 보정
        # OFF: 영점 보정 안 함 (빠름)
        if range_state and range_state.value > Range_state_t.DCI_10mA.value:
            # DCV 모드
            # CMD_Write(myPna, "VOLT:DC:ZERO:AUTO OFF")
            CMD_Write(myPna, "VOLT:DC:ZERO:AUTO ON")
            # print("  - Auto-zero disabled for voltage measurements")
        else:
            # DCI 모드
            # CMD_Write(myPna, "CURR:DC:ZERO:AUTO OFF")
            CMD_Write(myPna, "CURR:DC:ZERO:AUTO ON")
            # print("  - Auto-zero disabled for current measurements")

        # 2. Aperture mode를 NPLC로 설정 (기본값이지만 명시적으로)
        # APER: Aperture time 모드 (고정 시간)
        # NPLC: Power line cycle 모드 (전원 주파수에 동기화)
        if range_state and range_state.value > Range_state_t.DCI_10mA.value:
            CMD_Write(myPna, "SENS:VOLT:DC:APER:MODE NPLC")
            print("  - Aperture mode: NPLC (voltage)")
        else:
            CMD_Write(myPna, "SENS:CURR:DC:APER:MODE NPLC")
            print("  - Aperture mode: NPLC (current)")

        # 3. Display 비활성화 (측정 중 디스플레이 업데이트 안 함)
        CMD_Write(myPna, "DISP:TEXT:CLE")
        CMD_Write(myPna, "DISP OFF")
        print("  - Display updates disabled")

        # 4. Beeper 비활성화 (불필요한 지연 제거)
        CMD_Write(myPna, "SYST:BEEP:STAT OFF")
        print("  - Beeper disabled")

        print("A344xxx: Speed optimization complete")
        return True

    except Exception as ex:
        print(f"optimize_for_speed error: {ex}")
        import traceback
        traceback.print_exc()
        return False

def restore_normal_settings(myPna, range_state=None):
    """
    optimize_for_speed에서 변경한 설정들을 원래대로 복구
    측정 종료 시 호출하여 기기를 정상 상태로 되돌림
    """
    try:
        print("A344xxx: Restoring normal settings...")

        # 1. Auto-zero 원래대로 (AUTO: 매 측정마다 영점 보정)
        if range_state and range_state.value > Range_state_t.DCI_10mA.value:
            # DCV 모드
            CMD_Write(myPna, "VOLT:DC:ZERO:AUTO ON")
            print("  - Auto-zero restored to ON (voltage)")
        else:
            # DCI 모드
            CMD_Write(myPna, "CURR:DC:ZERO:AUTO ON")
            print("  - Auto-zero restored to ON (current)")

        # 2. Display 활성화
        CMD_Write(myPna, "DISP ON")
        print("  - Display enabled")

        # 3. Beeper 활성화
        CMD_Write(myPna, "SYST:BEEP:STAT ON")
        print("  - Beeper enabled")

        print("A344xxx: Normal settings restored")
        return True

    except Exception as ex:
        print(f"restore_normal_settings error: {ex}")
        import traceback
        traceback.print_exc()
        return False

def get_nplc(myPna, range_state=None):
    """현재 NPLC 값을 읽어옵니다"""
    try:
        # 전압 모드인지 전류 모드인지 확인
        if range_state and range_state.value > Range_state_t.DCI_10mA.value:
            # DCV 모드: 전압 NPLC 읽기
            result = CMD_Read(myPna, "VOLT:DC:NPLC?")
        else:
            # DCI 모드: 전류 NPLC 읽기
            result = CMD_Read(myPna, "CURR:DC:NPLC?")
        return float(result) if result else None
    except Exception as ex:
        print(ex)
        return None


# ============================================================================
# 디지타이저 모드 함수들 (고속 샘플링)
# ============================================================================

def set_digitizer_mode(myPna, nplc_value=0.001, sample_count=100, range_state=None):
    """
    디지타이저 모드 설정 (고속 연속 측정)

    Args:
        myPna: VISA 디바이스 객체
        nplc_value: NPLC 값 (0.001 ~ 10)
        sample_count: 한 번에 측정할 샘플 개수 (1 ~ 1,000,000)
        range_state: Range_state_t (전압/전류 모드 구분)

    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"A344xxx Digitizer: Configuring mode (NPLC={nplc_value}, samples={sample_count})")

        # 1. 샘플 카운트 설정
        CMD_Write(myPna, f"SAMP:COUN {sample_count}")

        # 2. NPLC 설정 (전압/전류 모드에 따라)
        if range_state and range_state.value > Range_state_t.DCI_10mA.value:
            # DCV 모드
            CMD_Write(myPna, f"VOLT:DC:NPLC {nplc_value}")
        else:
            # DCI 모드
            CMD_Write(myPna, f"CURR:DC:NPLC {nplc_value}")

        # 3. 트리거 소스 설정 (즉시 시작)
        CMD_Write(myPna, "TRIG:SOUR IMM")

        # 4. 트리거 카운트 설정 (1회 트리거로 sample_count개 측정)
        CMD_Write(myPna, "TRIG:COUN 1")

        print(f"A344xxx Digitizer: Configuration complete")
        return True

    except Exception as ex:
        print(f"set_digitizer_mode error: {ex}")
        import traceback
        traceback.print_exc()
        return False


def start_digitizer_measurement(myPna):
    """
    디지타이저 측정 시작 (INIT 명령)

    Returns:
        True if successful, False otherwise
    """
    try:
        # INIT 명령: 측정 시작
        CMD_Write(myPna, "INIT")
        return True

    except Exception as ex:
        print(f"start_digitizer_measurement error: {ex}")
        return False


def wait_digitizer_complete(myPna, timeout_ms=10000):
    """
    디지타이저 측정 완료 대기

    Args:
        myPna: VISA 디바이스 객체
        timeout_ms: 타임아웃 (밀리초)

    Returns:
        True if completed, False if timeout
    """
    try:
        import time
        start_time = time.time()
        timeout_sec = timeout_ms / 1000.0

        # *OPC? 명령: Operation Complete 쿼리
        # 측정이 완료되면 "1" 반환
        result = CMD_Read(myPna, "*OPC?")

        # 타임아웃 체크
        elapsed = time.time() - start_time
        if elapsed > timeout_sec:
            print(f"wait_digitizer_complete: Timeout after {timeout_ms}ms")
            return False

        if result and result.strip() == "1":
            return True
        else:
            print(f"wait_digitizer_complete: Unexpected response: {result}")
            return False

    except Exception as ex:
        print(f"wait_digitizer_complete error: {ex}")
        import traceback
        traceback.print_exc()
        return False


def read_digitizer_data(myPna):
    """
    디지타이저 버퍼에서 데이터 일괄 읽기

    Returns:
        List of float values, or None if error
    """
    try:
        # FETCH? 명령: 버퍼에서 데이터 읽기 (측정 완료 후)
        result = CMD_Read(myPna, "FETCH?")

        if result is None or result == "":
            print("read_digitizer_data: No data returned")
            return None

        # 쉼표로 구분된 값들 파싱
        # 예: "+1.234567E-03,+1.234568E-03,+1.234569E-03,..."
        values_str = result.split(',')
        values = [float(v) for v in values_str]

        # print(f"read_digitizer_data: Read {len(values)} samples")
        return values

    except Exception as ex:
        print(f"read_digitizer_data error: {ex}")
        import traceback
        traceback.print_exc()
        return None

def get_current_value(myPna):
    try:
        '''
        if current_range.value<= Range_state_t.DCI_10mA.value:
            return CMD_Read(myPna,"MEAS:CURR:DC?")
        else:
            return CMD_Read(myPna,"MEAS:VOLT:DC?")
        '''
        result = CMD_Read(myPna,"READ?")
        if result is None:
            print("get_current_value: CMD_Read returned None")
            return None

        # 측정값 유효성 검증
        try:
            value = float(result)
            # 측정 범위 검증: ±1000 초과 시 에러로 간주
            if abs(value) > 1000:
                print(f"get_current_value: Invalid value detected: {value} (raw={result})")
                return None
            return result
        except ValueError:
            print(f"get_current_value: Failed to parse value: {result}")
            return None

    except Exception as ex:
        print(f"get_current_value error: {ex}")
        import traceback
        traceback.print_exc()
        return None


def device_info(myPna):
    try:
        myPna.write("*IDN?")
        result = myPna.read()
        # ASCII 디코딩 에러 방지: bytes를 UTF-8로 안전하게 디코딩
        if isinstance(result, bytes):
            return result.decode('utf-8', errors='ignore')
        return str(result)
    except Exception as ex:
        print(f"device_info error: {ex}")
        return "Unknown device"

def avg_read_data():
    global count
    global avg_value
    global min_value
    global max_value
    global read_flag
    global avg_running_flag
    if read_flag and avg_running_flag:
        read_flag = False
        return [count,avg_value,min_value,max_value,True]
    else:
        return [0,0,0,0,False]

def avg_force_stop():
    global force_stop_flag
    force_stop_flag = True

def avg_test(myPna,range_init,test_count):
    global count
    global avg_value
    global min_value
    global max_value
    global read_flag
    global avg_running_flag
    global force_stop_flag
    try:
        # CMD_Reset(myPna)
        set_range(myPna,range_init, nplc_high=False)
        CMD_Write(myPna,"SAMP:COUN %d"%test_count)
        # CMD_Read(myPna,"SAMP:COUN?",True)
        CMD_Write(myPna,"CALCulate:FUNCtion AVERage")
        # CMD_Read(myPna,"CALCulate:FUNCtion?",True)
        CMD_Write(myPna,"CALCulate:STATe ON")
        # CMD_Read(myPna,"CALCulate:STATe?",True)

        CMD_Write(myPna,"INIT")
        force_stop_flag = False
        while True:
            time.sleep(1)
            avg_running_flag = True
            count_tmp = int(float(CMD_Read(myPna,"CALCulate:AVERage:COUNt?")))
            avg_value_tmp = float(CMD_Read(myPna,"CALCulate:AVERage:AVERage?"))
            min_value_tmp = float(CMD_Read(myPna,"CALCulate:AVERage:MINimum?"))
            max_value_tmp = float(CMD_Read(myPna,"CALCulate:AVERage:MAXimum?"))
            count = count_tmp
            avg_value = avg_value_tmp
            min_value = min_value_tmp
            max_value = max_value_tmp
            read_flag = True
            print("%s %d %s %s %s"%(datetime.datetime.now(),count, prinr(avg_value), prinr(min_value), prinr(max_value)))
            if count >= test_count or force_stop_flag:
                CMD_Write(myPna,"CALCulate:STATe OFF")
                # CMD_Read(myPna,"CALCulate:STATe?",True)
                avg_running_flag = False
                break

        myPna.write("CALCulate:STATe OFF")

        read_flag = False
        return [count,avg_value,min_value,max_value]

    except  Exception as ex:
        avg_running_flag = False
        print(ex)

        return [0,0,0,0]

def get_value_range(value):
    try:
        if value >= 1 or value <= -1:
            return ['',value]
        elif value >= 0.001 or value <= -0.001:
            return ['m',value*1000]
        else:
            return ['u',value*1000000]

    except  Exception as ex:
        print(ex)
        return ['',value]

def prinr(value):
    try:
        result = get_value_range(value)
        return "%f %s"%(result[1],result[0])

    except  Exception as ex:
        print(ex)
        return "%f"%value

def reset_usb_device(device_address):
    """USB 장치를 강제로 리셋 시도"""
    global rm
    try:
        print(f"Attempting to reset USB device: {device_address}")
        # open_resource with exclusive lock 해제 시도
        instrument = rm.open_resource(device_address,
                                      timeout=500,
                                      open_timeout=500,
                                      access_mode=pyvisa.constants.AccessModes.no_lock)

        # clear 명령으로 디바이스 상태 초기화
        try:
            instrument.clear()
            print(f"Device cleared: {device_address}")
        except:
            pass

        # 즉시 닫기
        try:
            instrument.close()
        except:
            pass

        return True
    except Exception as ex:
        print(f"Reset failed for {device_address}: {ex}")
        return False

def get_equipment():
    """연결된 장비 목록을 반환"""
    global rm

    # ResourceManager 확인
    if rm is None:
        print("ERROR: ResourceManager is None! Trying to reinitialize...")
        if not init_resource_manager():
            raise Exception("ResourceManager initialization failed. Cannot scan devices.")

    try:
        dev_list = rm.list_resources()
        print(f"Found {len(dev_list)} VISA resources")
    except Exception as ex:
        print(f"ERROR: rm.list_resources() failed: {ex}")
        raise

    # 실제 연결된 장비를 저장할 리스트입니다.
    connected_devices = []
    failed_devices = []

    print("장비 검색 중...")

    # 각 리소스를 순회하며 연결을 확인합니다.
    for device_address in dev_list:
        try:
            # 지정된 주소의 장비에 연결을 시도합니다.
            # timeout을 짧게 설정하여 응답 없는 장비에서 오래 기다리지 않도록 합니다.
            instrument = rm.open_resource(device_address,
                                         timeout=1000,
                                         access_mode=pyvisa.constants.AccessModes.no_lock)

            # *IDN? (identification) 쿼리를 보냅니다.
            # 대부분의 계측 장비는 이 명령에 모델명, 제조사 등의 정보로 응답합니다.
            identity = instrument.query('*IDN?')

            # 응답이 성공적으로 오면, 연결된 장비로 간주합니다.
            print(f"✅ 연결 성공: {device_address} - 응답: {identity.strip()}")
            connected_devices.append(device_address)

            # 사용 후에는 반드시 연결을 닫아줍니다.
            instrument.close()

        except pyvisa.errors.VisaIOError as e:
            # I/O 에러인 경우 리셋 시도
            error_code = e.error_code if hasattr(e, 'error_code') else None
            print(f"❌ 연결 실패: {device_address} - 오류: {e}")

            # VI_ERROR_IO (-1073807298) 에러인 경우
            if error_code == -1073807298 or "VI_ERROR_IO" in str(e):
                print(f"⚠️ I/O Error detected. Attempting device reset...")
                failed_devices.append(device_address)

                # 장치 리셋 시도
                if reset_usb_device(device_address):
                    print(f"✅ Device reset successful, retrying connection...")
                    time.sleep(0.5)

                    # 재시도
                    try:
                        instrument = rm.open_resource(device_address,
                                                     timeout=1000,
                                                     access_mode=pyvisa.constants.AccessModes.no_lock)
                        identity = instrument.query('*IDN?')
                        print(f"✅ 재연결 성공: {device_address} - 응답: {identity.strip()}")
                        connected_devices.append(device_address)
                        failed_devices.remove(device_address)
                        instrument.close()
                    except Exception as retry_ex:
                        print(f"❌ 재연결 실패: {device_address} - {retry_ex}")

        except Exception as ex:
            print(f"❌ Unexpected error for {device_address}: {ex}")
            failed_devices.append(device_address)

    print(f"총 {len(connected_devices)}개의 장비가 연결되어 있습니다.")

    if len(failed_devices) > 0:
        print(f"⚠️ {len(failed_devices)}개의 장비 연결 실패:")
        for dev in failed_devices:
            print(f"  - {dev}")

    return connected_devices


if __name__ == "__main__":
    import argparse
    try:
        parser = argparse.ArgumentParser(description='AG344xxx_read_avg')

        parser.add_argument('--device', '-d', required=False, type=str, help='Set Device ID')
        # parser.add_argument('--device', '-d', default = "9604",required=False, type=str, help='Set Device ID')
        parser.add_argument('--range', '-r', required=False, type=str, help='Range (DCI_3A, DCI_1A, DCI_100mA, DCI_10mA, DCV_100V, DCV_10V, DCV_1V')
        # parser.add_argument('--range', '-r', default='DCI_100mA',required=False, type=str, help='Range (DCI_3A, DCI_1A, DCI_100mA, DCI_10mA, DCV_100V, DCV_10V, DCV_1V')
        # parser.add_argument('--range', '-r', default='DCV_10V',required=False, type=str, help='Range (DCI_3A, DCI_1A, DCI_100mA, DCI_10mA, DCV_100V, DCV_10V, DCV_1V')
        parser.add_argument('--count', '-c', default= 4000,required=False, type=int, help='Count default 4000')
        # parser.add_argument('--count', '-c', default= 4000,required=False, type=int, help='Count default 4000')
        parser.add_argument('--Getlist', '-l', required=False, action='store_true', help='Get device list')

        args = parser.parse_args()

        # get device list
        # dev_list = rm.list_resources()
        dev_list = get_equipment()
        if args.Getlist:
            for device in dev_list:
                print(device)
            sys.exit()

        # Check argv
        if (args.device == None) or (args.range == None) or (args.count == None):
            print("Error !")
            sys.exit()

        # Check Device
        device_resource = None
        for device in dev_list:
            if args.device in device:
                device_resource = device
                break
        if device_resource == None:
            print("Device not found!")
            sys.exit()

        # device connect
        try:
            myPna = rm.open_resource(device_resource)      # 1층 PBA 1
        except:
            print("Device not connected!")
            sys.exit()

        device_range = None
        if "DCI_3A" in args.range :
            device_range = Range_state_t.DCI_3A
        elif "DCI_1A" in args.range :
            device_range = Range_state_t.DCI_1A
        elif "DCI_100mA" in args.range :
            device_range = Range_state_t.DCI_100mA
        elif "DCI_10mA" in args.range :
            device_range = Range_state_t.DCI_10mA
        elif "DCV_100V" in args.range :
            device_range = Range_state_t.DCV_100V
        elif "DCV_10V" in args.range :
            device_range = Range_state_t.DCV_10V
        elif "DCV_1V" in args.range :
            device_range = Range_state_t.DCV_1V
        else:
            print("Error! Check range")
            sys.exit(1)

        CMD_Reset(myPna)
        myPna.write("*IDN?")
        print(myPna.read())

        result = avg_test(myPna,device_range,args.count)
        # count_list.append(result[0])
        # avg_list.append(result[1])
        # min_list.append(result[2])
        # max_list.append(result[3])

        res_count = result[0]
        res_avg = result[1]
        res_min = result[2]
        res_max = result[3]

        if device_range.value<= Range_state_t.DCI_10mA.value:
            # print("Avg min : %sA, Avg Max : %sA, Avg avg : %sA"%(prinr(min(avg_list)),prinr(max(avg_list)),prinr(sum(avg_list)/test_count)))
            print("Current min : %sA, max : %sA, avg : %sA"%(prinr(res_min),prinr(res_max),prinr(res_avg)))
        else:
            print("Voltage min : %sV, max : %sV, avg : %sV"%(prinr(res_min),prinr(res_max),prinr(res_avg)))
        
    except  Exception as ex:
        print(ex)
        # myPna.close()
        # rm.close()

    try:
        myPna.close()
    except:
        pass
    try:
        rm.close()
    except:
        pass