sudo yum install python3.12 -y
echo "alias python3='python3.12'" >> ~/.bashrc
echo "alias pip3='python3.12 -m pip'" >> ~/.bashrc
source ~/.bashrc
python3.12 -m ensurepip --upgrade
python3.12 -m pip install boto3

mkdir python
pip3 install pandas -t python/
zip -r pandas.zip python/
aws s3 cp pandas.zip s3://YOUR-BUCKET-NAME/layers/pandas.zip
