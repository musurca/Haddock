@echo off
echo.
echo Installing haddock...
pip --quiet install rich requests
echo.
set /P HADDOCKKEY=Paste your Sailaway API URL here, then press return:
(echo %HADDOCKKEY%) >> key.txt
echo.
echo Done! Run \"haddock\" to begin.
echo.