@echo off
echo Installing dependencies. Are you sure?
pause
cls
pip install --upgrade pip
cls
pip install --upgrade setuptools
cls
pip install --upgrade wheel
cls
pip cache remove numpy
pip install numpy
cls
pip install -r requirements.txt
pip install numpy>=1.24,<1.25 openvino-dev[onnx] --no-deps
@echo on