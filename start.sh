cd ~/
mkdir bot
cd bot
echo "Cloning main Repository"
git clone https://github.com/kalanakt/baesuzy.git
pip3 install -U -r requirements.txt
echo "Starting Bot...."
python3 bot.py
