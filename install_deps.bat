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
pip install -r basereqs.txt
pip install -r requirements.txt --no-deps
@echo on