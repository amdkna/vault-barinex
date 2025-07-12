@echo off
setlocal

echo 🔧 Creating virtual environment...
@REM py -3.11 -m venv env-barinex

echo 📦 Activating virtual environment...
call env-barinex\Scripts\activate.bat
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip

echo 📜 Installing requirements...
pip install -r requirements.txt

echo ✅ Setup complete.
echo To activate the virtual environment later, run:
echo     call env-barinex\Scripts\activate.bat

endlocal
pause