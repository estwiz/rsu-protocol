#!/bin/bash

# variable for current folder
DIR=$(pwd)/certs

openssl ecparam -genkey  -name prime256v1 -out "$DIR/quic_private_key.pem"

openssl req -new -x509 -key "$DIR/quic_private_key.pem" -out "$DIR/quic_certificate.pem" -days 365 \
    -subj "/CN=localhost" \
    -addext "subjectAltName = DNS:localhost, IP:127.0.0.1"

openssl req -new -config "$DIR/certificate.conf" -key "$DIR/quic_private_key.pem" -out "$DIR/quic_csr.pem"
