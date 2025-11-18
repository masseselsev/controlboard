# ТУТ ХРАНЯТСЯ ВСЕ КОМАНДЫ
import binascii
from typing import TypedDict
from enum import IntEnum, StrEnum

class TYPE(StrEnum):
    READ        = "read"
    WRITE       = "write"
    CONTROL     = "control"
    TEST        = "test"
    UPDATE      = "update"
    UTIL        = "util"

class ModbusDict(TypedDict):
    address     : int
    function    : int
    register    : int
    value       : int

DEVICE_ADDR = 0x30      # [dec: 48] address of device
DEVICE_ADDR_STR = "30"  # текстовое представление

class FUNC(IntEnum):
    MB_FC1_READ_COILS            = 0x01  # ! FCT=1 -> read coils or digital outputs
    MB_FC2_READ_DISCRETE_INPUT   = 0x02  # ! FCT=2 -> read digital inputs
    MB_FC3_READ_REGISTERS        = 0x03  # ! FCT=3 -> read registers or analog outputs
    MB_FC4_READ_INPUT_REGISTER   = 0x04  # ! FCT=4 -> read analog inputs
    MB_FC5_WRITE_COIL            = 0x05  # ! FCT=5 -> write single coil or output
    MB_FC6_WRITE_REGISTER        = 0x06  # ! FCT=6 -> write single register

CMD_ON      = 0xFF00
CMD_OFF     = 0x0000
OFFSET      = 0x2000    # add an offset to avoid intersection of commands
                    # of the combined software version

class REG(IntEnum):
    ZERO_BIT_14 = 0x000E    # [14 bit]  ------[from Atmega128VIT_v1.4]
    ZERO_BIT_15 = 0x000F    # [15 bit]  ------[from Atmega128VIT_v1.4]

    # Registers KCPA func 6
    REG_RADAR_PWR   = (OFFSET + 0x1000)
    REG_CAMERA_PWR  = (OFFSET + 0x1001)
    REG_GPS_PWR     = (OFFSET + 0x1002)
    REG_HEATER_1    = (OFFSET + 0x1003)
    REG_HEATER_2    = (OFFSET + 0x1004)

    REG_LED1        = (OFFSET + 0x0001)
    REG_LED2        = (OFFSET + 0x0002)
    REG_FOCUS       = (OFFSET + 0x0012)
    REG_ZOOM        = (OFFSET + 0x0021)
    REG_DIAPH       = (OFFSET + 0x0011)
    REG_IRF         = (OFFSET + 0x0022)

    # bit addresses of function 0x02
    AC_OK           = 0x0000    # [0 bit]
    BATT_LOW        = 0x0001    # [1 bit]
    PWR_LED         = 0x0002    # [2 bit]
    FAN_BLOCKED     = 0x0004    # [4 bit]
    FROZEN_MODE     = 0x0005    # [5 bit]

    # Registers VSM
    REG_VSM_PC_PWR      = 0x0000
    REG_VSM_HEAT_1      = 0x0001
    REG_VSM_HEAT_2      = 0x0002
    REG_VSM_PC_SW       = 0x0005
    REG_LEDS_ON         = 0x0006    # new register for shutdown all LEDs
    REG_VSM_FROZEN_REQ  = 0x0007

    REG_GETRESET_WATCHDOG   = 0x0000    # dec:0 -
    REG_GET_FLAGS           = 0x0001    # dec:1 -
    REG_GET_POWERFLAGS      = 0x0002    # dec:2 -
    REG_GET_VOLTAGE         = 0x0003    # dec:3 -
    REG_GET_TEMPERATURE     = 0x0004    # dec:4 -
    REG_GET_CURRENT         = 0x0005    # dec:5 -
    REG_GET_FANSPEED        = 0x0006    # dec:6 -
    REG_SET_TXCOUNT         = 0x0007    # dec:7 -
    REG_UPDATE_FIRMWARE     = 0x0013    # dec:19 -
    REG_START_LO_TEMP       = 0x0014    # dec:20 -
    REG_START_HI_TEMP       = 0x0015    # dec:21 -
    REG_WORK_LO_TEMP        = 0x0016    # dec:22 -
    REG_WORK_HI_TEMP        = 0x0017    # dec:23 -
    REG_PREHEATING_TEMP     = 0x0018    # dec:24 -
    REG_INCHEAT_HYST        = 0x0019    # dec:25 -
    REG_MAX_VOLT            = 0x001A    # dec:26 -
    REG_MIN_VOLT            = 0x001B    # dec:27 -
    REG_FLASHLOG_POS        = 0x001C    # dec:28 -
    REG_FLASHLOG_ENTRY0     = 0x001D    # dec:29 -
    REG_FLASHLOG_ENTRY1     = 0x001E    # dec:30 -
    REG_FLASHLOG_ENTRY2     = 0x001F    # dec:31 -
    REG_FLASHLOG_ENTRY3     = 0x0020    # dec:32 -
    REG_FLASHLOG_ENTRY4     = 0x0021    # dec:33 -
    REG_FLASHLOG_ENTRY5     = 0x0022    # dec:34 -
    REG_FLASHLOG_ENTRY6     = 0x0023    # dec:35 -
    REG_MIN_CURRENT         = 0x0024    # dec:36 -
    REG_MAX_CURRENT         = 0x0025    # dec:37 -
    REG_VERSION             = 0x0026    # dec:38 -
    REG_CONFIG_RESET        = 0x0027    # dec:39 -
    REG_INCHEAT_X1_TEMP     = 0x0028    # dec:40 -
    REG_INCHEAT_X2_TEMP     = 0x0029    # dec:41 -
    REG_WITH_FAN            = 0x002A    # dec:42 -
    REG_REBOOT              = 0x002B    # dec:43 -
    REG_SERIAL0             = 0x002C    # dec:44 -
    REG_SERIAL1             = 0x002D    # dec:45 -
    REG_SERIAL2             = 0x002E    # dec:46 -
    REG_SERIAL3             = 0x002F    # dec:47 -
    REG_SERIAL4             = 0x0030    # dec:48 -
    REG_SERIAL5             = 0x0031    # dec:49 -
    REG_UPSCONF             = 0x0032    # dec:50 -
    REG_BATLOW              = 0x0033    # dec:51 -
    REG_FANPWR              = 0x0034    # dec:52 -
    REG_FRAME_DUR_MULT      = 0x0035    # dec:53 -
    REG_FRAME_FLAGS         = 0x0036    # dec:54 -
    REG_FRAME_STEP          = 0x0037    # dec:55 -
    REG_FRAME_WORK          = 0x0038    # dec:56 -
    REG_AUTO_HEAT_MODE      = 0x0039    # dec:57 - set and get auto heat mode

    # my parameters for reading
    REG_GET_TIME_LO         = 0x0050    # dec:80 - global timer from default task, low bytes
    REG_GET_TIME_HI         = 0x0051    # dec:81 - global timer from default task, high bytes
    REG_GET_ROLLO_TIME      = 0x0052    # dec:82 - 
    REG_GET_ACCUM_W_LO      = 0x0053    # dec:83 - 
    REG_GET_ACCUM_W_HI      = 0x0054    # dec:84 - 
    REG_GET_AVG_P_LO        = 0x0055    # dec:85 - 
    REG_GET_AVG_P_HI        = 0x0056    # dec:86 - 
    REG_GET_HUM             = 0x0057    # dec:87 - 
    REG_GET_PRESSURE_LO     = 0x0058    # dec:88 - 
    REG_GET_PRESSURE_HI     = 0x0059    # dec:88 - 
    REG_RTC_YEAR_MONTH      = 0x005A	# dec:90 - 
    REG_RTC_DATE_HOUR       = 0x005B	# dec:91 - 
    REG_RTC_MIN_SEC         = 0x005C	# dec:92 - 

    # IMU (Inertial Measurement Unit) registers
    REG_IMU                 = 0x0060            # dec:96
    REG_GET_IMU_STATUS      = (REG_IMU + 0x00)  # dec:96 - status
    REG_GET_GRAVITY         = (REG_IMU + 0x01)  # dec:97 - gravitational acceleration (an integer is not a float, as 9807 - 9.807 [m/s2])
    REG_GET_ACCEL_SCALE     = (REG_IMU + 0x02)  # dec:98 - accel scale
    REG_GET_GYRO_SCALE      = (REG_IMU + 0x03)  # dec:99 - gyro scale
    REG_GET_ACCEL_X         = (REG_IMU + 0x04)  # dec:100 - accel x
    REG_GET_ACCEL_Y         = (REG_IMU + 0x05)  # dec:101 - accel y
    REG_GET_ACCEL_Z         = (REG_IMU + 0x06)  # dec:102 - accel z
    REG_GET_GYRO_X          = (REG_IMU + 0x07)  # dec:103 - gyro x
    REG_GET_GYRO_Y          = (REG_IMU + 0x08)  # dec:104 - gyro y
    REG_GET_GYRO_Z          = (REG_IMU + 0x09)  # dec:105 - gyro z
    REG_GET_PITCH           = (REG_IMU + 0x0A)  # dec:106 - sides rotation
    REG_GET_ROLL            = (REG_IMU + 0x0B)  # dec:107 - forward-back rotation

    # here tech data registers
    REG_TECH_DATA           = 0xDA00
    REG_TECH_DATA_0         = (REG_TECH_DATA + 0x00)    # flag active firmware and glob version of the bootloader
    REG_TECH_DATA_1         = (REG_TECH_DATA + 0x01)    # sub version and revision of the bootloader
    REG_TECH_DATA_2         = (REG_TECH_DATA + 0x02)    # data of the bootloader uploading (dd.mm)
    REG_TECH_DATA_3         = (REG_TECH_DATA + 0x03)    # data of the bootloader uploading (yy) and glob version of the factory firmware
    REG_TECH_DATA_4         = (REG_TECH_DATA + 0x04)    # sub version and revision of the factory firmware
    REG_TECH_DATA_5         = (REG_TECH_DATA + 0x05)    # data of the factory firmware uploading (dd.mm)
    REG_TECH_DATA_6         = (REG_TECH_DATA + 0x06)    # data of the factory firmware uploading (yy) and glob version of the update firmware
    REG_TECH_DATA_7         = (REG_TECH_DATA + 0x07)    # sub version and revision of the update firmware
    REG_TECH_DATA_8         = (REG_TECH_DATA + 0x08)    # data of the update firmware uploading (dd.mm)
    REG_TECH_DATA_9         = (REG_TECH_DATA + 0x09)    # data of the update firmware uploading (yy) + 0xFF
    REG_TECH_DATA_10        = (REG_TECH_DATA + 0x0A)    # registers count of the firmware project name
    REG_TD_PRJ_NM_START     = (REG_TECH_DATA_10 + 0x01) # firmware project name starts

