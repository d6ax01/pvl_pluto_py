# -*- coding: utf-8 -*-

import numpy as np

def int_to_signed_short(value):
    return -(value & 0x8000) | (value & 0x7fff)

class EmbeddedDataParser:
    def __init__(self, chip_type: str = '63D', output_mode: str = 'unpacked_raw'):
        self.__output_mode = output_mode

        if chip_type == '33D':
            self.BYTE_INDEX_MODEL_ID = 6
            self.BYTE_INDEX_FRAME_COUNT = 16
            self.BYTE_INDEX_SENSOR_TEMP = 26
            self.BYTE_INDEX_DRIVER_TEMP = 188
            self.BYTE_INDEX_MODE = 180
            self.BYTE_INDEX_PHASE_MAP = 182
            self.BYTE_INDEX_MOD_FREQ = 184
            self.BYTE_INDEX_PROXIMITY = 186
            self.BYTE_INDEX_EIT = 220
            self.BYTE_INDEX_WIDTH = (256 + 128)
            self.BYTE_INDEX_HEIGHT = (256 + 132)
            self.BYTE_INDEX_BINNING_MODE = (256 + 168)
            self.BYTE_INDEX_BINNING_TYPE = (256 + 170)
            self.BYTE_INDEX_VT_D = (256 + 62)
            self.BYTE_INDEX_VT_P = (256 + 70)
            self.BYTE_INDEX_VT_M = (256 + 74)
            self.BYTE_INDEX_VT_S = (256 + 86)
            self.BYTE_INDEX_PCK = (256 + 108)
        if chip_type == 'RQ4':
            self.BYTE_INDEX_MODEL_ID = 6
            self.BYTE_INDEX_FRAME_COUNT = 16
            self.BYTE_INDEX_SENSOR_TEMP = 70
            self.BYTE_INDEX_DRIVER_TEMP = 194
            self.BYTE_INDEX_MODE = 202
            self.BYTE_INDEX_PHASE_MAP = 190
            self.BYTE_INDEX_MOD_FREQ = 192
            self.BYTE_INDEX_PROXIMITY = 0
            self.BYTE_INDEX_EIT = 236
            self.BYTE_INDEX_WIDTH = (256 + 148)
            self.BYTE_INDEX_HEIGHT = (256 + 152)
            self.BYTE_INDEX_BINNING_MODE = (256 + 194)
            self.BYTE_INDEX_BINNING_TYPE = (256 + 196)
            self.BYTE_INDEX_VT_D = (256 + 64)
            self.BYTE_INDEX_VT_P = (256 + 72)
            self.BYTE_INDEX_VT_M = (256 + 76)
            self.BYTE_INDEX_VT_S = (256 + 88)
            self.BYTE_INDEX_PCK = (256 + 128)
        elif chip_type == '63D':
            self.BYTE_INDEX_MODEL_ID = 6
            self.BYTE_INDEX_FRAME_COUNT = 16
            self.BYTE_INDEX_SENSOR_TEMP = 70
            self.BYTE_INDEX_DRIVER_TEMP = (512 + 26)
            self.BYTE_INDEX_MODE = (512 + 34)
            self.BYTE_INDEX_PHASE_MAP = (512 + 22)
            self.BYTE_INDEX_MOD_FREQ = (512 + 24)
            self.BYTE_INDEX_PROXIMITY = 0
            self.BYTE_INDEX_EIT = 204
            self.BYTE_INDEX_WIDTH = (256 + 124)
            self.BYTE_INDEX_HEIGHT = (256 + 128)
            self.BYTE_INDEX_BINNING_MODE = (512 + 6)
            self.BYTE_INDEX_BINNING_TYPE = (512 + 8)
            self.BYTE_INDEX_VT_D = (256 + 40)
            self.BYTE_INDEX_VT_P = (256 + 48)
            self.BYTE_INDEX_VT_M = (256 + 52)
            self.BYTE_INDEX_VT_S = (256 + 64)
            self.BYTE_INDEX_PCK = (256 + 104)
            self.BYTE_INDEX_MCLK = (768 + 6)
            self.BYTE_INDEX_PLL_MULTIPLIER1 = (768 + 16)
            self.BYTE_INDEX_PLL_POST_SCALER1 = (768 + 22)
            self.BYTE_INDEX_PIX_CLK_DIV1 = (768 + 26)
            self.BYTE_INDEX_PRE_PLL_CLK_DIV1 = (768 + 14)
            self.BYTE_INDEX_PLL_MULTIPLIER2 = (768 + 32)
            self.BYTE_INDEX_PLL_POST_SCALER2 = (768 + 38)
            self.BYTE_INDEX_PIX_CLK_DIV2 = (768 + 42)
            self.BYTE_INDEX_PRE_PLL_CLK_DIV2 = (768 + 30)
        else:
            print(f"Invalid chip ID({chip_type})")

    @staticmethod
    def __calculateEIT(eit, pck, vt_p, vt_s, vt_m, vt_d, mclk = 24.0):
        pll_sys = mclk * vt_m * 4 / ((2 ** vt_s) * vt_p * vt_d)
        return np.round(eit * pck * 1 / (pll_sys * 1000), 2)

    @staticmethod
    def __calculateSensorTemp(temp):
        if ((temp >> 15) & 1) == 1:
            ess = int_to_signed_short(int(temp))
            sensorTemp = ess / 256
        else:
            sensorTemp = temp / 256

        return np.round(sensorTemp, 3)

    @staticmethod
    def __calculateDriverTemp(temp):
        temp = temp & 1023
        driverTemp = (temp - 161) / 5.4

        return np.round(driverTemp, 3)

    def __parse_model_id(self, emb: np.ndarray, index_factor: int = 1):
        lsb_index = (self.BYTE_INDEX_MODEL_ID + 2) * index_factor
        msb_index = self.BYTE_INDEX_MODEL_ID * index_factor
        return hex(emb[lsb_index] + (emb[msb_index] << 8))

    def __parse_frame_count(self, emb: np.ndarray, index_factor: int = 1):
        index = self.BYTE_INDEX_FRAME_COUNT * index_factor
        return emb[index]

    def __parse_rx_temp(self, emb: np.ndarray, index_factor: int = 1):
        lsb_index = (self.BYTE_INDEX_SENSOR_TEMP + 2) * index_factor
        msb_index = self.BYTE_INDEX_SENSOR_TEMP * index_factor
        return self.__calculateSensorTemp(emb[lsb_index] + (emb[msb_index] << 8))

    def __parse_tx_temp(self, emb: np.ndarray, index_factor: int = 1):
        lsb_index = (self.BYTE_INDEX_DRIVER_TEMP + 2) * index_factor
        msb_index = self.BYTE_INDEX_DRIVER_TEMP * index_factor
        return self.__calculateDriverTemp(emb[lsb_index] + (emb[msb_index] << 8))

    def __parse_shuffle_index(self, emb: np.ndarray, index_factor: int = 1):
        return emb[self.BYTE_INDEX_PHASE_MAP * index_factor]

    def __parse_frequency_index(self, emb: np.ndarray, index_factor: int = 1):
        return emb[self.BYTE_INDEX_MOD_FREQ * index_factor]

    def __parse_mclk(self, emb: np.ndarray, index_factor: int = 1):
        lsb_index = (self.BYTE_INDEX_MCLK + 2) * index_factor
        msb_index = self.BYTE_INDEX_MCLK * index_factor
        return np.round((emb[lsb_index] + (emb[msb_index] << 8)) / 256, 1)

    def __parse_eit(self, emb: np.ndarray, index_factor: int = 1, mclk: float = 24.0):
        lsb_index = (self.BYTE_INDEX_EIT + 2) * index_factor
        msb_index = self.BYTE_INDEX_EIT * index_factor
        eit = emb[lsb_index] + (emb[msb_index] << 8)

        lsb_index = (self.BYTE_INDEX_PCK + 2) * index_factor
        msb_index = self.BYTE_INDEX_PCK * index_factor
        pck = emb[lsb_index] + (emb[msb_index] << 8)

        lsb_index = (self.BYTE_INDEX_VT_P + 2) * index_factor
        msb_index = self.BYTE_INDEX_VT_P * index_factor
        vt_p = emb[lsb_index] + (emb[msb_index] << 8)

        lsb_index = (self.BYTE_INDEX_VT_S + 2) * index_factor
        msb_index = self.BYTE_INDEX_VT_S * index_factor
        vt_s = emb[lsb_index] + (emb[msb_index] << 8)

        lsb_index = (self.BYTE_INDEX_VT_M + 2) * index_factor
        msb_index = self.BYTE_INDEX_VT_M * index_factor
        vt_m = emb[lsb_index] + (emb[msb_index] << 8)

        lsb_index = (self.BYTE_INDEX_VT_D + 2) * index_factor
        msb_index = self.BYTE_INDEX_VT_D * index_factor
        vt_d = emb[lsb_index] + (emb[msb_index] << 8)

        return self.__calculateEIT(eit, pck, vt_p, vt_s, vt_m, vt_d, mclk)

    def __parse_freq1(self, emb: np.ndarray, index_factor: int = 1, mclk: float = 24.0):
        lsb_index = (self.BYTE_INDEX_PLL_MULTIPLIER1 + 2) * index_factor
        msb_index = self.BYTE_INDEX_PLL_MULTIPLIER1 * index_factor
        pll_multiplier = emb[lsb_index] + (emb[msb_index] << 8)
        pll_post_scaler = emb[self.BYTE_INDEX_PLL_POST_SCALER1 * index_factor]
        pix_clk_div = emb[self.BYTE_INDEX_PIX_CLK_DIV1 * index_factor]
        pre_pll_clk_div = emb[self.BYTE_INDEX_PRE_PLL_CLK_DIV1 * index_factor]
        return mclk / 4 * pll_multiplier / (2 ** pll_post_scaler) / pix_clk_div / pre_pll_clk_div

    def __parse_freq2(self, emb: np.ndarray, index_factor: int = 1, mclk: float = 24.0):
        lsb_index = (self.BYTE_INDEX_PLL_MULTIPLIER2 + 2) * index_factor
        msb_index = self.BYTE_INDEX_PLL_MULTIPLIER2 * index_factor
        pll_multiplier = emb[lsb_index] + (emb[msb_index] << 8)
        pll_post_scaler = emb[self.BYTE_INDEX_PLL_POST_SCALER2 * index_factor]
        pix_clk_div = emb[self.BYTE_INDEX_PIX_CLK_DIV2 * index_factor]
        pre_pll_clk_div = emb[self.BYTE_INDEX_PRE_PLL_CLK_DIV2 * index_factor]
        return mclk / 4 * pll_multiplier / (2 ** pll_post_scaler) / pix_clk_div / pre_pll_clk_div

    def __parse_emb(self, emb, index_factor):
        mclk = self.__parse_mclk(emb, index_factor)

        embedded_data = {'Model ID': self.__parse_model_id(emb, index_factor),
                    'Frame count': self.__parse_frame_count(emb, index_factor),
                    'Rx temperature': self.__parse_rx_temp(emb, index_factor),
                    'Tx temperature': self.__parse_tx_temp(emb, index_factor),
                    'Shuffle index': self.__parse_shuffle_index(emb, index_factor),
                    'Frequency index': self.__parse_frequency_index(emb, index_factor),
                    'MCLK_MHz': self.__parse_mclk(emb, index_factor),
                    'EIT': self.__parse_eit(emb, index_factor, mclk),
                   # 'freq1_MHz': self.__parse_freq1(emb, index_factor, mclk),
                   # 'freq2_MHz': self.__parse_freq2(emb, index_factor, mclk)
                    'freq1_MHz': 0,
                    'freq2_MHz': 0}

        return embedded_data

    def parse_embedded_data(self, emb):
        if 'unpacked_raw' in self.__output_mode:
            return self.__parse_emb(emb, index_factor=1)

        if 'packed_raw' in self.__output_mode:
            return self.__parse_emb(emb, index_factor=1)

        if 'depth' in self.__output_mode:
            return self.__parse_emb(emb, index_factor=2)

        print(f'Cannot parse embedded data due to invalid output mode({self.__output_mode})')
        return None