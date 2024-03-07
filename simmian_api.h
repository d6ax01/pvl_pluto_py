#pragma once

void Connect();
void Disconnect();
bool Play(wchar_t* selectedTitleName);
bool Stop(wchar_t* selectedTitleName);
void Reset(wchar_t* selectedTitleName);
int RegisterReadBySymbol(wchar_t* selectedTitleName, wchar_t* symbol, int length);
void RegisterRead(wchar_t* selectedTitleName, unsigned int page, unsigned int address, int length, wchar_t* buff);
bool RegisterWriteBySymbol(wchar_t* selectedTitleName, wchar_t* symbol, unsigned int value, int length, int byteLength);
bool RegisterWrite(wchar_t* selectedTitleName, unsigned int page, unsigned int address, unsigned int value, int length);
bool LoadRegisterMap(wchar_t* selectedTitleName, wchar_t* regpath);
bool SPIRead(wchar_t* selectedTitleName, unsigned char* pAddrValue, int addrLength, unsigned char* pDataValue, int dataLength);
bool SPIWrite(wchar_t* selectedTitleName, unsigned char* pAddrValue, int addrLength, unsigned char* pDataValue, int dataLength);
bool I2CRead(wchar_t* selectedTitleName, unsigned char id, unsigned char* pAddrValue, int addrLength, unsigned char* pDataValue, int dataLength);
bool I2CWrite(wchar_t* selectedTitleName, unsigned char id, unsigned char* pAddrValue, int addrLength, unsigned char* pDataValue, int dataLength);
bool Capture(wchar_t* selectedTitleName, wchar_t* savePath, int skipFrameCount, int captureCount, POINTER(int) roi);
void MultiCapture(wchar_t* selectedTitleName, wchar_t* savePath, int captureCount, int skipEachFrame, int sizeOfIndexField, int isCheckFinish);
int GridROIMultiCapture(wchar_t* selectedTitleName, wchar_t* savePath, wchar_t* rawType, int captureCnt, int gridM, int gridN, int centerW, int centerH, int isCheckFinish);
bool AverageCapture(wchar_t* selectedTitleName, wchar_t* savePath, int captureCount, wchar_t* outPath, bool removeTemporalFiles, int skipEachFrame, POINTER(int) roi);
bool SequentialCapture(wchar_t* selectedTitleName, wchar_t* filename, wchar_t* path, int cnt, wchar_t* ext, bool isCheckFinished);
bool LoadSetfile(wchar_t* selectedTitleName, wchar_t* path);
bool GetRenderFrameInfo(wchar_t* selectedTitleName, wchar_t* width, wchar_t* height, wchar_t* format);
double GetSensorFPS(wchar_t* selectedTitleName);
double GetBoardPLLClock(wchar_t* selectedTitleName);
bool GetSelectedDecoder(wchar_t* selectedTitleName, wchar_t* name);
bool SetDecoder(wchar_t* selectedTitleName, wchar_t* decoderName);
bool GetBayerOrder(wchar_t* selectedTitleName, wchar_t* decoderName, wchar_t* order);
bool SetBayerOrder(wchar_t* selectedTitleName, wchar_t* decoderName, wchar_t* bayer);
bool SetClipROI(wchar_t* selectedTitleName, POINTER(int) roi, bool isCenter);
int SetEITbyLSB(wchar_t* selectedTitleName, int targetLSB, wchar_t* targetBayer, bool isCenter, POINTER(int) roi, unsigned int page, unsigned int eitAddr, unsigned int minEIT, int maxTry, unsigned int eitAddrShort, wchar_t* selPD, int delayMSec);
void GetROIRect(wchar_t* selectedTitleName, POINTER(int) pRoi);
void SetROIRect(wchar_t* selectedTitleName, int left, int top, int right, int bottom);
bool SetRawBitDepth(wchar_t* selectedTitleName, int bits);
bool Set2PDMode(wchar_t* selectedTitleName, wchar_t* value, wchar_t* mode);
bool Set2PD(wchar_t* selectedTitleName, int isTrue, c_wchar pd);
void GetResultByTag(wchar_t* tagName, wchar_t* resultStr, unsigned int resultStrLength);
void GetResult(wchar_t* resultStr, unsigned int resultStrLength);
bool UserCommand(wchar_t* command);
bool Set2PDDecoderSubOption(wchar_t* selectedTitleName, wchar_t* subOption, wchar_t* isOn);
bool SetDecoderSubOption(wchar_t* selectedTitleName, wchar_t* decoderName, wchar_t* subOption, wchar_t* isOn);
bool SetRawDecoderFrameFrameDecompress(wchar_t* selectedTitleName, wchar_t* methodName, wchar_t* firstOption, wchar_t* firstOptionValue, wchar_t* secondOption, wchar_t* secondOptionValue);
int GetBoardCount();
bool GetTitleName(unsigned int idx, wchar_t* board_name, unsigned int board_name_len);
bool GetBoardFWVersion(wchar_t* selectedTitleName, wchar_t* fw_ver, unsigned int fw_ver_len);
bool GetNxSimmianSWVersion(wchar_t* selectedTitleName, wchar_t* sw_ver, unsigned int sw_ver_len);
bool GetSensorName(wchar_t* selectedTitleName, wchar_t* sensor_name, unsigned int sensor_name_len);
bool GetBoardName(wchar_t* selectedTitleName, wchar_t* board_name, unsigned int board_name_len);
bool Get2PDDecoderSubOption(wchar_t* selectedTitleName, wchar_t* subOption, wchar_t* decoder_sub_option, unsigned int decoder_sub_option_len);
bool GetDecoderSubOption(wchar_t* selectedTitleName, wchar_t* decoderName, wchar_t* subOption, wchar_t* decoder_sub_option, unsigned int decoder_sub_option_len);
bool GetFrameData(unsigned short* pFrame, int width, int height, wchar_t* selectedTitleName);
bool GetRenderFrameData(unsigned char* pRGBFrame, int width, int height, wchar_t* selectedTitleName);
bool GetInterleavedDataSizeArray(int array_vc_size, unsigned int checked_vc_idx, wchar_t* selectedTitleName);
bool GetFrameWithInterleavedData(frame_data* pMainFrame, int array_interleaved_data, unsigned int checked_vc_idx, wchar_t* selectedTitleName);
bool SetDeviceAddress(wchar_t* selectedTitleName, int address);