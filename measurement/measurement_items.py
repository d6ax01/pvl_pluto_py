import datetime
import pandas as pd
import os
import os.path


class MeasurementItems:
    def __init__(self,file_path):
        self.result_table=list()
        self.min_max_data=list()
        self.csv_path=file_path
        self.item_count=0
        self.total_value=[0,0,0,0]
        self.total_value_pow=[0,0,0,0] # note that (total val * total val / n )  - (mean * mean) =  std^2
        for i in range(4):
            self.result_table.append([0,0,0,0,0,0]) #avg, std, max val, max time, min val, min time

    def input_measurement_item(self,item):
        # write csv
        #add count
        self.item_count+=1
        #add total value
        for i in range(4):
            self.total_value[i]+=item[i]
            self.total_value_pow[i]+= item[i]**2
        #cal mean , std
        for i in range(4):
            self.result_table[i][0]=self.total_value[i]/self.item_count
            self.result_table[i][1]=self.total_value_pow[i]/self.item_count - self.result_table[i][0]**2
        # check min,max
        self.__check_min_max__(item)
        self.__wr_items__(item)
        self.__wr_result_table__(item)

    def __check_min_max__(self,item):
        for i in range(4):
            #check max
            if self.result_table[i][3] == 0:#init
                self.result_table[i][2] = item[i]
                self.result_table[i][3] = item[4]
            elif self.result_table[i][2] < item[i]:#check val
                self.result_table[i][2] = item[i]
                self.result_table[i][3] = item[4]
                # check min
            if self.result_table[i][5] == 0:#init
                self.result_table[i][4] = item[i]
                self.result_table[i][5] = item[4]
            elif self.result_table[i][4] > item[i]:#check val
                self.result_table[i][4] = item[i]
                self.result_table[i][5] = item[4]


    def __wr_result_table__(self,item):

        # report 엑셀 출력
        df1 = pd.DataFrame(
                    self.result_table,
                    columns=['Average value', 'std. dev.', 'max. value', 'max. time', 'min. value', 'min. time']
        )

        # file_path = r'{0}\{1}.csv'.format(Path, gSensor_id)  # file_path = r'{0}\{1}.csv'.format(Path, f'result')
        file_path = r'{0}\{1}.csv'.format(self.csv_path, "result_table")  # file_path = r'{0}\{1}.csv'.format(Path, f'result')
        # df1.to_csv(file_path, index=True, mode='w', header=True)
        # 하단코드는 처음이면 새로 생성 , 기존에 있으면 해당 파일에 누적해서 기록함
        df1.to_csv(file_path, index=True, mode='w', header=True)

    def __wr_items__(self,item):

        # report 엑셀 출력
        df1 = pd.DataFrame(
                    [item],
                    columns=['Depth', 'Intensity', 'Tx_temp', 'Rx_temp', 'time_stamp']
        )

        # file_path = r'{0}\{1}.csv'.format(Path, gSensor_id)  # file_path = r'{0}\{1}.csv'.format(Path, f'result')
        file_path = r'{0}\{1}.csv'.format(self.csv_path, "measurement_items")  # file_path = r'{0}\{1}.csv'.format(Path, f'result')
        # df1.to_csv(file_path, index=True, mode='w', header=True)
        # 하단코드는 처음이면 새로 생성 , 기존에 있으면 해당 파일에 누적해서 기록함
        if not os.path.exists(file_path):
            df1.to_csv(file_path, index=True, mode='w', header=True)
        else:
            df1.to_csv(file_path, index=True, mode='a', header=False)
