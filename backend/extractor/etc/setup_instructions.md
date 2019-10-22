# Run these to setup HDQM backend in a new environment

```
sudo yum install python36
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
sudo python3 get-pip.py
pip install --user SQLAlchemy
pip install --user psycopg2-binary
python3 data_objects.py
```

