# Copyright (c) 2021 W-Mai
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

from PyInstaller.__main__ import run

lib_path = [r'D:\Prog\Python38-64\lib\site-packages\PyQt6\Qt\bin',
            r'D:\Prog\Python38-64\lib\site-packages\PyQt6\Qt\plugins\platforms;./platforms']

if __name__ == '__main__':
    opts = ['main.py', '-F',
            '-w',
            '--paths', lib_path[0],
            '--add-data', lib_path[1]]
    # opts = ['TargetOpinionMain.py', '-F', '-w']
    # opts = ['TargetOpinionMain.py', '-F', '-w', '--icon=TargetOpinionMain.ico','--upx-dir','upx391w']
    run(opts)