class Default_Value(IntEnum):
    # DEFAULT parametres in firmware
    DEF_START_LO_TEMP       = 0         # [°C]
    DEF_START_HI_TEMP       = 70        # [°C]
    DEF_WORK_LO_TEMP        = -5        # [°C]
    DEF_WORK_HI_TEMP        = 85        # [°C]
    DEF_PREHEATING_TEMP     = 10        # [°C] - in our version is absent
    DEF_TEMP_HYST           = 2         # [°C] temperature hysteresis for heaters processes
    DEF_MAX_VOLT            = 15000     # [mV] high limit of voltage
    DEF_MIN_VOLT            = 10500     # [mV] low limit of voltage
    DEF_MIN_CURRENT         = 50        # [mA] low limit of current
    DEF_MAX_CURRENT         = 20000     # [mA] high limit of current
    DEF_WORK_TEMP_HEAT1     = 5         # [°C] work line of temperature for heater_1 processes
    DEF_WORK_TEMP_HEAT2     = 5         # [°C] work line of temperature for heater_2 processes
    DEF_FAN_CONF            = 0         # without FAN - in our version is absent
    DEF_UPS_CONF            = 1         # Everything is always OK in older version
    DEF_BAT_LO_VOLT         = 9000      # [mV]

cmd_control_array = {
    ### CONTROL ### type 'control' - команды, которые отправляются как есть, без каких-то изменений в value
    # LED1
    "led1_on": {
        "type"          : TYPE.CONTROL,
        "description"   : "Включение светодиода LED1 (БЦО: H14 - SE_V1, H2 - SE_V2)",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_LED1,
            "value"     : 0x0000
        }
    },
    "led1_1hz": {
        "type"          : TYPE.CONTROL,
        "description"   : "Мигание светодиодом LED1 с частотой 1 Гц (БЦО: H14 - SE_V1, H2 - SE_V2)",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_LED1,
            "value"     : 0x0001
        }
    },
    "led1_2hz": {
        "type"          : TYPE.CONTROL,
        "description"   : "Мигание светодиодом LED1 с частотой 2 Гц (БЦО: H14 - SE_V1, H2 - SE_V2)",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_LED1,
            "value"     : 0x0002
        }
    },
    "led1_off": {
        "type"          : TYPE.CONTROL,
        "description"   : "ВЫКЛючение светодиода LED1 (БЦО: H14 - SE_V1, H2 - SE_V2)",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_LED1,
            "value"     : 0x0003
        }
    },
    "led1_1s": {
        "type"          : TYPE.CONTROL,
        "description"   : "Мигание светодиодом LED1 1 секунду (БЦО: H14 - SE_V1, H2 - SE_V2)",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_LED1,
            "value"     : 0x0004
        }
    },
    "led1_2s": {
        "type"          : TYPE.CONTROL,
        "description"   : "Мигание светодиодом LED1 2 секунды (БЦО: H14 - SE_V1, H2 - SE_V2)",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_LED1,
            "value"     : 0x0005
        }
    },

    # LED2
    "led2_on": {
        "type"          : TYPE.CONTROL,
        "description"   : "Включение светодиода LED2 (БЦО: H15 - SE_V1, H3 - SE_V2)",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_LED2,
            "value"     : 0x0000
        }
    },
    "led2_1hz": {
        "type"          : TYPE.CONTROL,
        "description"   : "Мигание светодиодом LED2 с частотой 1 Гц (БЦО: H15 - SE_V1, H3 - SE_V2)",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_LED2,
            "value"     : 0x0001
        }
    },
    "led2_2hz": {
        "type"          : TYPE.CONTROL,
        "description"   : "Мигание светодиодом LED2 с частотой 2 Гц (БЦО: H15 - SE_V1, H3 - SE_V2)",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_LED2,
            "value"     : 0x0002
        }
    },
    "led2_off": {
        "type"          : TYPE.CONTROL,
        "description"   : "ВЫКЛючение светодиода LED2 (БЦО: H15 - SE_V1, H3 - SE_V2)",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_LED2,
            "value"     : 0x0003
        }
    },
    "led2_1s": {
        "type"          : TYPE.CONTROL,
        "description"   : "Мигание светодиодом LED2 1 секунду (БЦО: H15 - SE_V1, H3 - SE_V2)",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_LED2,
            "value"     : 0x0004
        }
    },
    "led2_2s": {
        "type"          : TYPE.CONTROL,
        "description"   : "Мигание светодиодом LED2 2 секунды (БЦО: H15 - SE_V1, H3 - SE_V2)",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_LED2,
            "value"     : 0x0005
        }
    },

    "leds_on": {
        "type"          : TYPE.CONTROL,
        "description"   : "ВКЛючение индикации.",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC5_WRITE_COIL,
            "register"  : REG.REG_LEDS_ON,
            "value"     : CMD_ON
        }
    },
    "leds_off": {
        "type"          : TYPE.CONTROL,
        "description"   : "ВЫКЛючение индикации.",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC5_WRITE_COIL,
            "register"  : REG.REG_LEDS_ON,
            "value"     : CMD_OFF
        }
    },

    # RADAR
    "radar_on": {
        "type"          : TYPE.CONTROL,
        "description"   : "вкл РАДАР",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_RADAR_PWR,
            "value"     : CMD_ON
        }
    },
    "radar_off": {
        "type"          : TYPE.CONTROL,
        "description"   : "выкл РАДАР",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_RADAR_PWR,
            "value"     : CMD_OFF
        }
    },
    "radar_on_2": {
        "type"          : TYPE.CONTROL,
        "description"   : "вкл РАДАР (альтернативная команда)",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC5_WRITE_COIL,
            "register"  : REG.REG_RADAR_PWR,
            "value"     : CMD_ON
        }
    },
    "radar_off_2": {
        "type"          : TYPE.CONTROL,
        "description"   : "выкл РАДАР (альтернативная команда)",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC5_WRITE_COIL,
            "register"  : REG.REG_RADAR_PWR,
            "value"     : CMD_OFF
        }
    },

    # CAMERA
    "cam_on": {
        "type"          : TYPE.CONTROL,
        "description"   : "вкл КАМЕРУ",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_CAMERA_PWR,
            "value"     : CMD_ON
        }
    },
    "cam_off": {
        "type"          : TYPE.CONTROL,
        "description"   : "выкл КАМЕРУ",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_CAMERA_PWR,
            "value"     : CMD_OFF
        }
    },
    "cam_on_2": {
        "type"          : TYPE.CONTROL,
        "description"   : "вкл КАМЕРУ (альтернативная команда)",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC5_WRITE_COIL,
            "register"  : REG.REG_CAMERA_PWR,
            "value"     : CMD_ON
        }
    },
    "cam_off_2": {
        "type"          : TYPE.CONTROL,
        "description"   : "выкл КАМЕРУ (альтернативная команда)",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC5_WRITE_COIL,
            "register"  : REG.REG_CAMERA_PWR,
            "value"     : CMD_OFF
        }
    },

    # GPS
    "gps_on": {
        "type"          : TYPE.CONTROL,
        "description"   : "вкл GPS",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_GPS_PWR,
            "value"     : CMD_ON
        }
    },
    "gps_off": {
        "type"          : TYPE.CONTROL,
        "description"   : "выкл GPS",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_GPS_PWR,
            "value"     : CMD_OFF
        }
    },
    "gps_on_2": {
        "type"          : TYPE.CONTROL,
        "description"   : "вкл GPS (альтернативная команда)",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC5_WRITE_COIL,
            "register"  : REG.REG_GPS_PWR,
            "value"     : CMD_ON
        }
    },
    "gps_off_2": {
        "type"          : TYPE.CONTROL,
        "description"   : "выкл GPS (альтернативная команда)",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC5_WRITE_COIL,
            "register"  : REG.REG_GPS_PWR,
            "value"     : CMD_OFF
        }
    },

    # PC
    "pc_on": {
        "type"          : TYPE.CONTROL,
        "description"   : "вкл ПК",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC5_WRITE_COIL,
            "register"  : REG.REG_VSM_PC_PWR,
            "value"     : CMD_ON
        }
    },
    "pc_off": {
        "type"          : TYPE.CONTROL,
        "description"   : "выкл ПК",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC5_WRITE_COIL,
            "register"  : REG.REG_VSM_PC_PWR,
            "value"     : CMD_OFF
        }
    },
    "pc_wdt_reset": {
        "type"          : TYPE.CONTROL,
        "description"   : "Сброс таймера Watchdog ПК",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_GETRESET_WATCHDOG,
            "value"     : 0x0000
        }
    },

    "reset": {
        "type"          : TYPE.CONTROL,
        "description"   : "команда сброса МК, обычно для перехода в режим обновления ПО",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_UPDATE_FIRMWARE,
            "value"     : 0x021F
        }
    },

    "params_save": {
        "type"          : TYPE.CONTROL,
        "description"   : "Сохранение конфигурационных параметров во Flash",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_WITH_FAN,
            "value"     : 0x0000
        }
    },

    "params_reset": {
        "type"          : TYPE.CONTROL,
        "description"   : "Сброс конфигурационных параметров и запись во Flash",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_CONFIG_RESET,
            "value"     : 0x0000
        }
    },

    "freez": {
        "type"          : TYPE.CONTROL,
        "description"   : "Включение freez mode (остановка WDT ПК)",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC5_WRITE_COIL,
            "register"  : REG.REG_VSM_FROZEN_REQ,
            "value"     : CMD_ON
        }
    },

    "unfreez": {
        "type"          : TYPE.CONTROL,
        "description"   : "Выключение freez mode (возобновление работы WDT ПК)",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC5_WRITE_COIL,
            "register"  : REG.REG_VSM_FROZEN_REQ,
            "value"     : CMD_OFF
        }
    },

    # HEATER 1 - есть дополнительные возможности, работа в ШИМ режиме, при изменении value (см. cmd_write_array и func_write)
    "heat1_on": {
        "type"          : TYPE.CONTROL,
        "description"   : "вкл НАГРЕВАТЕЛЬ 1 (X14 - SE_V1 или 3-4 пины X2 - SE_V2)",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC5_WRITE_COIL,
            "register"  : REG.REG_HEATER_1,
            "value"     : CMD_ON
        }
    },
    "heat1_off": {
        "type"          : TYPE.CONTROL,
        "description"   : "выкл НАГРЕВАТЕЛЬ 1 (X14 - SE_V1 или 3-4 пины X2 - SE_V2)",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC5_WRITE_COIL,
            "register"  : REG.REG_HEATER_1,
            "value"     : CMD_OFF
        }
    },

    # HEATER 2 - есть дополнительные возможности, работа в ШИМ режиме, при изменении value (см. cmd_write_array и func_write)
    "heat2_on": {
        "type"          : TYPE.CONTROL,
        "description"   : "вкл НАГРЕВАТЕЛЬ 2 (X19 - SE_V1 или 1-2 пины X2 - SE_V2)",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC5_WRITE_COIL,
            "register"  : REG.REG_HEATER_2,
            "value"     : CMD_ON
        }
    },
    "heat2_off": {
        "type"          : TYPE.CONTROL,
        "description"   : "выкл НАГРЕВАТЕЛЬ 2 (X19 - SE_V1 или 1-2 пины X2 - SE_V2)",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC5_WRITE_COIL,
            "register"  : REG.REG_HEATER_2,
            "value"     : CMD_OFF
        }
    },
    ###############
}

