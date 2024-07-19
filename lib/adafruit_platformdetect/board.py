# SPDX-FileCopyrightText: 2021 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT


"""
`adafruit_platformdetect.board`
================================================================================

Detect boards

* Author(s): Melissa LeBlanc-Williams

Implementation Notes
--------------------

**Software and Dependencies:**

* Linux and Python 3.7 or Higher

"""

import os
import re

try:
    from typing import Optional
except ImportError:
    pass

from adafruit_platformdetect.constants import boards, chips

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PlatformDetect.git"


class Board:
    """Attempt to detect specific boards."""

    def __init__(self, detector) -> None:
        self.detector = detector
        self._board_id = None

    # pylint: disable=invalid-name, protected-access, too-many-return-statements, too-many-lines
    @property
    def id(self) -> Optional[str]:
        """Return a unique id for the detected board, if any."""
        # There are some times we want to trick the platform detection
        # say if a raspberry pi doesn't have the right ID, or for testing

        # Caching
        if self._board_id:
            return self._board_id

        try:
            return os.environ["BLINKA_FORCEBOARD"]
        except (AttributeError, KeyError):  # no forced board, continue with testing!
            pass

        chip_id = self.detector.chip.id
        board_id = None

        if chip_id == chips.H3:
            board_id = self._armbian_id() or self._allwinner_variants_id()
        elif chip_id == chips.RP2040:
            board_id = boards.RASPBERRY_PI_PICO
        elif chip_id == chips.RP2040_U2IF:
            board_id = self._rp2040_u2if_id()
        elif chip_id == chips.GENERIC_X86:
            board_id = boards.GENERIC_LINUX_PC
        self._board_id = board_id
        return board_id


    def _pi_id(self) -> Optional[str]:
        """Try to detect id of a Raspberry Pi."""
        # Check for Pi boards:
        pi_rev_code = self._pi_rev_code()
        if pi_rev_code:
            from adafruit_platformdetect.revcodes import PiDecoder

            try:
                decoder = PiDecoder(pi_rev_code)
                model = boards._PI_MODELS[decoder.type_raw]
                if isinstance(model, dict):
                    model = model[decoder.revision]
                return model
            except ValueError:
                pass
        # We may be on a non-Raspbian OS, so try to lazily determine
        # the version based on `get_device_model`
        else:
            pi_model = self.detector.get_device_model()
            if pi_model:
                pi_model = pi_model.upper().replace(" ", "_")
                if "PLUS" in pi_model:
                    re_model = re.search(r"(RASPBERRY_PI_\d).*([AB]_*)(PLUS)", pi_model)
                elif "CM" in pi_model:  # untested for Compute Module
                    re_model = re.search(r"(RASPBERRY_PI_CM)(\d)", pi_model)
                else:  # untested for non-plus models
                    re_model = re.search(r"(RASPBERRY_PI_\d).*([AB])", pi_model)

                if re_model:
                    pi_model = "".join(re_model.groups())
                    available_models = boards._PI_MODELS.values()
                    for model in available_models:
                        # Account for the PI_B_REV1/2 case
                        if isinstance(model, dict) and pi_model in model:
                            return model[pi_model]
                        if model == pi_model:
                            return model

        return None

    def _pi_rev_code(self) -> Optional[str]:
        """Attempt to find a Raspberry Pi revision code for this board."""
        # 2708 is Pi 1
        # 2709 is Pi 2
        # 2835 is Pi 3 (or greater) on 4.9.x kernel
        # Anything else is not a Pi.
        if self.detector.chip.id != chips.BCM2XXX:
            # Something else, not a Pi.
            return None
        rev = self.detector.get_cpuinfo_field("Revision")

        if rev is not None:
            return rev

        try:
            with open("/proc/device-tree/system/linux,revision", "rb") as revision:
                rev_bytes = revision.read()

                if rev_bytes[:1] == b"\x00":
                    rev_bytes = rev_bytes[1:]

                return rev_bytes.hex()
        except FileNotFoundError:
            return None

    # pylint: disable=too-many-return-statements

    def _rp2040_u2if_id(self) -> Optional[str]:
        import hid

        # look for it based on PID/VID
        for dev in hid.enumerate():
            # Raspberry Pi Pico
            vendor = dev["vendor_id"]
            product = dev["product_id"]
            if vendor == 0xCAFE and product == 0x4005:
                return boards.PICO_U2IF
            if vendor == 0x239A:
                # Feather RP2040
                if product == 0x00F1:
                    return boards.FEATHER_U2IF
        # Will only reach here if a device was added in chip.py but here.
        raise RuntimeError("RP2040_U2IF device was added to chip but not board.")

    # pylint: enable=too-many-return-statements

    @property
    def any_raspberry_pi(self) -> bool:
        """Check whether the current board is any Raspberry Pi."""
        return self._pi_rev_code() is not None

    @property
    def any_raspberry_pi_40_pin(self) -> bool:
        """Check whether the current board is any 40-pin Raspberry Pi."""
        return self.id in boards._RASPBERRY_PI_40_PIN_IDS

    @property
    def any_raspberry_pi_cm(self) -> bool:
        """Check whether the current board is any Compute Module Raspberry Pi."""
        return self.id in boards._RASPBERRY_PI_CM_IDS

    @property
    def os_environ_board(self) -> bool:
        """Check whether the current board is an OS environment variable special case."""

        def lazily_generate_conditions():
            yield self.board.FTDI_FT232H
            yield self.board.FTDI_FT2232H
            yield self.board.MICROCHIP_MCP2221
            yield self.board.BINHO_NOVA
            yield self.board.GREATFET_ONE
            yield self.board.PICO_U2IF
            yield self.board.FEATHER_U2IF
            yield self.board.FEATHER_CAN_U2IF
            yield self.board.FEATHER_EPD_U2IF
            yield self.board.FEATHER_RFM_U2IF
            yield self.board.ITSYBITY_U2IF
            yield self.board.MACROPAD_U2IF
            yield self.board.QTPY_U2IF
            yield self.board.QT2040_TRINKEY_U2IF
            yield self.board.KB2040_U2IF
            yield self.board.OS_AGNOSTIC_BOARD

        return any(condition for condition in lazily_generate_conditions())

    @property
    def any_embedded_linux(self) -> bool:
        """Check whether the current board is any embedded Linux device."""

        def lazily_generate_conditions():
            yield self.any_raspberry_pi_40_pin
            yield self.any_raspberry_pi
            yield self.any_beaglebone
            yield self.any_orange_pi
            yield self.any_nanopi
            yield self.any_giant_board
            yield self.any_jetson_board
            yield self.any_coral_board
            yield self.any_odroid_40_pin
            yield self.any_odroid_mini_pc
            yield self.khadas_vim3_40_pin
            yield self.any_96boards
            yield self.any_sifive_board
            yield self.any_onion_omega_board
            yield self.any_pine64_board
            yield self.any_pynq_board
            yield self.any_rock_pi_board
            yield self.any_clockwork_pi_board
            yield self.any_udoo_board
            yield self.any_seeed_board
            yield self.any_asus_tinker_board
            yield self.any_stm32mp1
            yield self.any_lubancat
            yield self.any_bananapi
            yield self.any_lemaker
            yield self.any_maaxboard
            yield self.any_tisk_board
            yield self.any_siemens_simatic_iot2000
            yield self.any_lichee_riscv_board
            yield self.any_pcduino_board
            yield self.any_libre_computer_board
            yield self.generic_linux
            yield self.any_nxp_navq_board
            yield self.any_walnutpi
            yield self.any_olimex_board
            yield self.any_repka_board
            yield self.any_milkv_board
            yield self.any_luckfox_pico_board
            yield self.any_vivid_unit

        return any(condition for condition in lazily_generate_conditions())

    @property
    def generic_linux(self) -> bool:
        """Check whether the current board is an Generic Linux System."""
        return self.id == boards.GENERIC_LINUX_PC

    @property
    def ftdi_ft232h(self) -> bool:
        """Check whether the current board is an FTDI FT232H."""
        return self.id == boards.FTDI_FT232H

    @property
    def ftdi_ft2232h(self) -> bool:
        """Check whether the current board is an FTDI FT2232H."""
        return self.id == boards.FTDI_FT2232H

    @property
    def microchip_mcp2221(self) -> bool:
        """Check whether the current board is a Microchip MCP2221."""
        return self.id == boards.MICROCHIP_MCP2221

    @property
    def os_agnostic_board(self) -> bool:
        """Check whether the current board is an OS agnostic special case."""
        return self.id == boards.OS_AGNOSTIC_BOARD

    @property
    def pico_u2if(self) -> bool:
        """Check whether the current board is a RPi Pico w/ u2if."""
        return self.id == boards.PICO_U2IF

    @property
    def feather_u2if(self) -> bool:
        """Check whether the current board is a Feather RP2040 w/ u2if."""
        return self.id == boards.FEATHER_U2IF

    @property
    def feather_can_u2if(self) -> bool:
        """Check whether the current board is a Feather CAN Bus RP2040 w/ u2if."""
        return self.id == boards.FEATHER_CAN_U2IF

    @property
    def feather_epd_u2if(self) -> bool:
        """Check whether the current board is a Feather ThinkInk RP2040 w/ u2if."""
        return self.id == boards.FEATHER_EPD_U2IF

    @property
    def feather_rfm_u2if(self) -> bool:
        """Check whether the current board is a Feather RFM RP2040 w/ u2if."""
        return self.id == boards.FEATHER_RFM_U2IF

    @property
    def itsybitsy_u2if(self) -> bool:
        """Check whether the current board is a Itsy Bitsy w/ u2if."""
        return self.id == boards.ITSYBITSY_U2IF

    @property
    def macropad_u2if(self) -> bool:
        """Check whether the current board is a MacroPad w/ u2if."""
        return self.id == boards.MACROPAD_U2IF

    @property
    def qtpy_u2if(self) -> bool:
        """Check whether the current board is a QT Py w/ u2if."""
        return self.id == boards.QTPY_U2IF

    @property
    def qt2040_trinkey_u2if(self) -> bool:
        """Check whether the current board is a QT Py w/ u2if."""
        return self.id == boards.QT2040_TRINKEY_U2IF

    @property
    def kb2040_u2if(self) -> bool:
        """Check whether the current board is a KB2040 w/ u2if."""
        return self.id == boards.KB2040_U2IF

    @property
    def binho_nova(self) -> bool:
        """Check whether the current board is an BINHO NOVA."""
        return self.id == boards.BINHO_NOVA

    @property
    def greatfet_one(self) -> bool:
        """Check whether the current board is a GreatFET One."""
        return self.id == boards.GREATFET_ONE

    def __getattr__(self, attr: str) -> bool:
        """
        Detect whether the given attribute is the currently-detected board.  See list
        of constants at the top of this module for available options.
        """
        if self.id == attr:
            return True
        return False
