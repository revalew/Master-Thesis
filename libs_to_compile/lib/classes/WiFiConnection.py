# class to handle WiFi conenction
import utime  # type: ignore
import network  # type: ignore
from .NetworkCredentials import NetworkCredentials


class WiFiConnection:
    """
    Class to handle WiFi connection setup and management.

    WiFi Module Errors:
        [CYW43] core not in reset
        [CYW43] HT not ready
    """

    # class level vars
    status = network.STAT_IDLE
    ip = ""
    subnet_mask = ""
    gateway = ""
    dns_server = ""
    wlan = None
    fullConfig = None

    def __init__(self):
        pass

    @classmethod
    def start_ap_mode(cls, print_progress: bool = False) -> bool:
        utime.sleep(1)
        cls.wlan = network.WLAN(network.AP_IF)
        cls.wlan.config(
            essid=NetworkCredentials.ap_ssid, password=NetworkCredentials.ap_password
        )
        cls.wlan.active(True)  # Activate Access Point
        cls.wlan.config(pm=0xA11140)  # Disable power-save mode

        # print("Setting up the Access Point")
        while cls.wlan.active() == False:
            if print_progress:
                print("Setting up the Access Point - Please wait")
            # pass

        # setup successful
        config = cls.wlan.ifconfig()
        cls.ip = config[0]
        cls.subnet_mask = config[1]
        cls.gateway = config[2]
        cls.dns_server = config[3]

        cls.status = cls.wlan.status()

        cls.fullConfig = [
            f"status: {cls.status}",
            f"ssid: {cls.wlan.config("ssid")}",
            # f"key: {cls.wlan.config("key")}",
            f"txpower: {cls.wlan.config("txpower")}",
            f"pm: {cls.wlan.config("pm")}",
            f"mac: {cls.wlan.config("mac")}",
            f"ip: {cls.ip}",
            f"subnet_mask: {cls.subnet_mask}",
            f"gateway: {cls.gateway}",
            f"dns_server: {cls.dns_server}",
        ]

        if print_progress:
            print("Successfully started AP")
            print(config)

        utime.sleep(0.5)

        return True

    @classmethod
    def start_station_mode(cls, print_progress: bool = False) -> bool:
        # set WiFi to station interface
        cls.wlan = network.WLAN(network.STA_IF)
        # activate the network interface
        cls.wlan.active(True)
        cls.wlan.config(pm=0xA11140)
        # connect to wifi network
        cls.wlan.connect(NetworkCredentials.ssid, NetworkCredentials.password)
        cls.status = network.STAT_CONNECTING
        if print_progress:
            print("Connecting to Wi-Fi - please wait")
        max_wait = 20
        # wait for connection - poll every 0.5 secs
        while max_wait > 0:
            """
            0   STAT_IDLE -- no connection and no activity,
            1   STAT_CONNECTING -- connecting in progress,
            -3  STAT_WRONG_PASSWORD -- failed due to incorrect password,
            -2  STAT_NO_AP_FOUND -- failed because no access point replied,
            -1  STAT_CONNECT_FAIL -- failed due to other problems,
            3   STAT_GOT_IP -- connection successful.
            """
            if cls.wlan.status() < 0 or cls.wlan.status() >= 3:
                # connection attempt finished
                break
            max_wait -= 1
            utime.sleep(0.5)

        # check connection
        cls.status = cls.wlan.status()
        if cls.wlan.status() != 3:
            # No connection
            if print_progress:
                print("Connection Failed")
            return False
        else:
            # connection successful
            config = cls.wlan.ifconfig()
            cls.ip = config[0]
            cls.subnet_mask = config[1]
            cls.gateway = config[2]
            cls.dns_server = config[3]

            cls.fullConfig = [
                f"status: {cls.status}",
                f"ssid: {cls.wlan.config("ssid")}",
                # f"key: {cls.wlan.config("key")}",
                f"txpower: {cls.wlan.config("txpower")}",
                f"pm: {cls.wlan.config("pm")}",
                f"mac: {cls.wlan.config("mac")}",
                f"ip: {cls.ip}",
                f"subnet_mask: {cls.subnet_mask}",
                f"gateway: {cls.gateway}",
                f"dns_server: {cls.dns_server}",
            ]

            if print_progress:
                print("ip = " + str(cls.ip))
            return True
