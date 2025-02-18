
# Set up python libraries

cd /Users/simon/dev/tryout/hachack
pip install -r requirements.txt

## mutual TLS (mTLS) authentication

Set up using ./generate_certificates.zsh

## Launch

cd /Users/simon/dev/tryout/hachack
python hac_api.py --timeout 10