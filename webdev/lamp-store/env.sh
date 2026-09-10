export PRODUCTS=http://localhost:8001
export ORDERS=http://localhost:8002
export ADMIN=http://localhost:8003
set -a; . ./.env; set +a
echo "endpoints ready: $PRODUCTS $ORDERS $ADMIN"