cmd_read_array = {
    ### READ ###
    "version_request": {
        "type"          : TYPE.READ,
        "description"   : "запрос версии, в ответ [addr byte] 04 02 20 00 [2 байта crc16] - было 14",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0xFFFF,
            "value"     : 0x0001
        }
    },

    "temp": {
        "type"          : TYPE.READ,
        "description"   : 'Чтение датчика температуры напрямую',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x9100,
            "value"     : 0x0000
        }
    },

    # Запрос цепей питания. Регистр и значение сделаны с ошибкой умышленно,
    # т.к. мы будем в данной программе получать сразу все значения, что требует
    # отправления нескольких команд.
    "coils": {
        "type"          : TYPE.READ,
        "description"   : 'Чтение цепей питания',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC1_READ_COILS,
            "register"  : 0xFFFF,
            "value"     : 0x0000
        }
    },

    # Запрос флагов. Регистр и значение сделаны с ошибкой умышленно,
    # т.к. мы будем в данной программе получать сразу все значения, что требует
    # отправления нескольких команд.
    "states": {
        "type"          : TYPE.READ,
        "description"   : 'Чтение состояний флагов',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC2_READ_DISCRETE_INPUT,
            "register"  : 0xFFFF,
            "value"     : 0x0000
        }
    },

    "pc_wdt": {
        "type"          : TYPE.READ,
        "description"   : 'Чтение Watchdog таймера ПК',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC3_READ_REGISTERS,
            "register"  : REG.REG_GETRESET_WATCHDOG,
            "value"     : 0x0001
        }
    },

    "voltage": {
        "type"          : TYPE.READ,
        "description"   : 'Чтение напряжения на входе, зафиксированное при последнем обновлении данных с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC3_READ_REGISTERS,
            "register"  : REG.REG_GET_VOLTAGE,
            "value"     : 0x0001
        }
    },

    "temperature": {
        "type"          : TYPE.READ,
        "description"   : 'Чтение температуры, зафиксированной при последнем обновлении данных с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC3_READ_REGISTERS,
            "register"  : REG.REG_GET_TEMPERATURE,
            "value"     : 0x0001
        }
    },

    "current": {
        "type"          : TYPE.READ,
        "description"   : 'Чтение тока на входе, зафиксированного при последнем обновлении данных с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC3_READ_REGISTERS,
            "register"  : REG.REG_GET_CURRENT,
            "value"     : 0x0001
        }
    },

    "start_temp": {
        "type"          : TYPE.READ,
        "description"   : f'Чтение лимитов стартовой температуры (конфигурацинные параметры работы прибора, пока номинальные параметры: {Default_Value.DEF_START_LO_TEMP}...{Default_Value.DEF_START_HI_TEMP} [॰С])',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC3_READ_REGISTERS,
            "register"  : REG.REG_START_LO_TEMP,
            "value"     : 0x0002
        }
    },

    "work_temp": {
        "type"          : TYPE.READ,
        "description"   : f'Чтение лимитов рабочей температуры (конфигурацинные параметры работы прибора, по дефолту обычно: {Default_Value.DEF_WORK_LO_TEMP}...{Default_Value.DEF_WORK_HI_TEMP} [॰С])',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC3_READ_REGISTERS,
            "register"  : REG.REG_WORK_LO_TEMP,
            "value"     : 0x0002
        }
    },

    "pre_temp": {
        "type"          : TYPE.READ,
        "description"   : f'Чтение параметра температуры преднагрева (конфигурационный параметр работы прибора, пока номинальный параметр: {Default_Value.DEF_PREHEATING_TEMP} [॰С])',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC3_READ_REGISTERS,
            "register"  : REG.REG_PREHEATING_TEMP,
            "value"     : 0x0001
        }
    },

    "hyst": {
        "type"          : TYPE.READ,
        "description"   : f'Чтение гистререзиса переключения нагревателей (конфигурационный параметр работы прибора, обычно по дефолту: {Default_Value.DEF_TEMP_HYST} [॰С])',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC3_READ_REGISTERS,
            "register"  : REG.REG_INCHEAT_HYST,
            "value"     : 0x0001
        }
    },

    "voltage_limits": {
        "type"          : TYPE.READ,
        "description"   : f'Чтение диапазона нормальной работы по напряжению (конфигурационные параметры работы прибора, обычно по дефолту: {Default_Value.DEF_MIN_VOLT}...{Default_Value.DEF_MAX_CURRENT} [mA])',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC3_READ_REGISTERS,
            "register"  : REG.REG_MAX_VOLT,
            "value"     : 0x0002
        }
    },

    "current_limits": {
        "type"          : TYPE.READ,
        "description"   : f'Чтение диапазона нормальной рабты прибора по току (конфигурационные параметры работы прибора, обычно по дефолту: {Default_Value.DEF_MIN_CURRENT}...{Default_Value.DEF_MAX_CURRENT} [mA])',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC3_READ_REGISTERS,
            "register"  : REG.REG_MIN_CURRENT,
            "value"     : 0x0002
        }
    },

    "firmware_version": {
        "type"          : TYPE.READ,
        "description"   : 'Чтение версии прошивки, установленной при первом старте прибора (читается из Flash-памяти)',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC3_READ_REGISTERS,
            "register"  : REG.REG_VERSION,
            "value"     : 0x0001
        }
    },

    "heat_temp": {
        "type"          : TYPE.READ,
        "description"   : f'Чтение установленных границ срабатывания нагревателей (конфигурационные параметры работы прибора, обычно по дефолту:\nдля нагревателя 1 - {Default_Value.DEF_WORK_TEMP_HEAT1} [॰С], для нагревателя 2 - {Default_Value.DEF_WORK_TEMP_HEAT2} [॰С])',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC3_READ_REGISTERS,
            "register"  : REG.REG_INCHEAT_X1_TEMP,
            "value"     : 0x0002
        }
    },

    "serial_number": {
        "type"          : TYPE.READ,
        "description"   : 'Чтение серийного номера микроконтроллера STM32',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC3_READ_REGISTERS,
            "register"  : REG.REG_SERIAL0,
            "value"     : 0x0006
        }
    },

    "with_fan": {
        "type"          : TYPE.READ,
        "description"   : f'Чтение параметра работы FAN (конфигурационный параметр работы прибора, пока номинальный параметр: {Default_Value.DEF_FAN_CONF})',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC3_READ_REGISTERS,
            "register"  : REG.REG_WITH_FAN,
            "value"     : 0x0001
        }
    },

    "ups_conf": {
        "type"          : TYPE.READ,
        "description"   : f'Чтение параметра работы UPS (конфигурационный параметр работы прибора, пока номинальный параметр: {Default_Value.DEF_UPS_CONF})',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC3_READ_REGISTERS,
            "register"  : REG.REG_UPSCONF,
            "value"     : 0x0001
        }
    },

    "bat_low_limit": {
        "type"          : TYPE.READ,
        "description"   : f'Чтение установленного порога низкого заряда батареи (конфигурацинный параметр работы прибора, обычно по дефолту: {Default_Value.DEF_BAT_LO_VOLT} [mV])',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC3_READ_REGISTERS,
            "register"  : REG.REG_BATLOW,
            "value"     : 0x0001
        }
    },

    "timer": {
        "type"          : TYPE.READ,
        "description"   : 'Чтение счетчика времени работы платы (время не совсем точное)',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC3_READ_REGISTERS,
            "register"  : REG.REG_GET_TIME_LO,
            "value"     : 0x0003
        }
    },

    "accum": {
        "type"          : TYPE.READ,
        "description"   : 'Чтение саккумурированных значений потребления (в данную функцию включена фунция "timer")',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC3_READ_REGISTERS,
            "register"  : REG.REG_GET_ACCUM_W_LO,
            "value"     : 0x0004
        }
    },

    "humidity": {
        "type"          : TYPE.READ,
        "description"   : 'Чтение значения влажности с датчика влажности',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC3_READ_REGISTERS,
            "register"  : REG.REG_GET_HUM,
            "value"     : 0x0001
        }
    },

    "pressure": {
        "type"          : TYPE.READ,
        "description"   : 'Чтение значения с датчика давления',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC3_READ_REGISTERS,
            "register"  : REG.REG_GET_PRESSURE_LO,
            "value"     : 0x0002
        }
    },

    "in_v": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос входного напряжения прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x8188,
            "value"     : 0x0000
        }
    },

    "in_v_high_lim": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос лимита перенапряжения входного питания прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x8157,
            "value"     : 0x0000
        }
    },

    "in_v_low_lim": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос лимита пониженного напряжения входного питания прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x8158,
            "value"     : 0x0000
        }
    },

    "in_meter": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос данных счетчика в кВт входного питания прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x8186,
            "value"     : 0x0000
        }
    },

    "in_v_shunt": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос падения напряжения на входном шунте прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x81D1,
            "value"     : 0x0000
        }
    },

    "in_i": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос входного тока прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x8189,
            "value"     : 0x0000
        }
    },

    "in_i_lim": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос лимита установленного по току прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x814A,
            "value"     : 0x0000
        }
    },

    "in_p": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос входной мощности прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x8197,
            "value"     : 0x0000
        }
    },

    "in_p_lim": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос лимита установленного по мощности прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x816B,
            "value"     : 0x0000
        }
    },

    "pc_v": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос напряжения ПК прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x8388,
            "value"     : 0x0000
        }
    },

    "pc_v_high_lim": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос лимита перенапряжения питания ПК прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x8357,
            "value"     : 0x0000
        }
    },

    "pc_v_low_lim": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос лимита пониженного напряжения питания ПК прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x8358,
            "value"     : 0x0000
        }
    },

    "pc_meter": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос данных счетчика в кВт питания ПК прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x8386,
            "value"     : 0x0000
        }
    },

    "pc_v_shunt": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос падения напряжения на шунте ПК прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x83D1,
            "value"     : 0x0000
        }
    },

    "pc_i": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос тока ПК прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x8389,
            "value"     : 0x0000
        }
    },

    "pc_i_lim": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос лимита установленного по току для ПК прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x834A,
            "value"     : 0x0000
        }
    },

    "pc_p": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос мощности потребляемой ПК прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x8397,
            "value"     : 0x0000
        }
    },

    "pc_p_lim": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос лимита установленного по мощности для ПК прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x836B,
            "value"     : 0x0000
        }
    },

    "ra_v": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос напряжения радара прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x8788,
            "value"     : 0x0000
        }
    },

    "ra_v_high_lim": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос лимита перенапряжения питания радара прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x8757,
            "value"     : 0x0000
        }
    },

    "ra_v_low_lim": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос лимита пониженного напряжения питания радара прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x8758,
            "value"     : 0x0000
        }
    },

    "ra_meter": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос данных счетчика в кВт питания радара прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x8786,
            "value"     : 0x0000
        }
    },

    "ra_v_shunt": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос падения напряжения на шунте радара прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x87D1,
            "value"     : 0x0000
        }
    },

    "ra_i": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос тока радара прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x8789,
            "value"     : 0x0000
        }
    },

    "ra_i_lim": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос лимита установленного по току радара прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x874A,
            "value"     : 0x0000
        }
    },

    "ra_p": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос мощности потребляемой радаром прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x8797,
            "value"     : 0x0000
        }
    },

    "ra_p_lim": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос лимита установленного по мощности радара прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x876B,
            "value"     : 0x0000
        }
    },

    "sl_v": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос напряжения питания прожектора прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x8B88,
            "value"     : 0x0000
        }
    },

    "sl_v_high_lim": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос лимита перенапряжения питания прожектора прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x8B57,
            "value"     : 0x0000
        }
    },

    "sl_v_low_lim": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос лимита пониженного напряжения питания прожектора прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x8B58,
            "value"     : 0x0000
        }
    },

    "sl_meter": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос данных счетчика в кВт питания прожектора прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x8B86,
            "value"     : 0x0000
        }
    },

    "sl_v_shunt": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос падения напряжения на шунте прожектора прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x8BD1,
            "value"     : 0x0000
        }
    },

    "sl_i": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос тока прожектора прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x8B89,
            "value"     : 0x0000
        }
    },

    "sl_i_lim": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос лимита установленного по току для прожектора прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x8B4A,
            "value"     : 0x0000
        }
    },

    "sl_p": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос мощности потребляемой прожектора прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x8B97,
            "value"     : 0x0000
        }
    },

    "sl_p_lim": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос лимита установленного по мощности для прожектора прямо с датчика',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC4_READ_INPUT_REGISTER,
            "register"  : 0x8B6B,
            "value"     : 0x0000
        }
    },

    "tech_data": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос технической информации, записанной при прошивке',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC3_READ_REGISTERS,
            "register"  : REG.REG_TECH_DATA,
            "value"     : 0x000B    # 11
        }
    },

    "project_name": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос наименования проекта, в котором сделана прошивка',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC3_READ_REGISTERS,
            "register"  : REG.REG_TD_PRJ_NM_START,
            "value"     : 0x0000
        }
    },

    "imu": {
        "type"          : TYPE.READ,
        "description"   : 'Запрос данных чипа ICM-20948.',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC3_READ_REGISTERS,
            "register"  : REG.REG_IMU,
            "value"     : 0x000C
        }
    },

    "rtc": {
        "type"          : TYPE.READ,
        "description"   : 'Чтение даты и времени с RTC микроконтроллера.',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC3_READ_REGISTERS,
            "register"  : REG.REG_RTC_YEAR_MONTH,
            "value"     : 0x0003
        }
    },

    "frame_mult": {
        "type"          : TYPE.READ,
        "description"   : 'Чтение параметра умножения тактового сигнала для прожектора (и внутренний и внешний).',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC3_READ_REGISTERS,
            "register"  : REG.REG_FRAME_DUR_MULT,
            "value"     : 0x0001
        }
    },

    "frame_state": {
        "type"          : TYPE.READ,
        "description"   : 'Чтение состояния в процессе работы тактого сигнала пля прожектора.',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC3_READ_REGISTERS,
            "register"  : REG.REG_FRAME_DUR_MULT,
            "value"     : 0x0004
        }
    },

    "autoheat_mode": {
        "type"          : TYPE.READ,
        "description"   : 'Чтение режима автонагрева.',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC3_READ_REGISTERS,
            "register"  : REG.REG_AUTO_HEAT_MODE,
            "value"     : 0x0001
        }
    },

    # "imu_to_file": {
    #     "type"          : TYPE.READ,
    #     "description"   : 'Запрос всех данных чипа ICM-20948.',
    #     "modbus": {
    #         "address"   : DEVICE_ADDR,
    #         "function"  : FUNC.MB_FC3_READ_REGISTERS,
    #         "register"  : 0xD000,
    #         "value"     : 0x0000
    #     }
    # },
    # "imu_status": {
    #     "type"          : TYPE.READ,
    #     "description"   : 'Запрос состояния чипа ICM-20948.',
    #     "modbus": {
    #         "address"   : DEVICE_ADDR,
    #         "function"  : FUNC.MB_FC3_READ_REGISTERS,
    #         "register"  : 0xD000,
    #         "value"     : 0x0006
    #     }
    # },
    # "imu_data_1": {
    #     "type"          : TYPE.READ,
    #     "description"   : 'Запрос 5-ти записей буфера данных чипа ICM-20948. Часть 1 - 5 из 30.',
    #     "modbus": {
    #         "address"   : DEVICE_ADDR,
    #         "function"  : FUNC.MB_FC3_READ_REGISTERS,
    #         "register"  : 0xD006,
    #         "value"     : 0x002D
    #     }
    # },
    # "imu_data_2": {
    #     "type"          : TYPE.READ,
    #     "description"   : 'Запрос 5-ти записей буфера данных чипа ICM-20948. Часть 2 - 5 из 30.',
    #     "modbus": {
    #         "address"   : DEVICE_ADDR,
    #         "function"  : FUNC.MB_FC3_READ_REGISTERS,
    #         "register"  : 0xD033,
    #         "value"     : 0x002D
    #     }
    # },
    # "imu_data_3": {
    #     "type"          : TYPE.READ,
    #     "description"   : 'Запрос 5-ти записей буфера данных чипа ICM-20948. Часть 3 - 5 из 30.',
    #     "modbus": {
    #         "address"   : DEVICE_ADDR,
    #         "function"  : FUNC.MB_FC3_READ_REGISTERS,
    #         "register"  : 0xD060,
    #         "value"     : 0x002D
    #     }
    # },
    # "imu_data_4": {
    #     "type"          : TYPE.READ,
    #     "description"   : 'Запрос 5-ти записей буфера данных чипа ICM-20948. Часть 4 - 5 из 30.',
    #     "modbus": {
    #         "address"   : DEVICE_ADDR,
    #         "function"  : FUNC.MB_FC3_READ_REGISTERS,
    #         "register"  : 0xD08D,
    #         "value"     : 0x002D
    #     }
    # },
    # "imu_data_5": {
    #     "type"          : TYPE.READ,
    #     "description"   : 'Запрос 5-ти записей буфера данных чипа ICM-20948. Часть 5 - 5 из 30.',
    #     "modbus": {
    #         "address"   : DEVICE_ADDR,
    #         "function"  : FUNC.MB_FC3_READ_REGISTERS,
    #         "register"  : 0xD0BA,
    #         "value"     : 0x002D
    #     }
    # },
    # "imu_data_6": {
    #     "type"          : TYPE.READ,
    #     "description"   : 'Запрос 5-ти записей буфера данных чипа ICM-20948. Часть 6 - 5 из 30.',
    #     "modbus": {
    #         "address"   : DEVICE_ADDR,
    #         "function"  : FUNC.MB_FC3_READ_REGISTERS,
    #         "register"  : 0xD0E7,
    #         "value"     : 0x002D
    #     }
    # },
    ############
}

