## Before running

Before running the API server there should be a `private/` folder inside `api/` containing these files:
* `private/cert.key` - GRID certificate key file
* `private/cert.pem` - GRID certificate file

### Instructions:

* Get GRID certificate: https://ca.cern.ch/ca/ You have to use your personal account. **Certificate has to be passwordless**.
* Instructions on how to get certificate and key files: https://twiki.cern.ch/twiki/bin/view/CMSPublic/WorkBookStartingGrid#ObtainingCert
* Copy paste-ble instructions:
```
# Leave Import Password blank
# PEM passphrase is required to be set
openssl pkcs12 -in myCertificate.p12 -clcerts -nokeys -out usercert.pem
openssl pkcs12 -in myCertificate.p12 -nocerts -out userkey.tmp.pem
openssl rsa -in userkey.tmp.pem -out userkey.pem
```
