# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.patches as patches


def outputmode1(path, vc_0, max_depth_range, vc_2):
    # mode1 변환 코드 : depth image *************************************************************************************
    fullpath = os.path.join(path, vc_0)
    dump = np.fromfile(fullpath, dtype='>B').reshape(height + 4, width * 2)  # '>' big endian, 'B' unsigned byte
    dump = dump[4:, :]  # remove embedded lines
    z = np.zeros((height, width), dtype=np.ushort)
    for h in range(0, height):
        for w in range(0, width):
            z[h, w] = (dump[h, w * 2] << 8) + dump[h, w * 2 + 1]

    depth = np.bitwise_and(z, 0x1FFF).astype(np.float32) / 2 ** 13 * max_depth_range

    # intensity image
    fullpath = os.path.join(path, vc_2)
    dump = np.fromfile(fullpath, dtype='B').reshape(height + 0, width * 2)  # '>' big endian, 'H' unsigned short
    image = np.zeros((height, width), dtype=np.ushort)
    for h in range(0, height):
        for w in range(0, width):
            image[h, w] = (dump[h, w * 2] << 8) + dump[h, w * 2 + 1]
    intensity = image / 2 ** 4  # DEPS tool 설정과 동일하게 맞추기 위해 2**4를 함

    figure_2d(depth, 'Depth', z_start=450, z_end=550)
    figure_2d(intensity, 'Intensity', z_start=0, z_end=500)

    # save csv file
    np.savetxt(os.path.join(path, '0001_depthImg.csv'), depth, delimiter=',')
    np.savetxt(os.path.join(path, '0001_IntensityImg.csv'), intensity, delimiter=',')


def outputmode3(path, vc_0, max_depth_range, vc_1, vc_2, vc_3 ):
    # mode3 변환 코드 : depth image *************************************************************************************
    fullpath = os.path.join(path, vc_0)
    dump = np.fromfile(fullpath, dtype='>H').reshape(height + 4, width * 3)  # '>' big endian, 'H' unsigned short
    dump = dump[4:, :]  # remove embedded lines
    z = np.zeros((height, width), dtype=np.ushort)
    for h in range(0, height):
        for w in range(0, width):
            z[h, w] = dump[h, w * 3 + 2]

    depth = z / 2 ** 16 * max_depth_range

    # Amplitude image
    fullpath = os.path.join(path, vc_1)
    dump = np.fromfile(fullpath, dtype='B').reshape(height + 0, width * 2)  # '>' big endian, 'H' unsigned short
    image = np.zeros((height, width), dtype=np.ushort)
    for h in range(0, height):
        for w in range(0, width):
            image[h, w] = (dump[h, w * 2] << 8) + dump[h, w * 2 + 1]
    amplitude = image / 2 ** 4  # DEPS tool 설정과 동일하게 맞추기 위해 2**4를 함

    # Intensity image
    fullpath = os.path.join(path, vc_2)
    dump = np.fromfile(fullpath, dtype='B').reshape(height + 0, width * 2)  # '>' big endian, 'H' unsigned short
    image = np.zeros((height, width), dtype=np.ushort)
    for h in range(0, height):
        for w in range(0, width):
            image[h, w] = (dump[h, w * 2] << 8) + dump[h, w * 2 + 1]
    intensity = image / 2 ** 4  # DEPS tool 설정과 동일하게 맞추기 위해 2**4를 함

    # Confidence image
    fullpath = os.path.join(path, vc_3)
    dump = np.fromfile(fullpath, dtype='B').reshape(height + 0, width * 2)  # '>' big endian, 'H' unsigned short
    image = np.zeros((height, width), dtype=np.ushort)
    for h in range(0, height):
        for w in range(0, width):
            image[h, w] = (dump[h, w * 2] << 8) + dump[h, w * 2 + 1]
    confidence = image *0.002857 / 2 ** 4  # DEPS tool 설정과 동일하게 맞추기 위해 2**4를 함


    figure_2d(depth,        'Depth',        z_start=450,    z_end=550)
    figure_2d(amplitude,    'Amplitude',    z_start=0,      z_end=500)
    figure_2d(intensity,    'Intensity',    z_start=0,      z_end=500)
    figure_2d(confidence,   'Confidence',   z_start=0,      z_end=5)


    # save csv file
    np.savetxt(os.path.join(path, '0001_depthImg.csv'),         depth,      delimiter=',')
    np.savetxt(os.path.join(path, '0001_amplitudeImg.csv'),     amplitude,  delimiter=',')
    np.savetxt(os.path.join(path, '0001_intensityImg.csv'),     intensity,  delimiter=',')
    np.savetxt(os.path.join(path, '0001_confidenceImg.csv'),    confidence, delimiter=',')


def figure_2d(image, title, x=0, y=0, len_x=0, len_y=0, z_start=0, z_end=10000):
    fig = plt.figure()
    ax1 = fig.add_subplot(1, 1, 1)
    ax1.set(title=title, xlabel='Column Index', ylabel='Row Index')
    ax1.grid(True)
    rect = patches.Rectangle((x, y),
                             len_x,
                             len_y,
                             linewidth=2,
                             edgecolor='cyan',
                             fill=False)
    ax1.add_patch(rect)

    if title == 'Depth':
        cmap = cm.get_cmap('jet').copy()
    else:
        cmap = cm.get_cmap('gray').copy()

    cmap.set_under(color='black')
    plt.imshow(image, cmap=cmap, vmin=z_start, vmax=z_end)
    plt.colorbar()
    plt.show()



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    path = r'C:\LSI_VST63D\save\robot사업부evt0p0_셋파일\LUTI-QW-10020_120D017_FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF\20M_50cm'
    main_vc_0 = r'image20mhz_0_ALL0_f1_nshfl'+'.raw'
    main_vc_1 = r'image20mhz_0_ALL0_f1_nshfl_VC(1)_DT(Raw8)'+'.raw'
    main_vc_2 = r'image20mhz_0_ALL0_f1_nshfl_VC(2)_DT(Raw8)'+'.raw'
    main_vc_3 = r'image20mhz_0_ALL0_f1_nshfl_VC(3)_DT(Raw8)'+'.raw'
    width = 320
    height = 240
    max_depth_range = 7500  # single 100MHz = 1500(mm), 20MHz = 7500(mm), 50MHz = 3000(mm), 100+30MHz = 15000(mm)


    output_mode = 1

    if output_mode == 1:
        outputmode1(path, main_vc_0, max_depth_range, main_vc_2)
    elif output_mode == 3:
        outputmode3(path, main_vc_0, max_depth_range, main_vc_1, main_vc_2, main_vc_3)
    else:
        pass