cmd_write_array = {
    ### WRITE ###
    # HEATER 1 - есть дополнительные возможности, работа в ШИМ режиме, при изменении value
    "heat1_on": {
        "type"          : TYPE.WRITE,
        "description"   : "вкл НАГРЕВАТЕЛЬ 1 (X14 - SE_V1 или 3-4 пины X2 - SE_V2)",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC5_WRITE_COIL,
            "register"  : REG.REG_HEATER_1,
            "value"     : CMD_ON
        }
    },
    "heat1_off": {
        "type"          : TYPE.WRITE,
        "description"   : "выкл НАГРЕВАТЕЛЬ 1 (X14 - SE_V1 или 3-4 пины X2 - SE_V2)",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC5_WRITE_COIL,
            "register"  : REG.REG_HEATER_1,
            "value"     : CMD_OFF
        }
    },

    # HEATER 2 - есть дополнительные возможности, работа в ШИМ режиме, при изменении value
    "heat2_on": {
        "type"          : TYPE.WRITE,
        "description"   : "вкл НАГРЕВАТЕЛЬ 2 (X19 - SE_V1 или 1-2 пины X2 - SE_V2)",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC5_WRITE_COIL,
            "register"  : REG.REG_HEATER_2,
            "value"     : CMD_ON
        }
    },
    "heat2_off": {
        "type"          : TYPE.WRITE,
        "description"   : "выкл НАГРЕВАТЕЛЬ 2 (X19 - SE_V1 или 1-2 пины X2 - SE_V2)",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC5_WRITE_COIL,
            "register"  : REG.REG_HEATER_2,
            "value"     : CMD_OFF
        }
    },

    # FOCUS - value условное, с данным значением не будет работать, значение зависит от установленных значений
    "focus": {
        "type"          : TYPE.WRITE,
        "description"   : "Управление мотором фокуса",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_FOCUS,
            "value"     : 0x0000
        }
    },
    # ZOOM - value условное, с данным значением не будет работать, значение зависит от установленных значений
    "zoom": {
        "type"          : TYPE.WRITE,
        "description"   : "Управление мотором зума",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_ZOOM,
            "value"     : 0x0000
        }
    },

    "diaph": {
        "type"          : TYPE.WRITE,
        "description"   : "Управление мотором диафрагмы",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_DIAPH,
            "value"     : 0x0000
        }
    },

    "start_low_temp": {
        "type"          : TYPE.WRITE,
        "title"         : "[WRITED] Low limit of start temperature (config)",
        "units"         : "॰С",
        "description"   : f"Записываем нижнюю границу стартовой температуры (default: {Default_Value.DEF_START_LO_TEMP})",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_START_LO_TEMP,
            "value"     : Default_Value.DEF_START_LO_TEMP
        }
    },

    "start_high_temp": {
        "type"          : TYPE.WRITE,
        "title"         : "[WRITED] High limit of start temperature (config)",
        "units"         : "॰С",
        "description"   : f"Записываем верхнюю границу стартовой температуры (default: {Default_Value.DEF_START_HI_TEMP})",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_START_HI_TEMP,
            "value"     : Default_Value.DEF_START_HI_TEMP
        }
    },

    "work_low_temp": {
        "type"          : TYPE.WRITE,
        "title"         : "[WRITED] Low limit of work temperature (config)",
        "units"         : "॰С",
        "description"   : f"Записываем нижнюю границу рабочей температуры (default: {Default_Value.DEF_WORK_LO_TEMP})",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_WORK_LO_TEMP,
            "value"     : Default_Value.DEF_WORK_LO_TEMP
        }
    },

    "work_high_temp": {
        "type"          : TYPE.WRITE,
        "title"         : "[WRITED] Low limit of work temperature (config)",
        "units"         : "॰С",
        "description"   : f"Записываем верхнюю границу рабочей температуры (default: {Default_Value.DEF_WORK_HI_TEMP})",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_WORK_HI_TEMP,
            "value"     : Default_Value.DEF_WORK_HI_TEMP
        }
    },

    "hyst": {
        "type"          : TYPE.WRITE,
        "title"         : "[WRITED] Hysteresis (config)",
        "units"         : "॰С",
        "description"   : f"Записываем значение гистерезиса для работы нагревателей (default: {Default_Value.DEF_TEMP_HYST})",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_INCHEAT_HYST,
            "value"     : Default_Value.DEF_TEMP_HYST
        }
    },

    "max_volt": {
        "type"          : TYPE.WRITE,
        "title"         : "[WRITED] Max Voltage (config)",
        "units"         : "mV",
        "description"   : f"Записываем значение максимального рабочего напряжения (default: {Default_Value.DEF_MAX_VOLT})",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_MAX_VOLT,
            "value"     : Default_Value.DEF_MAX_VOLT
        }
    },

    "min_volt": {
        "type"          : TYPE.WRITE,
        "title"         : "[WRITED] Min Voltage (config)",
        "units"         : "mV",
        "description"   : f"Записываем значение минимального рабочего напряжения (default: {Default_Value.DEF_MIN_VOLT})",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_MIN_VOLT,
            "value"     : Default_Value.DEF_MIN_VOLT
        }
    },

    "max_current": {
        "type"          : TYPE.WRITE,
        "title"         : "[WRITED] Max Current (config)",
        "units"         : "mA",
        "description"   : f"Записываем значение максимального рабочего тока (default: {Default_Value.DEF_MAX_CURRENT})",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_MAX_CURRENT,
            "value"     : Default_Value.DEF_MAX_CURRENT
        }
    },

    "min_current": {
        "type"          : TYPE.WRITE,
        "title"         : "[WRITED] Min Current (config)",
        "units"         : "mA",
        "description"   : f"Записываем значение минимального рабочего тока (default: {Default_Value.DEF_MIN_CURRENT})",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_MIN_CURRENT,
            "value"     : Default_Value.DEF_MIN_CURRENT
        }
    },

    "heater1_temp": {
        "type"          : TYPE.WRITE,
        "title"         : "[WRITED] Heater 1 temperature work limit (config)",
        "units"         : "॰С",
        "description"   : f"Записываем значение предела работы нагревателя 1 (default: {Default_Value.DEF_WORK_TEMP_HEAT1} [॰С])",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_INCHEAT_X1_TEMP,
            "value"     : Default_Value.DEF_WORK_TEMP_HEAT1
        }
    },

    "heater2_temp": {
        "type"          : TYPE.WRITE,
        "title"         : "[WRITED] Heater 2 temperature work limit (config)",
        "units"         : "॰С",
        "description"   : f"Записываем значение предела работы нагревателя 2 (default: {Default_Value.DEF_WORK_TEMP_HEAT2} [॰С])",
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_INCHEAT_X2_TEMP,
            "value"     : Default_Value.DEF_WORK_TEMP_HEAT2
        }
    },

    "rtc": {
        "type"          : TYPE.WRITE,
        "description"   : 'Записываем данные в RTC. (Формат для значения: "DD.MM.YY HH.MM.SS", без значения вводятся данные системы)',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_RTC_YEAR_MONTH,
            "value"     : 0x0000
        }
    },

    "frame_mult": {
        "type"          : TYPE.WRITE,
        "title"         : "[WRITED] Frame Multiply of teh Spotlight (config)",
        "units"         : "-",
        "description"   : 'Запись параметра умножения тактового сигнала для прожектора (и внутренний и внешний).',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_FRAME_DUR_MULT,
            "value"     : 0x0001
        }
    },

    "autoheat_mode": {
        "type"          : TYPE.WRITE,
        "title"         : "[WRITED] Auto Heat Mode (config)",
        "units"         : "-",
        "description"   : 'Установка режима автонагрева.',
        "modbus": {
            "address"   : DEVICE_ADDR,
            "function"  : FUNC.MB_FC6_WRITE_REGISTER,
            "register"  : REG.REG_AUTO_HEAT_MODE,
            "value"     : 0x0000
        }
    },
    #############
}

