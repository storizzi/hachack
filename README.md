# Hac Hack - API for auto-running hybris hac operations

This is a python library for calling SAP Commerce / hybris hac tool automatically without having to use a browser session.

It has an accompanying API so that this can be called from other tools remotely. In order to use this, you'll need to set up mTLS authentication - a certificate generation script is included to make this a lot easier.

Samples of how to use th library and the API from a python program are included in the demos directory.

## Set up python libraries

```sh
cd /Users/simon/dev/tryout/hachack
pip install -r requirements.txt
```

## mutual TLS (mTLS) authentication

Get list of options for the generator using ```./generate_certificates.zsh``` without any parameters.

Set up using ```./generate_certificates.zsh --all```

You can generate a new client cert using ```--client``` parameter
You can generate a new server cert using ```--server``` parameter

Default parameters are as follows - override any of them - e.g.

```sh
./generate_certificates.zsh --all \
    --base-dir "certs" \
    --ca-dir "certs/ca" \
    --server-dir "certs/server" \
    --client-dir "certs/client" \
    --country "US" \
    --state "New York" \
    --city "Manhattan" \
    --org "Storizzi" \
    --ou "MyApp" \
    --email "simon@example.com"
```

Ideally you'd have a separate copy of this to keep the ca directory separate from the server and client for security reasons, and only generate certs from that copy.

## Launch

```sh
cd /Users/simon/dev/tryout/hachack
python hac_api.py --timeout 10
```
