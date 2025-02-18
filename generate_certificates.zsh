#!/bin/zsh

usage() {
    echo "Usage: $0 [<optional params>] [--ca | --server | --client | --all]"
    echo ""
    echo "Optional Params:"
    echo "  --base-dir <path>     Specify base directory for certificates (default: 'certs')"
    echo "  --ca-dir <path>       Specify CA directory (default: 'certs/ca')"
    echo "  --server-dir <path>   Specify server directory (default: 'certs/server')"
    echo "  --client-dir <path>   Specify client directory (default: 'certs/client')"
    echo "  --country <value>     Specify country for certificates (default: 'GB')"
    echo "  --state <value>       Specify state for certificates (default: 'England')"
    echo "  --city <value>        Specify city for certificates (default: 'London')"
    echo "  --org <value>         Specify organization for certificates (default: 'Storizzi')"
    echo "  --ou <value>          Specify organizational unit for certificates (default: 'ExampleApp')"
    echo "  --email <value>       Specify email for certificates (default: 'simon@example.com')"
    echo ""
    echo "Actions (at least one required):"
    echo "  --ca         Issue a new Certificate Authority (CA)"
    echo "  --server     Issue a new server key and certificate"
    echo "  --client     Issue a new client key and certificate"
    echo "  --all        Issue all of the above"
    exit 1
}

###################################################
# Default directories
###################################################
BASE_DIR="certs"
CA_DIR="$BASE_DIR/ca"
SERVER_DIR="$BASE_DIR/server"
CLIENT_DIR="$BASE_DIR/client"

###################################################
# Default certificate details
###################################################
COUNTRY="GB"
STATE="England"
CITY="London"
ORG="Example"
OU="ExampleApp"
EMAIL="simon@example.com"

###################################################
# Parse optional parameters and actions in one pass
###################################################
ACTIONS=()

# Single loop to parse all CLI args
while [[ $# -gt 0 ]]; do
    case $1 in
        # Optional Params
        --base-dir)
            BASE_DIR="$2"
            CA_DIR="$BASE_DIR/ca"
            SERVER_DIR="$BASE_DIR/server"
            CLIENT_DIR="$BASE_DIR/client"
            shift 2
            ;;
        --ca-dir)
            CA_DIR="$2"
            shift 2
            ;;
        --server-dir)
            SERVER_DIR="$2"
            shift 2
            ;;
        --client-dir)
            CLIENT_DIR="$2"
            shift 2
            ;;
        --country)
            COUNTRY="$2"
            shift 2
            ;;
        --state)
            STATE="$2"
            shift 2
            ;;
        --city)
            CITY="$2"
            shift 2
            ;;
        --org)
            ORG="$2"
            shift 2
            ;;
        --ou)
            OU="$2"
            shift 2
            ;;
        --email)
            EMAIL="$2"
            shift 2
            ;;

        # Actions
        --ca|--server|--client|--all)
            ACTIONS+=("$1")
            shift
            ;;

        # Unknown
        *)
            echo "Unrecognized option: $1"
            usage
            ;;
    esac
done

# If no actions were provided, show usage
if [[ ${#ACTIONS[@]} -eq 0 ]]; then
    usage
fi

###################################################
# Ensure directories exist
###################################################
mkdir -p "$CA_DIR" "$SERVER_DIR" "$CLIENT_DIR"

###################################################
# Define file paths
###################################################
CA_KEY="$CA_DIR/ca-key.pem"
CA_CERT="$CA_DIR/ca-cert.pem"
CA_SERIAL="$CA_DIR/ca-cert.srl"

SERVER_KEY="$SERVER_DIR/server-key.pem"
SERVER_CSR="$SERVER_DIR/server-req.csr"
SERVER_CERT="$SERVER_DIR/server-cert.pem"

CLIENT_KEY="$CLIENT_DIR/client-key.pem"
CLIENT_CSR="$CLIENT_DIR/client-req.csr"
CLIENT_CERT="$CLIENT_DIR/client-cert.pem"

###################################################
# Functions to generate certificates
###################################################
generate_ca() {
    echo "🔹 Generating Certificate Authority (CA)..."
    openssl genpkey -algorithm RSA -out "$CA_KEY"
    openssl req -x509 -new -key "$CA_KEY" -out "$CA_CERT" -days 365 \
        -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/OU=$OU/CN=Example-CA/emailAddress=$EMAIL"
}

generate_server_cert() {
    echo "🔹 Generating Server Key and Certificate..."
    openssl genpkey -algorithm RSA -out "$SERVER_KEY"
    openssl req -new -key "$SERVER_KEY" -out "$SERVER_CSR" \
        -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/OU=$OU/CN=localhost/emailAddress=$EMAIL"
    openssl x509 -req -in "$SERVER_CSR" -CA "$CA_CERT" -CAkey "$CA_KEY" -CAcreateserial -out "$SERVER_CERT" -days 365 -CAserial "$CA_SERIAL"
}

generate_client_cert() {
    echo "🔹 Generating Client Key and Certificate..."
    openssl genpkey -algorithm RSA -out "$CLIENT_KEY"
    openssl req -new -key "$CLIENT_KEY" -out "$CLIENT_CSR" \
        -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/OU=$OU/CN=Example-Client/emailAddress=$EMAIL"
    openssl x509 -req -in "$CLIENT_CSR" -CA "$CA_CERT" -CAkey "$CA_KEY" -CAcreateserial -out "$CLIENT_CERT" -days 365 -CAserial "$CA_SERIAL"
}

display_structure() {
    echo "✅ Operation completed successfully!"
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
}

###################################################
# Perform requested actions
###################################################
for action in "${ACTIONS[@]}"; do
    case $action in
        --ca)
            generate_ca
            ;;
        --server)
            generate_server_cert
            ;;
        --client)
            generate_client_cert
            ;;
        --all)
            generate_ca
            generate_server_cert
            generate_client_cert
            ;;
    esac
done

display_structure