cmd_test_array = {
    #### TEST ####
    "leds": {
        "type"          : TYPE.TEST,
        "description"   : "Тесты индикации.",
    },

    "flash": {
        "type"          : TYPE.TEST,
        "description"   : "Тесты записи данных во Flash память.",
    },

    "pc_wdt": {
        "type"          : TYPE.TEST,
        "description"   : "Тесты работы Wathchdog таймера ПК.",
    },

    "sensors": {
        "type"          : TYPE.TEST,
        "description"   : "Тесты работы калориметров.",
    },

    "motors": {
        "type"          : TYPE.TEST,
        "description"   : "Тесты работы моторов.",
    },

    "motors_2": {
        "type"          : TYPE.TEST,
        "description"   : "Тесты работы моторов: 255 шагов, >, часто.",
    },

    "work": {
        "type"          : TYPE.TEST,
        "description"   : "Пробуем в долгую иммитацию работы.",
    },

    "imu_data_to_file": {
        "type"          : TYPE.TEST,
        "description"   : "Тестируем рабоу акселерометра, гироскопа (датчик ICM-20948), смотрим углы. Записываем данные в файл",
    },

    # "imu_10": {
    #     "type"          : TYPE.TEST,
    #     "description"   : "Тестируем рабоу акселерометра, гироскопа (датчик ICM-20948).",
    # },
    ##############
}

cmd_util_array = {
    #### UTILITY ####
    "CP2105_RST": {
        "type"          : TYPE.UTIL,
        "description"   : "Принудительный ресет CP2105 со стороны ПК. Кросплатформенный метод.",
    },
    "back": {
        "type"          : TYPE.UTIL,
        "description"   : "Откат прошивки к заводской.",
    },
    ##############
}