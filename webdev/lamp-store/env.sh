export PRODUCTS=http://localhost:8001
export ORDERS=http://localhost:8002
export ADMIN=http://localhost:8003
export INTERNAL_API_KEY=k7Qx2mR9vT4wLp8NzB3sYd6HjF1aCgE51
set -a; . ./.env; set +a
echo "endpoints ready: $PRODUCTS $ORDERS $ADMIN"