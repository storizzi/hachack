#!/bin/zsh

# Define directories
BASE_DIR="certs"
CA_DIR="$BASE_DIR/ca"
SERVER_DIR="$BASE_DIR/server"
CLIENT_DIR="$BASE_DIR/client"

# Certificate details
COUNTRY="GB"
STATE="England"
CITY="London"
ORG="Storizzi"
OU="ExampleApp"
EMAIL="simon@example.com"

# Ensure directories exist
mkdir -p $CA_DIR $SERVER_DIR $CLIENT_DIR

# Define file paths
CA_KEY="$CA_DIR/ca-key.pem"
CA_CERT="$CA_DIR/ca-cert.pem"
CA_SERIAL="$CA_DIR/ca-cert.srl"

SERVER_KEY="$SERVER_DIR/server-key.pem"
SERVER_CSR="$SERVER_DIR/server-req.csr"
SERVER_CERT="$SERVER_DIR/server-cert.pem"

CLIENT_KEY="$CLIENT_DIR/client-key.pem"
CLIENT_CSR="$CLIENT_DIR/client-req.csr"
CLIENT_CERT="$CLIENT_DIR/client-cert.pem"

echo "🔹 Generating Certificate Authority (CA)..."
openssl genpkey -algorithm RSA -out $CA_KEY
openssl req -x509 -new -key $CA_KEY -out $CA_CERT -days 365 \
-subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/OU=$OU/CN=Example-CA/emailAddress=$EMAIL"

echo "🔹 Generating Server Certificate..."
openssl genpkey -algorithm RSA -out $SERVER_KEY
openssl req -new -key $SERVER_KEY -out $SERVER_CSR \
-subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/OU=$OU/CN=localhost/emailAddress=$EMAIL"
openssl x509 -req -in $SERVER_CSR -CA $CA_CERT -CAkey $CA_KEY -CAcreateserial -out $SERVER_CERT -days 365 -CAserial $CA_SERIAL

echo "🔹 Generating Client Certificate..."
openssl genpkey -algorithm RSA -out $CLIENT_KEY
openssl req -new -key $CLIENT_KEY -out $CLIENT_CSR \
-subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/OU=$OU/CN=Example-Client/emailAddress=$EMAIL"
openssl x509 -req -in $CLIENT_CSR -CA $CA_CERT -CAkey $CA_KEY -CAcreateserial -out $CLIENT_CERT -days 365 -CAserial $CA_SERIAL

echo "✅ All certificates generated successfully!"
echo "🔹 Certificate structure:"
echo "   📂 $BASE_DIR/"
echo "   ├── 📂 ca/       (CA certs)"
echo "   │   ├── $CA_CERT"
echo "   │   ├── $CA_KEY"
echo "   ├── 📂 server/   (Server certs)"
echo "   │   ├── $SERVER_CERT"
echo "   │   ├── $SERVER_KEY"
echo "   ├── 📂 client/   (Client certs)"
echo "       ├── $CLIENT_CERT"
echo "       ├── $CLIENT_KEY"
